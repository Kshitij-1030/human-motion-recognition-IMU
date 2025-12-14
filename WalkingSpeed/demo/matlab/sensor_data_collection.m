% Real-Time Orientation Data Collection and Plotting with API Streaming

clear; clc; close all;

% API Configuration
API_URL = 'http://127.0.0.1:8000/orientation';

% Create connection to mobile device
m = mobiledev;

% Enable orientation sensor
m.OrientationSensorEnabled = 1;

% Set up figure for plotting
figure('Name', 'Real-Time Orientation Data');

% Create animated line objects for each orientation angle
subplot(3,1,1);
h1 = animatedline('Color', 'r', 'LineWidth', 2);
ylabel('Azimuth (deg)');
title('Real-Time Orientation Data');
grid on;

subplot(3,1,2);
h2 = animatedline('Color', 'g', 'LineWidth', 2);
ylabel('Pitch (deg)');
grid on;

subplot(3,1,3);
h3 = animatedline('Color', 'b', 'LineWidth', 2);
ylabel('Roll (deg)');
xlabel('Time (s)');
grid on;

% Initialize timing
startTime = datetime('now');
duration = 60; % Collection duration in seconds

% Real-time data collection loop
while seconds(datetime('now') - startTime) < duration
    % Get current orientation data
    [o, t] = orientlog(m);
    
    if ~isempty(o)
        % Get the most recent data point
        azimuth = o(end, 1);
        pitch = o(end, 2);
        roll = o(end, 3);
        
        % Convert time to numeric seconds
        if isdatetime(t)
            currentTime = seconds(t(end) - t(1));
        else
            currentTime = t(end) - t(1);
        end
        
        % Ensure all values are numeric doubles
        currentTime = double(currentTime);
        azimuth = double(azimuth);
        pitch = double(pitch);
        roll = double(roll);
        
        % Add points to animated lines
        addpoints(h1, currentTime, azimuth);
        addpoints(h2, currentTime, pitch);
        addpoints(h3, currentTime, roll);
        
        % Stream data to FastAPI endpoint
        try
            data = struct('timestamp', currentTime, ...
                         'azimuth', azimuth, ...
                         'pitch', pitch, ...
                         'roll', roll);
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

% Disable sensor after collection
m.OrientationSensorEnabled = 0;

fprintf('Data collection complete!\n');