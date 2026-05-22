"""
optimizer.py

Optimization functions for the basketball free throw simulator.
This file implements the binary search to find the lower and upper angle bounds 
for a successful shot (allowing us to compute the error margin), searches for the
optimal release angle, and generates comparison tables for different shooter heights.
"""

import numpy as np
import basketball_model as bm

def find_theta_low(theta0, v0, h):
    """
    Finds the lowest release angle below theta0 that still results in a made shot,
    holding initial velocity v0 constant.
    
    Parameters:
        theta0 (float): Target release angle in degrees.
        v0 (float): Initial velocity in m/s.
        h (float): Hoop height minus release height.
        
    Returns:
        theta_low (float): Lowest successful angle in degrees.
    """
    # Start checking below theta0 to find a miss angle
    low = theta0 - 1.0
    while low > 10.0 and bm.check_shot(low, v0, h)['result'] == 'made':
        low -= 5.0
        
    high = theta0
    
    # Binary search for the transition from Miss (False) to Make (True)
    # 25 iterations gives a precision of ~3e-7 degrees
    for _ in range(25):
        mid = (low + high) / 2
        if bm.check_shot(mid, v0, h)['result'] == 'made':
            high = mid  # mid is inside the successful region, so lower bound is <= mid
        else:
            low = mid   # mid is outside, so lower bound is > mid
            
    return high


def find_theta_high(theta0, v0, h):
    """
    Finds the highest release angle above theta0 that still results in a made shot,
    holding initial velocity v0 constant.
    
    Parameters:
        theta0 (float): Target release angle in degrees.
        v0 (float): Initial velocity in m/s.
        h (float): Hoop height minus release height.
        
    Returns:
        theta_high (float): Highest successful angle in degrees.
    """
    # Start checking above theta0 to find a miss angle
    low = theta0
    high = theta0 + 1.0
    while high < 85.0 and bm.check_shot(high, v0, h)['result'] == 'made':
        high += 5.0
        
    # Binary search for the transition from Make (True) to Miss (False)
    for _ in range(25):
        mid = (low + high) / 2
        if bm.check_shot(mid, v0, h)['result'] == 'made':
            low = mid   # mid is inside the successful region, so upper bound is >= mid
        else:
            high = mid  # mid is outside, so upper bound is < mid
            
    return low


def compute_error_margin(theta0, h):
    """
    Computes the allowed angle error margin for a release angle theta0.
    Error margin is defined as min(theta_high - theta0, theta0 - theta_low).
    
    Parameters:
        theta0 (float): Target release angle in degrees.
        h (float): Hoop height minus release height.
        
    Returns:
        error_margin (float): Allowed error in degrees (0.0 if the center shot itself misses).
    """
    # 1. Compute velocity needed for a center shot at this angle
    v0 = bm.required_v0(theta0, h)
    if v0 is None:
        return 0.0
        
    # 2. Check if the center shot itself is actually made
    # (very flat angles may clip the front rim even if aimed at the center)
    shot = bm.check_shot(theta0, v0, h)
    if shot['result'] != 'made':
        return 0.0
        
    # 3. Find boundaries using binary search
    theta_low = find_theta_low(theta0, v0, h)
    theta_high = find_theta_high(theta0, v0, h)
    
    # 4. Error margin is the minimum deviation in either direction
    return min(theta0 - theta_low, theta_high - theta0)


def find_optimal_angle(h):
    """
    Finds the release angle that maximizes the allowed angle error margin
    by doing a grid search over a reasonable range of angles.
    
    Parameters:
        h (float): Hoop height minus release height.
        
    Returns:
        best_theta (float): Optimal release angle in degrees.
        best_error (float): Maximum error margin in degrees.
        v0 (float): Release velocity in m/s at the optimal angle.
        theta_low (float): Lower bound of successful angles at optimal velocity.
        theta_high (float): Upper bound of successful angles at optimal velocity.
    """
    # Range of typical release angles for free throws
    theta_vals = np.arange(40.0, 75.1, 0.1)
    errors = []
    
    for theta in theta_vals:
        errors.append(compute_error_margin(theta, h))
        
    best_idx = np.argmax(errors)
    best_theta = theta_vals[best_idx]
    best_error = errors[best_idx]
    
    # Calculate associated parameters for the optimal angle
    v0 = bm.required_v0(best_theta, h)
    if v0 is not None and best_error > 0:
        theta_low = find_theta_low(best_theta, v0, h)
        theta_high = find_theta_high(best_theta, v0, h)
    else:
        theta_low, theta_high = best_theta, best_theta
        
    return best_theta, best_error, v0, theta_low, theta_high


def get_optimal_heights_table():
    """
    Generates a table of optimal release angles, velocities, and error margins
    for heights from 5'0" to 7'3" (in 3-inch increments).
    
    Returns:
        list of dict: List containing optimal shot stats for each height.
    """
    heights = [
        (5, 0), (5, 3), (5, 6), (5, 9),
        (6, 0), (6, 3), (6, 6), (6, 9),
        (7, 0), (7, 3)
    ]
    
    table_data = []
    for ft, inches in heights:
        # Convert height to meters
        total_inches = ft * 12 + inches
        height_m = total_inches * 0.0254
        
        h = bm.get_h(height_m)
        best_theta, best_error, v0, t_low, t_high = find_optimal_angle(h)
        
        table_data.append({
            "height_str": f"{ft}'{inches}\"",
            "height_m": height_m,
            "release_height_m": height_m * 1.25,
            "opt_angle": best_theta,
            "opt_velocity": v0,
            "error_margin": best_error,
            "angle_range": f"[{t_low:.1f}°, {t_high:.1f}°]"
        })
        
    return table_data
