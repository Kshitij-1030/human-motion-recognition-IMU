# Human Motion Recognition using IMU data

### 👥 **Team Members**

| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Karla Armoush   | @karmou01 | Worked jointly with Yuting on the HARTH model and refined our real-time demo |
| Kshitij Kesharwani  | @Kshitij-1030 | Worked with Sukie on the DualSleep (SWR) model and developed the DualSleep website interface  |
| Yuting Lin    | @YutingLin0 | Contributed to developing the HARTH model with Karla and worked on our real-time demo |
| Raymond Xu     | @Bruvato | Worked jointly with Cynthia on the Walking Speed model and created the initial structure for our real-time demo |
| Sukie Zhang      | @sukiecodes | Collaborated on developing the DualSleep (SWR) model with Kshitij |
| Cynthia Zhu     | @Cynthiazhu0808 | Worked with Raymond on the development of the Walking Speed model |

---

## 🎯 **Project Highlights**

- Developed three machine learning models (HARTH, DualSleep, Walking Speed) using random forest and support vector machines to classify activities, sleep/wake, and different walking speeds.
- Generated actionable insights and used MATLAB to produce a real-time demo of our findings at MathWorks.
- Learned how to do feature engineering from raw IMU signals through extracting meaningful information from raw acceleration (x, y, z) coordinates by computing features such as mean, standard deviation, magnitude, and frequency-based metrics.
- Worked with large, continuous time-series datasets.
- In the end, we developed an end-to-end ML pipeline, including model deployment using MATLAB!


---

## 👩🏽‍💻 **Setup and Installation**

This repository contains:
- **HARTH (Human Activity Recoginition)** model training notebooks and real-time demo files in `Harth/`
- **DualSleep (Sleep vs. Wake Recogintion)** model training notebooks and Streamlit web application in `DualSleep/`
- **Walking Speed (Gait Speed Classification)** model training notebooks for predicting walking speed categories in `WalkingSpeed/`

---

### 1) Clone the repository
```bash
git clone git@github.com:Kshitij-1030/human-motion-recognition-IMU.git
cd human-motion-recognition-IMU
```

---

### 2) Create and activate a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

---

### 3) Install dependencies
These dependencies are sufficient to run the model training notebooks across HARTH, DualSleep, and Walking Speed models:
```bash
pip install pandas numpy matplotlib scikit-learn scipy joblib jupyter
```
Note: The DualSleep Streamlit web application has additional dependencies listed in
`DualSleep/webapp/requirements.txt`.

---

### 4) Open the repository in VS Code
Open the repository in VS Code and install the following extensions if prompted:
- Python  
- Jupyter  

---

### 5) Run the model training notebooks

- Navigate to the relevant subfolder  
- Open the corresponding `.ipynb` notebook  
- Run all cells using **Run All** (top toolbar), or run cells individually using the play button

---

### 6) Output files
The HARTH notebook saves the trained model + feature schema to the folder as:
```bash
harth_rf_thigh.pkl
thigh_feature_names.csv
```
These files are used by the real-time demo.

---

## 📈 **Real-time Demo (MATLAB Mobile + MATLAB Desktop + Python model)**
This demo streams accelerometer data from your phone into MATLAB in real time and runs the thigh-only HARTH random-forest model on sliding windows

Requirements:
MATLAB (R2022b or later recommended)
MATLAB Mobile app installed on your phone
Phone and computer on the same Wi-Fi network

1) Configure Python for MATLAB 
In MATLAB, point pyenv to the Python you used to train/save the model (where sckiki-learn, pandas, and joblib are installed):
```bash
pyenv('Version','/usr/bin/python3')
```

2) Open the real-time demo folder:
Navigate to the following folder in MATLAB:
```bash
Harth/realtime_demo/
```
Ensure the following files are in the same directory:
```bash
harth_rf_thigh.pkl
thigh_feature_names.csv
extractWindowFeaturesThigh.m
live_demo_thigh.m
```

3) Connect MATLAB Mobile
On your phone:
-	Open MATLAB Mobile
- Go to settings -> Connect to -> MATLAB (not MathWorks Cloud)
- Ensure:
  - You are signed in with the same account as MATLAB Desktop
  - Phone and computer are on the same network
  - Sensors -> Acceleration is enabled
  - Stream to is set to MATLAB

4) Run the live demo
In the MATLAB command window:
```bash
run live_demo_thigh
```

## 🏗️ **Project Overview**

Our project was completed as part of the Break Through Tech AI Studio Program, where we collaborated with MathWorks engineers and MIT mentors to design a machine-learning system capable of recognizing human motion from wearable sensor data.
Using open-source IMU datasets, we built models that classify physical activities, detect sleep vs wakefulness, and estimate walking speed categories. 
The real-world significance of this work lies in its broad applicability to wearable tech, health monitoring, and performance tracking. IMU-based systems can provide users, clinicians, and companies with continuous, low-cost insights into mobility, sleep quality, and daily activity patterns. By building robust models and deploying them in interactive environments we demonstrate how machine learning can transform raw motion signals into actionable information for wellness and human-centered design.

