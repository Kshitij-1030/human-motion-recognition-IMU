%% HARTH — Thigh-only live demo (MATLAB Mobile + Python RF model)
% Folder must contain:
%   - harth_rf_thigh.pkl
%   - thigh_feature_names.csv
%   - extractWindowFeaturesThigh.m
%
% PHONE POSITION (for this script):
%   - Strap phone on the FRONT of your RIGHT thigh
%   - Portrait orientation
%   - TOP edge of phone pointing UP toward your hip
%   - SCREEN facing FORWARD (away from your body)
%

clear; clc; close all;

%% Load Python thigh-only model + feature order

fprintf("Loading THIGH model & feature order...\n");
mdl = py.joblib.load('harth_rf_thigh.pkl');

% Load and sanitize feature order 
featOrder = string(readlines('thigh_feature_names.csv'));
featOrder = strtrim(featOrder);
featOrder = featOrder(strlength(featOrder) > 0);
fprintf("Thigh feature names loaded: %d\n", numel(featOrder));

% Read class names from the sklearn model 
try
    classes = string(cell(mdl.classes_.tolist()));
catch
    try
        classes = string(cell(py.list(mdl.classes_)));
    catch
        warning("Could not read class names from model; using generic names.");
        classes = "class" + (1:8);
    end
end
fprintf("Model classes: %s\n", strjoin(classes,", "));

%% Connect phone via MATLAB Mobile (app: Stream to = MATLAB)

fprintf("\nCreating mobiledev object (open MATLAB Mobile, Stream to=MATLAB)...\n");
m = mobiledev;                            

m.SampleRate = 50;                       % match HARTH training (50 Hz)
m.AccelerationSensorEnabled = true;

%% Record a short snippet
fprintf("\nRecording ~6 s of accelerometer (THIGH)...\n");

% Clear any existing logs
try
    discardlogs(m);
catch
    try; accellog(m); end 
end

m.Logging = true; pause(6); m.Logging = false;

[acc, tAcc] = accellog(m);               % Nx3 accel (m/s^2)
if isempty(acc)
    error("No samples received. Check the app's Acceleration toggle and permissions.");
end
dur  = tAcc(end)-tAcc(1);
rate = size(acc,1) / max(1, dur);
fprintf("Samples: %d | Duration: %.2f s | ~%.1f Hz\n", size(acc,1), dur, rate);

%% Convert to HARTH units (g) and map MATLAB Mobile axes -> HARTH thigh axes
% MATLAB Mobile: X right, Y top, Z out of screen, in m/s^2.
% HARTH thigh sensor: x down, y right, z backward, in g.

g = 9.81;
acc = acc / g;          % convert m/s^2 -> g

accX = acc(:,1);     
accY = acc(:,2);        
accZ = acc(:,3);       

% HARTH convention:
%   thigh_x: DOWN      => -Y_device
%   thigh_y: RIGHT     => +X_device
%   thigh_z: BACKWARD  => -Z_device

thigh_x = -accY;  
thigh_y =  accX; 
thigh_z = -accZ;   

T = table(thigh_x, thigh_y, thigh_z, tAcc, ...
          'VariableNames', {'thigh_x','thigh_y','thigh_z','timestamp'});

fprintf("First 3 rows (mapped thigh axes, in g):\n");
disp(T(1:min(3,height(T)), {'thigh_x','thigh_y','thigh_z'}))

%% Slide over 2 s windows and predict
fs  = 50;
win = 2*fs;           
hop = win;              % non-overlapping for simplicity
i0  = 1;

figure('Name','HARTH Thigh-only Live Demo');

k = 0;
while (i0+win-1) <= height(T)
    k = k + 1;
    W = T(i0:i0+win-1, {'thigh_x','thigh_y','thigh_z'});

    % Thigh-only feature extraction (MATLAB function)
    feat = extractWindowFeaturesThigh(W);

    % Ensure names & order exactly match Python training
    curNames = string(feat.Properties.VariableNames);
    missing  = setdiff(featOrder, curNames, 'stable');  % preserve training order

    for r = 1:numel(missing)
        nm = char(missing(r));            % tables prefer char variable names
        feat.(nm) = 0;                    % fill any missing features with 0
    end
    feat = feat(:, cellstr(featOrder));   % reorder to training order

    if k == 1
        fprintf("\n[Window %d] feature vector preview (first columns):\n", k);
        disp(feat(:,1:min(10,width(feat))))
    end

    % Predict with Python RF model
    try
        feat_py  = py.pandas.DataFrame(feat);
        yhat_py  = mdl.predict(feat_py);
        proba_py = mdl.predict_proba(feat_py);
    catch ME
        warning('PythonPredictFail:msg','Python predict failed: %s', ME.message);
        break;
    end

    % Convert Python -> MATLAB 
    predLabel = py_first_str(yhat_py);
    probs     = py_row_double(proba_py);

    % Print to Command Window
    fprintf("[Window %d] Predicted: %s | probs=[", k, predLabel);
    fprintf("%.2f ", probs);
    fprintf("]\n");

    % Simple visualization
    clf;
    subplot(2,1,1);
    plot((0:win-1)/fs, W.thigh_x);
    title("Thigh (x = down) accel"); xlabel('Seconds'); ylabel('g');

    subplot(2,1,2);
    bar(probs); ylim([0 1]);
    xticks(1:numel(probs)); xticklabels(classes); xtickangle(30);
    ylabel('Probability');
    sgtitle("Predicted: " + predLabel);

    drawnow limitrate;
    i0 = i0 + hop;
end

fprintf("\nDone. Processed %d window(s).\n", k);

%% Helper functions (Python → MATLAB conversions)
function s = py_first_str(obj)
% Return the first element of a Python array/Series/list as MATLAB string.
    s = "";
    try, s = string(obj{1});        return; end   % py.list (1-based in MATLAB interop)
    try, s = string(obj{0});        return; end   % zero-based fallback
    try, s = string(obj.item(0));   return; end   % numpy.ndarray
    try, s = string(obj.iloc{0});   return; end   % pandas.Series
    try
        tmp = obj.tolist();
        s   = string(tmp{1});
        return
    end
    error('py_first_str:unsupported', 'Unable to read first element from Python object.');
end

function v = py_row_double(obj)
% Convert a Python proba array (shape 1xC or C) to a 1xC double row.
    try
        arr = obj.squeeze().tolist();           % numpy / pandas
        v   = double(py.numpy.array(arr));
        v   = reshape(v, 1, []);
        return
    end
    try
        v = double(py.array.array('d', obj.ravel().tolist()));
        v = reshape(v, 1, []);
        return
    end
    try
        arr = obj{1};                           % py.list fallback
        v   = double(py.array.array('d', arr));
        v   = reshape(v, 1, []);
        return
    end
    error('py_row_double:unsupported', 'Unable to convert Python proba to double row.');
end
