import io
import zipfile
import requests

import joblib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import skew, kurtosis
from sklearn.metrics import confusion_matrix, f1_score

# Page config
st.set_page_config(
    page_title="DualSleep - Sleep/Wake Classifier",
    layout="wide",
)

# DualSleep constants + feature helpers
dualsleep_labels = {
    81: "wake",
    82: "non-rem1",
    83: "non-rem2",
    84: "non-rem3",
    85: "rem",
    86: "movement",
}

# Columns we expect from raw high-frequency CSV
RAW_REQUIRED_COLS = [
    "timestamp",
    "back_x", "back_y", "back_z",
    "thigh_x", "thigh_y", "thigh_z",
    "back_temp", "thigh_temp",
    "label",  # DualSleep label
]

cols_acc = ["back_x", "back_y", "back_z", "thigh_x", "thigh_y", "thigh_z"]
cols_temp = ["back_temp", "thigh_temp"]


def _skew_safe(x: np.ndarray) -> float:
    """Skewness that returns 0 if values are nearly identical or too short."""
    x = np.asarray(x)
    if x.size < 4 or np.allclose(x, x[0]):
        return 0.0
    return float(skew(x, bias=False))


def _kurt_safe(x: np.ndarray) -> float:
    """Kurtosis that returns 0 if values are nearly identical or too short."""
    x = np.asarray(x)
    if x.size < 4 or np.allclose(x, x[0]):
        return 0.0
    return float(kurtosis(x, fisher=True, bias=False))


