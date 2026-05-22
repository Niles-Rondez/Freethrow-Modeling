"""
basketball_model.py

Core mathematical model for the basketball free throw simulator.
This file implements the equations of motion, solves for the required velocity
for a center shot, and checks if a given shot clears the front rim and doesn't
overshoot the back rim.
"""

import numpy as np

# Physical constants from blueprint.md (standard SI units)
g = -9.8              # Gravitational acceleration (m/s^2)
l = 4.115             # Horizontal distance from release to hoop center (13 ft 6.5 in = 4.115 m)
Dr = 0.457            # Hoop rim diameter (1.5 ft = 0.457 m)
Db = 0.244            # Ball diameter (0.8 ft = 0.244 m)
hoop_height = 3.048   # Standard hoop height (10 ft = 3.048 m)


def get_h(shooter_height_m):
    """
    Computes the net vertical rise from release point to hoop center.
    Assumes ball release height is 1.25 times the shooter's height.
    
    Parameters:
        shooter_height_m (float): Shooter's height in meters.
        
    Returns:
        h (float): Hoop height minus release height (can be negative for very tall shooters).
    """
    release_height = shooter_height_m * 1.25
    return hoop_height - release_height


def required_v0(theta_deg, h):
    """
    Calculates the initial velocity (v0) required to send the ball directly
    through the center of the hoop, given the release angle (theta) and
    vertical rise (h).
    
    Formula:
        v0 = (l / cos(theta)) * sqrt(-g / (2 * (l * tan(theta) - h)))
        
    Parameters:
        theta_deg (float): Release angle in degrees from horizontal.
        h (float): Hoop height minus release height.
        
    Returns:
        v0 (float or None): Required velocity in m/s, or None if the angle
                            is too flat to reach the hoop height (denominator <= 0).
    """
    theta_rad = np.radians(theta_deg)
    denom = 2 * (l * np.tan(theta_rad) - h)
    
    # Skip angles where the ball cannot physically clear the height of the hoop
    if denom <= 0:
        return None
        
    return (l / np.cos(theta_rad)) * np.sqrt(-g / denom)


def get_trajectory(theta_deg, v0, h, n=500):
    """
    Generates time, x-coordinates, and y-coordinates of the ball's trajectory
    from release (t=0) until the ball descends to the hoop height (t=T).
    
    Parameters:
        theta_deg (float): Release angle in degrees from horizontal.
        v0 (float): Initial velocity in m/s.
        h (float): Hoop height minus release height.
        n (int): Number of trajectory points to generate.
        
    Returns:
        ts, x, y (arrays or (None, None, None)): Time steps, horizontal position, 
                                                 and vertical position relative to release point.
    """
    theta_rad = np.radians(theta_deg)
    sin_theta = np.sin(theta_rad)
    cos_theta = np.cos(theta_rad)
    
    # Check if the ball has enough velocity to reach hoop height h
    discriminant = (v0 * sin_theta)**2 + 2 * g * h
    if discriminant < 0:
        return None, None, None
        
    # Solve quadratic equation for landing time T (descending root)
    T = (-v0 * sin_theta - np.sqrt(discriminant)) / g
    
    # Time must be positive
    if T <= 0:
        return None, None, None
        
    ts = np.linspace(0, T, n)
    x = v0 * cos_theta * ts
    y = v0 * sin_theta * ts + 0.5 * g * ts**2
    
    return ts, x, y


def check_shot(theta_deg, v0, h):
    """
    Analyzes a shot's trajectory to determine if it goes in the hoop.
    Checks front rim clearance and back rim overshoot.
    
    Parameters:
        theta_deg (float): Release angle in degrees.
        v0 (float): Initial velocity in m/s.
        h (float): Hoop height minus release height.
        
    Returns:
        dict: A dictionary containing:
            - 'result' (str): 'made', 'hit_front_rim', 'overshoot_back_rim', 
                              'undershoot_front_rim', or 'miss_low' (never reaches hoop height)
            - 'min_dist_to_front_rim' (float): Minimum distance from ball center to front rim (m)
            - 'right_edge_at_landing' (float): Rightmost edge of ball when center is at hoop height (m)
            - 'left_edge_at_landing' (float): Leftmost edge of ball when center is at hoop height (m)
            - 'trajectory' (tuple): (ts, x, y) or (None, None, None)
    """
    # 1. Generate trajectory
    ts, x, y = get_trajectory(theta_deg, v0, h)
    
    if ts is None:
        return {
            'result': 'miss_low',
            'min_dist_to_front_rim': 0.0,
            'right_edge_at_landing': 0.0,
            'left_edge_at_landing': 0.0,
            'trajectory': (None, None, None)
        }
        
    x_land = x[-1]
    right_edge = x_land + Db / 2
    left_edge = x_land - Db / 2
    
    # 2. Check front rim clearance (ball center to front rim coordinate: x = l - Dr/2, y = h)
    front_rim_x = l - Dr / 2
    front_rim_y = h
    dists_sq = (x - front_rim_x)**2 + (y - front_rim_y)**2
    min_dist = np.sqrt(np.min(dists_sq))
    
    # 3. Success checks
    clears_front = min_dist > Db / 2
    doesnt_overshoot = right_edge <= l + Dr / 2
    doesnt_undershoot = left_edge >= l - Dr / 2
    
    if not clears_front:
        result = 'hit_front_rim'
    elif not doesnt_overshoot:
        result = 'overshoot_back_rim'
    elif not doesnt_undershoot:
        result = 'undershoot_front_rim'
    else:
        result = 'made'
        
    return {
        'result': result,
        'min_dist_to_front_rim': min_dist,
        'right_edge_at_landing': right_edge,
        'left_edge_at_landing': left_edge,
        'trajectory': (ts, x, y)
    }
