% Real-Time Acceleration Data Collection and Plotting with API Streaming

clear; clc; close all;

% API Configuration
API_URL = 'http://127.0.0.1:8000/api/sensor';

% Create connection to mobile device
m = mobiledev;

% Enable acceleration sensor
m.AccelerationSensorEnabled = 1;

% Set up figure for plotting
figure('Name', 'Real-Time Acceleration Data');

% Create animated line objects for each acceleration axis
subplot(3,1,1);
h1 = animatedline('Color', 'r', 'LineWidth', 2);
ylabel('X Acceleration (m/s²)');
title('Real-Time Acceleration Data');
grid on;

subplot(3,1,2);
h2 = animatedline('Color', 'g', 'LineWidth', 2);
ylabel('Y Acceleration (m/s²)');
grid on;

subplot(3,1,3);
h3 = animatedline('Color', 'b', 'LineWidth', 2);
ylabel('Z Acceleration (m/s²)');
xlabel('Time (s)');
grid on;

% Initialize timing
startTime = datetime('now');

% Real-time data collection loop (runs indefinitely)
while true
    % Get current acceleration data
    [a, t] = accellog(m);
    
    if ~isempty(a)
        % Get the most recent data point
        x = a(end, 1);
        y = a(end, 2);
        z = a(end, 3);
        
        % Convert time to numeric seconds
        if isdatetime(t)
            currentTime = seconds(t(end) - t(1));
        else
            currentTime = t(end) - t(1);
        end
        
        % Ensure all values are numeric doubles
        currentTime = double(currentTime);
        x = double(x);
        y = double(y);
        z = double(z);
        
        % Add points to animated lines
        addpoints(h1, currentTime, x);
        addpoints(h2, currentTime, y);
        addpoints(h3, currentTime, z);
        
        % Stream data to FastAPI endpoint
        try
            data = struct('timestamp', currentTime, ...
                         'x', x, ...
                         'y', y, ...
                         'z', z);
            jsonData = jsonencode(data);
            
            % Use HTTP interface instead of webwrite
            import matlab.net.*
            import matlab.net.http.*
            
            uri = URI(API_URL);
            header = HeaderField('Content-Type', 'application/json');
            method = RequestMethod.POST;
            request = RequestMessage(method, header, jsonData);
            
            response = send(request, uri);
        catch err
            warning('Failed to send data to API: %s', err.message);
        end
        
        % Update plots
        drawnow limitrate;
    end
    
    pause(0.05); % Small pause to control update rate
end

% Disable sensor after collection (won't reach here unless manually stopped)
m.AccelerationSensorEnabled = 0;

fprintf('Data collection stopped!\n');