def _corr_or_zero(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation that returns 0 if not enough points."""
    a = np.asarray(a)
    b = np.asarray(b)
    if a.size > 3 and b.size > 3:
        return float(np.corrcoef(a, b)[0, 1])
    return 0.0


def to_windows_60s_uploaded(df_raw: pd.DataFrame, subject_id: str = "uploaded") -> pd.DataFrame:
    """
    Take raw DualSleep-style sensor data and:
    - parse per-minute windows
    - compute same stats as in the training notebook
    - build y (sleep vs wake) from label
    - add circadian feature sleep_prob_clock (using this file's y)
    """
    # basic checks
    missing = [c for c in RAW_REQUIRED_COLS if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Raw file is missing required columns: {missing}")

    # Timestamp to pandas datetime
    if not np.issubdtype(df_raw["timestamp"].dtype, np.datetime64):
        df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"], errors="coerce")
    df_raw = df_raw.dropna(subset=["timestamp"]).copy()

    # Build activity + y (sleep vs wake) from label
    df_raw["activity"] = df_raw["label"].map(dualsleep_labels).astype("category")
    df_raw["y"] = df_raw["activity"].isin(
        ["non-rem1", "non-rem2", "non-rem3", "rem"]
    ).astype("int8")

    # Assign subject_id (if not present)
    if "subject_id" not in df_raw.columns:
        df_raw["subject_id"] = subject_id

    # Minute-level grouping
    df_raw["minute"] = df_raw["timestamp"].dt.floor("60s")
    g = df_raw.groupby("minute", sort=True)

    out = pd.DataFrame(index=g.size().index)
    out["subject_id"] = df_raw["subject_id"].iloc[0]

    # Majority vote for y in each minute
    out["y"] = g["y"].mean().round().astype("int8")

    # per-sensor stats
    for c in cols_acc + cols_temp:
        s = g[c]
        out[f"{c}_mean"] = s.mean()
        out[f"{c}_std"] = s.std(ddof=0)
        out[f"{c}_min"] = s.min()
        out[f"{c}_max"] = s.max()
        out[f"{c}_p25"] = s.quantile(0.25)
        out[f"{c}_p75"] = s.quantile(0.75)
        out[f"{c}_skew"] = s.apply(_skew_safe)
        out[f"{c}_kurt"] = s.apply(_kurt_safe)
        out[f"{c}_energy"] = s.apply(lambda x: float(np.square(x).sum()))

    # magnitudes
    df_raw["back_mag"] = np.sqrt(
        df_raw["back_x"] ** 2 + df_raw["back_y"] ** 2 + df_raw["back_z"] ** 2
    )
    df_raw["thigh_mag"] = np.sqrt(
        df_raw["thigh_x"] ** 2 + df_raw["thigh_y"] ** 2 + df_raw["thigh_z"] ** 2
    )

    out["back_mag_mean"] = g["back_mag"].mean()
    out["thigh_mag_mean"] = g["thigh_mag"].mean()

    # correlations between back & thigh
    out["back_thigh_corr_mag"] = g.apply(
        lambda x: _corr_or_zero(x["back_mag"], x["thigh_mag"]), include_groups=False
    )
    for axis in ["x", "y", "z"]:
        out[f"corr_back_{axis}_thigh_{axis}"] = g.apply(
            lambda x, ax=axis: _corr_or_zero(x[f"back_{ax}"], x[f"thigh_{ax}"]),
            include_groups=False,
        )

    # cyclic time features
    t = out.index.to_series()
    hour = t.dt.hour + t.dt.minute / 60.0
    day = t.dt.dayofweek + hour / 24.0
    monthp = t.dt.month - 1 + (t.dt.day - 1) / 30.0

    out["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    out["dow_sin"] = np.sin(2 * np.pi * day / 7)
    out["dow_cos"] = np.cos(2 * np.pi * day / 7)
    out["mon_sin"] = np.sin(2 * np.pi * monthp / 12)
    out["mon_cos"] = np.cos(2 * np.pi * monthp / 12)

    # circadian sleep probability (per clock minute)
    clock_min = (t.dt.hour * 60 + t.dt.minute).astype("int16")
    out["clock_minute"] = clock_min.values

    sleep_prob_clock = (
        out.groupby("clock_minute")["y"].mean().astype("float32")
    )
    out["sleep_prob_clock"] = out["clock_minute"].map(sleep_prob_clock).astype(
        "float32"
    )

    # Final shape: put minute as timestamp column
    out = out.reset_index().rename(columns={"minute": "timestamp"})
    return out


# Helpers for different upload modes

def _concat_csv_files(files) -> pd.DataFrame:
    dfs = []
    for f in files:
        dfs.append(pd.read_csv(f))
    return pd.concat(dfs, ignore_index=True)


def load_from_zip(uploaded_zip) -> pd.DataFrame:
    """Read one or more CSVs inside a ZIP and concatenate them."""
    z = zipfile.ZipFile(uploaded_zip)
    csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise ValueError("No .csv files found inside the ZIP archive.")
    dfs = []
    for name in sorted(csv_names):
        with z.open(name) as f:
            dfs.append(pd.read_csv(f))
    return pd.concat(dfs, ignore_index=True)


def load_from_url(url: str) -> pd.DataFrame:
    """Download CSV/ZIP from a URL and return concatenated DataFrame."""
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    content = io.BytesIO(resp.content)

    lower = url.lower()
    if lower.endswith(".zip"):
        return load_from_zip(content)
    # try to detect zip by content-type, just in case
    ctype = resp.headers.get("Content-Type", "").lower()
    if "zip" in ctype:
        return load_from_zip(content)

    # assume CSV
    return pd.read_csv(content)


# Load model + data (cached)

@st.cache_resource
def load_model():
    """Load the saved SVM pipeline and metadata."""
    bundle = joblib.load("dualsleep_svm.joblib")
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    svm_params = bundle["svm_params"]
    return model, feature_cols, svm_params


@st.cache_data
def load_preds():
    """
    Load final minute-level predictions and per-subject metrics.
    - preds_final.csv: timestamp, subject_id, y, y_pred
    - per_subject_final.csv: sensitivity, specificity, f1_macro per subject
    """
    preds = pd.read_csv("preds_final.csv", parse_dates=["timestamp"])
    per_subj = pd.read_csv("per_subject_final.csv", index_col=0)
    return preds, per_subj


model, feature_cols, svm_params = load_model()
preds_final, per_subj_final = load_preds()

# Sidebar controls
st.sidebar.title("DualSleep controls")

subject_ids = sorted(preds_final["subject_id"].unique().tolist())
default_idx = subject_ids.index("PSG_14") if "PSG_14" in subject_ids else 0

sid = st.sidebar.selectbox("Select subject", subject_ids, index=default_idx)
hrs = st.sidebar.slider("Show first N hours", min_value=4, max_value=24, value=12)

st.sidebar.markdown("**Model hyperparameters**")
st.sidebar.json(svm_params)

# Main title + description
st.title("DualSleep – Sleep/Wake Prediction Viewer")

st.markdown(
    """
This app lets you explore the performance of our **RBF-kernel SVM** sleep/wake classifier  
trained on 60-second windows of accelerometer and temperature from the **DualSleep** dataset.

- **Labels:** `sleep = 1`, `wake = 0`  
- **Training scheme:** Leave-One-Subject-Out (LOSO) cross-validation  
- The SVM’s decision threshold is tuned to balance **sensitivity** (detecting sleep)
  and **specificity** (detecting wake).
"""
)

st.divider()

# Tabs
tab_overview, tab_subject, tab_upload, tab_info = st.tabs(
    ["Overview", "Per-subject view", "Upload your data", "How the model works"]
)

# TAB 1: Overview (all subjects)
with tab_overview:
    st.subheader("Overall post-threshold performance (across all subjects)")

    overall_cols = ["sensitivity", "specificity", "f1_macro"]
    overall_mean = per_subj_final[overall_cols].mean()

    # KPI-style summary cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean sensitivity", f"{overall_mean['sensitivity']:.3f}")
    c2.metric("Mean specificity", f"{overall_mean['specificity']:.3f}")
    c3.metric("Mean F1 (macro)", f"{overall_mean['f1_macro']:.3f}")

    # Dataset-wide bar plots
    st.subheader("Performance by subject (all participants)")

    # F1 (macro) by subject
    fig_f1, ax_f1 = plt.subplots(figsize=(10, 3))
    (
        per_subj_final["f1_macro"]
        .sort_index()
        .plot(kind="bar", ax=ax_f1, alpha=0.9)
    )
    ax_f1.set_ylabel("F1 (macro)")
    ax_f1.set_title("F1 (macro) by subject")
    ax_f1.tick_params(axis="x", labelrotation=60)
    plt.tight_layout()
    st.pyplot(fig_f1)

    # Sensitivity vs specificity by subject
    fig_ss, ax_ss = plt.subplots(figsize=(10, 3))
    (
        per_subj_final[["sensitivity", "specificity"]]
        .sort_index()
        .plot(kind="bar", ax=ax_ss)
    )
    ax_ss.set_ylabel("score")
    ax_ss.set_title("Sensitivity vs Specificity by subject")
    ax_ss.tick_params(axis="x", labelrotation=60)
    plt.tight_layout()
    st.pyplot(fig_ss)

    # Quick summary
    st.subheader("Quick summary")

    sens_mean = float(overall_mean["sensitivity"])
    spec_mean = float(overall_mean["specificity"])
    f1_mean = float(overall_mean["f1_macro"])

    top_k = 3
    best_f1 = per_subj_final.sort_values("f1_macro", ascending=False).head(top_k)
    worst_f1 = per_subj_final.sort_values("f1_macro", ascending=True).head(top_k)

    st.markdown(
        f"""
**Overall performance (after final threshold):**

- Average sensitivity (sleep detection): **{sens_mean:.3f}**
- Average specificity (wake detection): **{spec_mean:.3f}**
- Average F1 (macro): **{f1_mean:.3f}**

The model is slightly better at detecting **sleep** than wake,  
but both sensitivity and specificity are in the mid 0.7s range.
"""
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Easiest subjects (highest F1):**")
        for sid_row, row in best_f1.iterrows():
            st.markdown(
                f"- `{sid_row}` – F1 **{row['f1_macro']:.3f}** "
                f"(sens={row['sensitivity']:.3f}, spec={row['specificity']:.3f})"
            )

    with col2:
        st.markdown("**Hardest subjects (lowest F1):**")
        for sid_row, row in worst_f1.iterrows():
            st.markdown(
                f"- `{sid_row}` – F1 **{row['f1_macro']:.3f}** "
                f"(sens={row['sensitivity']:.3f}, spec={row['specificity']:.3f})"
            )

# TAB 2: Per-subject view
with tab_subject:
    st.subheader(f"Per-subject metrics – {sid}")

    if sid in per_subj_final.index:
        row = per_subj_final.loc[sid]

        c1, c2, c3 = st.columns(3)
        c1.metric("Sensitivity", f"{row['sensitivity']:.3f}")
        c2.metric("Specificity", f"{row['specificity']:.3f}")
        c3.metric("F1 (macro)", f"{row['f1_macro']:.3f}")
    else:
        st.warning("Selected subject not found in per_subject_final.csv")

    st.subheader(f"{sid} – first {hrs} hours (true vs predicted)")

    # Filter to chosen subject and first N hours
    d = preds_final[preds_final["subject_id"] == sid].copy()
    d = d.sort_values("timestamp")

    if not d.empty:
        end_time = d["timestamp"].min() + pd.Timedelta(hours=hrs)
        d = d[d["timestamp"] <= end_time].copy()

        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(
            d["timestamp"],
            d["y"],
            drawstyle="steps-post",
            label="true",
            alpha=0.9,
        )
        ax.plot(
            d["timestamp"],
            d["y_pred"],
            drawstyle="steps-post",
            label="pred",
            alpha=0.9,
        )

        ax.set_yticks([0, 1])
        ax.set_yticklabels(["wake", "sleep"])
        ax.set_xlabel("time")
        ax.set_title(f"{sid} – sleep vs wake (true vs pred)")
        ax.legend()
        fig.autofmt_xdate()

        st.pyplot(fig)
    else:
        st.info("No prediction rows found for this subject.")

    with st.expander("Sanity check: model bundle status"):
        st.write("Model bundle loaded successfully.")
        st.write("Number of features used by the SVM:", len(feature_cols))
        st.write("Example feature names:", feature_cols[:10])

# TAB 3: Upload your data
with tab_upload:
    st.header("Try the model on raw DualSleep-style sensor data")

    st.markdown(
        """
Upload a **raw high-frequency DualSleep dataset** with columns:

- `timestamp`
- `back_x`, `back_y`, `back_z`
- `thigh_x`, `thigh_y`, `thigh_z`
- `back_temp`, `thigh_temp`
- `label` (81–86, DualSleep codes)

**Streamlit Cloud limit:** 200MB per uploaded file.  
To handle larger nights you can:
- Upload a **compressed ZIP** containing one or more CSVs  
- Upload **multiple CSV chunks** of the same night  
- Provide a **URL** to a CSV/ZIP file hosted elsewhere (Drive/Dropbox/S3, etc.)
"""
    )

    mode = st.radio(
        "Choose how to provide your data:",
        [
            "Single CSV file (≤200MB)",
            "ZIP file with one or more CSVs",
            "Multiple CSV files (night split into chunks)",
            "URL to CSV/ZIP (public link)",
        ],
        index=0,
    )

    df_raw = None
    source_desc = None

    try:
        if mode == "Single CSV file (≤200MB)":
            uploaded_raw = st.file_uploader(
                "Upload a single DualSleep CSV",
                type=["csv"],
                key="single_csv",
            )
            if uploaded_raw is not None:
                df_raw = pd.read_csv(uploaded_raw)
                source_desc = "single uploaded CSV"

        elif mode == "ZIP file with one or more CSVs":
            uploaded_zip = st.file_uploader(
                "Upload a ZIP file containing one or more DualSleep CSVs",
                type=["zip"],
                key="zip_upload",
            )
            if uploaded_zip is not None:
                df_raw = load_from_zip(uploaded_zip)
                source_desc = "ZIP archive"

        elif mode == "Multiple CSV files (night split into chunks)":
            uploaded_many = st.file_uploader(
                "Upload one or more CSV files (they will be concatenated in order)",
                type=["csv"],
                accept_multiple_files=True,
                key="multi_csv",
            )
            if uploaded_many:
                df_raw = _concat_csv_files(uploaded_many)
                source_desc = f"{len(uploaded_many)} CSV chunks"

        elif mode == "URL to CSV/ZIP (public link)":
            url = st.text_input(
                "Paste a direct link to a CSV or ZIP file (must be publicly accessible)"
            )
            fetch = st.button("Fetch data from URL")
            if fetch and url:
                df_raw = load_from_url(url.strip())
                source_desc = "remote URL"

    except Exception as e:
        st.error(f"Error while loading data: {e}")

    if df_raw is not None:
        try:
            st.success(f"Loaded raw data from {source_desc}.")
            st.write("Raw file shape:", df_raw.shape)
            st.write("Columns:", list(df_raw.columns))

            # Build win60-style features
            win60_up = to_windows_60s_uploaded(df_raw, subject_id="uploaded")

            st.success(
                f"Built minute-level features: {win60_up.shape[0]} rows, "
                f"{win60_up.shape[1]} columns."
            )
            st.write("Preview of engineered features:")
            st.dataframe(win60_up.head())

            # Check that all feature_cols expected by the model are present
            missing_feats = [c for c in feature_cols if c not in win60_up.columns]
            if missing_feats:
                st.error(
                    "The engineered table is missing some features that the model expects.\n\n"
                    f"Missing columns (first few): {missing_feats[:10]}"
                )
            else:
                # Run model on uploaded data
                X_user = win60_up[feature_cols].values
                scores_user = model.decision_function(X_user)

                # Same final threshold as notebook
                FINAL_THR = -0.6
                y_pred_user = (scores_user > FINAL_THR).astype("int8")

                win60_up["y_pred"] = y_pred_user

                # Metrics (if ground truth y exists)
                if "y" in win60_up.columns:
                    tn, fp, fn, tp = confusion_matrix(
                        win60_up["y"], win60_up["y_pred"], labels=[0, 1]
                    ).ravel()
                    sens_u = tp / (tp + fn + 1e-9)
                    spec_u = tn / (tn + fp + 1e-9)
                    f1_u = f1_score(
                        win60_up["y"], win60_up["y_pred"], average="macro"
                    )

                    st.subheader("Metrics on uploaded file")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Sensitivity (sleep)", f"{sens_u:.3f}")
                    c2.metric("Specificity (wake)", f"{spec_u:.3f}")
                    c3.metric("F1 (macro)", f"{f1_u:.3f}")
                else:
                    st.info(
                        "No ground-truth `y` column available, so only predictions are shown."
                    )

                # Model confidence summary
                st.subheader("Model confidence on uploaded file")

                # Distance from threshold as a rough confidence score
                dist_from_thr = np.abs(scores_user - FINAL_THR)

                # Define confidence bands
                conf_bins = [0, 0.5, 1.5, np.inf]
                conf_labels = ["low", "medium", "high"]
                conf_cat = pd.cut(
                    dist_from_thr,
                    bins=conf_bins,
                    labels=conf_labels,
                    include_lowest=True,
                )

                win60_up["confidence_level"] = conf_cat

                conf_summary = (
                    win60_up["confidence_level"]
                    .value_counts(normalize=True)
                    .reindex(conf_labels)
                    .mul(100)
                    .round(1)
                )

                st.markdown(
                    """
We treat the **distance from the decision threshold** as a rough measure of confidence:

- **High**: score is far from the threshold → model is very sure  
- **Medium**: score is moderately far → some uncertainty  
- **Low**: score is close to the threshold → ambiguous minutes (often around transitions)
"""
                )

                st.write("Percentage of minutes in each confidence band:")
                st.dataframe(
                    conf_summary.rename("percent_of_minutes")
                    .to_frame()
                    .style.format("{:.1f}%")
                )

                # Timeline for uploaded data
                if "timestamp" in win60_up.columns:
                    st.subheader("Uploaded data – sleep vs wake (true vs predicted)")

                    win60_up = win60_up.sort_values("timestamp").copy()
                    t0 = win60_up["timestamp"].min()
                    hrs_uploaded = st.slider(
                        "Show first N hours (uploaded data)",
                        min_value=2,
                        max_value=24,
                        value=8,
                        key="hrs_uploaded",
                    )
                    t_end = t0 + pd.Timedelta(hours=hrs_uploaded)
                    d_up = win60_up[win60_up["timestamp"] <= t_end].copy()

                    fig_u, ax_u = plt.subplots(figsize=(10, 3))
                    if "y" in d_up.columns:
                        ax_u.plot(
                            d_up["timestamp"],
                            d_up["y"],
                            drawstyle="steps-post",
                            label="true",
                            alpha=0.9,
                        )
                    ax_u.plot(
                        d_up["timestamp"],
                        d_up["y_pred"],
                        drawstyle="steps-post",
                        label="pred",
                        alpha=0.9,
                    )

                    ax_u.set_yticks([0, 1])
                    ax_u.set_yticklabels(["wake", "sleep"])
                    ax_u.set_xlabel("time")
                    ax_u.set_title("Uploaded data – sleep vs wake (true vs pred)")
                    ax_u.legend()
                    fig_u.autofmt_xdate()
                    st.pyplot(fig_u)
                else:
                    st.info(
                        "No `timestamp` column found after processing – "
                        "cannot draw a timeline plot."
                    )

                # Download predictions
                csv_bytes = win60_up.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download predictions as CSV",
                    data=csv_bytes,
                    file_name="dualsleep_uploaded_predictions.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error while processing uploaded raw CSV: {e}")
    else:
        st.info("Provide a DualSleep-style raw dataset to run the full pipeline.")

# TAB 4: How the model works
with tab_info:
    st.header("Model info – how DualSleep SVM works")

    st.markdown(
        """
**Model type**  
- RBF-kernel Support Vector Machine (SVM) classifier.

**Training scheme (LOSO)**  
- We train on all but one subject, test on the held-out subject.  
- Repeat this for every subject and average the metrics.  
- This mimics a “new user” the model has never seen before.

**Input features per 60-second window include**  
- Summary stats of accelerometer signals (`back` and `thigh`):  
  - mean, std, min, max, 25th/75th percentiles, skew, kurtosis, energy.  
- Magnitude features:  
  - `back_mag_mean`, `thigh_mag_mean`.  
- Correlations between back and thigh axes:  
  - `corr_back_x_thigh_x`, `corr_back_y_thigh_y`, `corr_back_z_thigh_z`,  
    and magnitude correlation `back_thigh_corr_mag`.  
- Cyclic time encoding:  
  - hour of day (sin/cos), day of week (sin/cos), month position (sin/cos).  
- Circadian prior:  
  - `sleep_prob_clock` = empirical probability of sleep at a given clock minute (0–1439).

**Decision scores and confidence**  
- The SVM outputs a **decision score** for each minute:  
  - Positive score → more like *sleep*  
  - Negative score → more like *wake*  
- We don’t use the raw 0.0 cut; instead we shift the final threshold (e.g. **−0.6**) to:  
  - reduce false sleep during wake,  
  - while keeping sleep sensitivity in a reasonable range.

**Why this matters for users**  
- If the model’s score is very far from the threshold (e.g., −3 or +3),  
  it is more “confident” about being wake or sleep.  
- Minutes near the threshold are more ambiguous, which is expected  
  around transitions (falling asleep / waking up).
"""
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="font-size: 0.8rem; color: #777; text-align: center; margin-top: 0.5rem;">
        DualSleep Sleep/Wake Classifier · Built for MathWorks<br>
        Model: RBF-kernel SVM with LOSO cross-validation on the DualSleep dataset<br>
    </div>
    """,
    unsafe_allow_html=True,
)