---

## 📊 **Data Exploration**

The dataset(s) used: HAR/SWR Datasets and Machine Learning Experiments (Link here)
Data cleaning: We grouped similar features (for example, ascending stairs and descending stairs for HARTH), null and duplicate value detection
Data preprocessing: Due to how big each time series dataset was, we segmented our data into fixed time windows before feature extraction (60 seconds for SWR, 2 seconds for HAR, 5 seconds for Walking Speed), and a majority label voting was used. Within each window, we computed statistical features such as mean, standard deviation, minimum, maximum, magnitudes and quartiles.
Challenges and assumptions when working with the dataset(s): We initially underestimated the size of our datasets, which made it difficult to work with them locally and collaborate since we couldn’t push the data directly to GitHub. To resolve this, we ultimately shifted our workflow to Google Colab for real-time collaboration.

---

## 🧠 **Model Development**

## Model Development

### HARTH: Human Activity Recognition

- **Model:** Random Forest classifier  
- **Features:** 2 s windows (50 Hz) of trunk and thigh accelerometer data with summary/statistical features
- **Train / validation / test split:**
  - GroupShuffleSplit **by subject**
  - 70% train, 15% validation, 15% test  
- **Hyperparameter tuning (GridSearchCV):**
  - `n_estimators = 200`
  - `max_depth = 24`
  - `min_samples_leaf = 1`

---

### DualSleep: Sleep vs. Wake Classification

- **Model:** RBF-kernel SVM (with `StandardScaler` and `class_weight="balanced"`).  
- **Task:** Binary **sleep vs. wake** (all non-wake stages collapsed into “sleep”).  
- **Features:** 60 s aggregated features from thigh + back accelerometers and temperature.  
- **Evaluation:** **Leave-One-Subject-Out (LOSO)** cross-validation for subject-level generalization.  
- **Hyperparameter tuning:** Grid search over `C` and `gamma`, followed by decision-threshold tuning; final decision threshold set to **−0.6**.

---

### Walking Speed

- **Model:** Random Forest (regressor/classifier depending on target; see notebook).  
- **Train / test split:** 80% training, 20% testing.  
- **Hyperparameter tuning (Grid Search):**
  - `n_estimators = 100`
  - `min_samples_leaf = 1`
  - `min_samples_split = 10`
  - `max_depth = None`

---

## 📈 **Results & Key Findings**

HARTH Activity Classification (Random Forest): 
Achieved 91.8% accuracy after hyperparameter tuning.
Main challenge: class imbalance, especially for stairs (much fewer samples).
Confusion matrix shows walking ↔ stairs misclassifications due to similar movement patterns.
DualSleep (SVM):
Using LOSO cross-validation, the final tuned model achieved:
Sensitivity: 0.752
Specificity: 0.758
Balanced accuracy: 0.755.
Walking Speed Classification (Random Forest): Achieved a test accuracy of 90–95% depending on the walking speed class..

---

## 🚀 **Next Steps**

If we had more time and resources, we would’ve loved to explore using both thigh and back accelerometer information for our MATLAB real-time demo, as well as migrate from a MATLAB GUI to a full-stack application to showcase our models’ performances. Currently, our demo collects data from smartphone sensors through the MATLAB mobile app, but we would also be interested in experimenting with running the classification algorithm on real hardware. In terms of the DualSleep model, expanding the model from binary sleep/wake detection to full sleep-stage classification for deeper analysis, as well as integrating the app with a real-time data stream to enable live prediction and visualization.

---

## 📝 **License**

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

---

## 📄 References

1. **Reiss, A., et al. (2023).**  
   *Deep learning for human activity recognition using wearable sensor data: The HARTH dataset.*  
   *Sensors*, 23(14), 6458.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC10385571/

2. **Haghayegh, S., Khoshnevis, S., Smolensky, M. H., & Diller, K. R. (2019).**  
   *A machine learning model for predicting sleep and wakefulness based on Accelerometry, Skin Temperature and Contextual Information.*  
   *Nature and Science of Sleep*, 11, 265–278.  
   https://www.dovepress.com/a-machine-learning-model-for-predicting-sleep-and-wakefulness-based-on-peer-reviewed-fulltext-article-NSS

---

## 🙏 **Acknowledgements**

A huge thank you to Noah, our challenge advisor; Mimi, our TA; Maxime, Chu, and everyone else from Break Through Tech; as well as everyone from our host company, MathWorks. We could not have done it without you all!
