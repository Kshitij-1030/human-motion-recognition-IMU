function featRow = extractWindowFeaturesThigh(W)
    % W: table for a 2 s window with variables:
    %     thigh_x, thigh_y, thigh_z   (in g, already mapped to HARTH axes)
    
    tx = W.thigh_x;
    ty = W.thigh_y;
    tz = W.thigh_z;
    
    vars = {'thigh_x','thigh_y','thigh_z'};
    vals = [tx, ty, tz];
    
    % Per-axis mean/std
    mu = mean(vals, 1);
    sd = std(vals, 0, 1);
    
    % Vector magnitude
    thigh_mag = sqrt(tx.^2 + ty.^2 + tz.^2);
    
    featNames = [ ...
        strcat(vars,'_mean'), ...
        strcat(vars,'_std'), ...
        {'thigh_mag_mean','thigh_mag_std'}];
    
    featVals  = [ ...
        mu, sd, ...
        mean(thigh_mag), std(thigh_mag)];
    
    featRow = array2table(featVals, 'VariableNames', featNames);
    end
    