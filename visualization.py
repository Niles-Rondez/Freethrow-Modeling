"""
visualization.py

Visualization functions for the basketball free throw simulator.
Provides matplotlib figures for trajectory plotting, error margin curve,
and a 2D feasible region heatmap.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import basketball_model as bm
import optimizer as opt

# Standard styling constants
COLOR_MADE = '#2ca02c'        # Green
COLOR_MISS = '#d62728'        # Red
COLOR_RIM = '#ff7f0e'         # Orange (for the hoop)
COLOR_OPTIMAL = '#d4af37'     # Gold (for optimal point)
COLOR_CHOSEN = '#1f77b4'      # Blue (for user selected point)

def plot_trajectory(theta_deg, v0, h, result, min_d, r_edge, shooter_height_m):
    """
    Plots the basketball flight path relative to the court floor.
    Draws the release point, the basket rim, backboard, and the ball at landing.
    
    Parameters:
        theta_deg (float): Release angle in degrees.
        v0 (float): Release velocity in m/s.
        h (float): Hoop height minus release height.
        result (str): Shot result ('made', 'hit_front_rim', etc.)
        min_d (float): Minimum distance to front rim.
        r_edge (float): Ball right edge at landing height.
        shooter_height_m (float): Shooter's height in meters.
        
    Returns:
        fig: Matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(8.5, 5))
    
    # Calculate release height (m)
    release_height = shooter_height_m * 1.25
    
    # Generate trajectory arrays relative to release point
    ts, x, y = bm.get_trajectory(theta_deg, v0, h)
    
    # Draw court floor (y = 0)
    ax.axhline(0, color='gray', linestyle='-', linewidth=2, alpha=0.5)
    
    # Draw basket hoop (rim) at height y = 3.048m
    # Front rim is at x = l - Dr/2, back rim is at x = l + Dr/2
    front_rim_x = bm.l - bm.Dr / 2
    back_rim_x = bm.l + bm.Dr / 2
    hoop_y = bm.hoop_height
    
    # Draw hoop rim as thick orange line
    ax.plot([front_rim_x, back_rim_x], [hoop_y, hoop_y], color=COLOR_RIM, linewidth=4, label='Hoop Rim')
    ax.plot(front_rim_x, hoop_y, 'o', color=COLOR_RIM, markersize=6)
    ax.plot(back_rim_x, hoop_y, 'o', color=COLOR_RIM, markersize=6)
    
    # Draw backboard (vertical line 0.381 m behind the hoop center)
    backboard_x = bm.l + 0.381
    backboard_y_low = hoop_y - 0.305
    backboard_y_high = hoop_y + 0.914
    ax.plot([backboard_x, backboard_x], [backboard_y_low, backboard_y_high], color='darkgray', linewidth=5, label='Backboard')
    
    # Draw the support neck for the rim
    ax.plot([back_rim_x, backboard_x], [hoop_y, hoop_y], color='black', linewidth=2)
    
    # Draw the trajectory if it exists
    if x is not None and len(x) > 0:
        # Shift y coordinates to be relative to the floor
        x_plot = x
        y_plot = y + release_height
        
        # Determine trajectory color based on result
        traj_color = COLOR_MADE if result == 'made' else COLOR_MISS
        traj_style = '-' if result == 'made' else '--'
        
        ax.plot(x_plot, y_plot, color=traj_color, linestyle=traj_style, linewidth=2.5, label='Ball Center Path')
        
        # Draw the ball at its landing point (center is at x_land, y = hoop_height)
        x_land = x[-1]
        ball_circle = Circle((x_land, hoop_y), bm.Db / 2, color='orange', alpha=0.7, ec='black', lw=1.5, label='Ball at Landing')
        ax.add_patch(ball_circle)
        
        # Draw ball at release
        release_circle = Circle((0, release_height), bm.Db / 2, color='orange', alpha=0.3, ec='black', lw=1.0)
        ax.add_patch(release_circle)
    else:
        # Draw a small text indicating no trajectory
        ax.text(1.5, hoop_y / 2, "Ball never reaches hoop height", color='red', fontsize=12, ha='center')
    
    # Plot formatting
    ax.set_xlim(-0.5, bm.l + 0.8)
    ax.set_ylim(-0.1, 5.5)  # Let room for arc height
    ax.set_aspect('equal')
    ax.set_xlabel('Horizontal Distance (m)', fontsize=10)
    ax.set_ylabel('Vertical Height (m)', fontsize=10)
    
    # Result text box
    result_labels = {
        'made': ('MADE (Nothing but Net)', COLOR_MADE),
        'hit_front_rim': ('MISSED (Hit Front Rim)', COLOR_MISS),
        'overshoot_back_rim': ('MISSED (Overshot Back Rim)', COLOR_MISS),
        'undershoot_front_rim': ('MISSED (Short / Airball)', COLOR_MISS),
        'miss_low': ('MISSED (Shot Too Flat / Low)', COLOR_MISS)
    }
    
    label_text, box_color = result_labels.get(result, ('MISSED', COLOR_MISS))
    
    # Draw shooter release point label
    ax.plot(0, release_height, 'o', color='purple', markersize=8, label='Release Point')
    ax.annotate(f"Release Height\n{release_height:.2f} m", (0, release_height), textcoords="offset points", 
                xytext=(-10, 10), ha='center', fontsize=8, arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
    
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Title showing details of shot
    title_str = f"Angle: {theta_deg:.1f}° | Velocity: {v0:.2f} m/s | Result: {label_text}"
    ax.set_title(title_str, fontsize=12, fontweight='bold', color=box_color)
    
    return fig


def plot_error_function(theta_values, error_values, best_theta, chosen_theta, h):
    """
    Plots the error margin e(theta0) vs release angle.
    Highlights the optimal release angle and the current release angle.
    
    Parameters:
        theta_values (array): Array of angles in degrees.
        error_values (array): Array of error margins in degrees.
        best_theta (float): Optimal release angle in degrees.
        chosen_theta (float): Selected release angle in degrees.
        h (float): Hoop height minus release height.
        
    Returns:
        fig: Matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(8.5, 4))
    
    ax.plot(theta_values, error_values, color='purple', linewidth=2.5, label=r'Error Margin $e(\theta_0)$')
    
    # Fill the "forgiving zone" where error > 0
    ax.fill_between(theta_values, error_values, where=(error_values > 0), color='#d4edda', alpha=0.5, label='Forgiving Zone')
    
    # Find error values for vertical lines
    best_idx = np.abs(theta_values - best_theta).argmin()
    best_error = error_values[best_idx]
    
    chosen_idx = np.abs(theta_values - chosen_theta).argmin()
    chosen_error = error_values[chosen_idx]
    
    # Plot vertical line at optimal angle
    ax.axvline(best_theta, color=COLOR_OPTIMAL, linestyle='--', linewidth=2, 
               label=f'Optimal Angle: {best_theta:.1f}° (Error: ±{best_error:.2f}°)')
    ax.plot(best_theta, best_error, 'o', color=COLOR_OPTIMAL, markersize=8)
    
    # Plot vertical line at current angle
    ax.axvline(chosen_theta, color=COLOR_CHOSEN, linestyle=':', linewidth=2, 
               label=f'Selected Angle: {chosen_theta:.1f}° (Error: ±{chosen_error:.2f}°)')
    ax.plot(chosen_theta, chosen_error, 's', color=COLOR_CHOSEN, markersize=7)
    
    ax.set_xlabel('Release Angle (degrees)', fontsize=10)
    ax.set_ylabel('Allowed Angle Error (degrees)', fontsize=10)
    ax.set_title('Error Margin vs. Release Angle (Sweet Spot Analysis)', fontsize=11, fontweight='bold')
    
    ax.set_xlim(38.0, 77.0)
    ax.set_ylim(-0.2, max(error_values) + 0.5 if len(error_values) > 0 else 5.0)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right', fontsize=8)
    
    return fig


def plot_feasible_region(h, chosen_theta, chosen_v0, best_theta, best_v0):
    """
    Plots a 2D map of release angle vs. velocity, coloring the success (made) zone.
    Overlays the center-shot velocity line.
    
    Parameters:
        h (float): Hoop height minus release height.
        chosen_theta (float): Selected release angle in degrees.
        chosen_v0 (float): Selected velocity in m/s.
        best_theta (float): Optimal release angle in degrees.
        best_v0 (float): Velocity in m/s at the optimal release angle.
        
    Returns:
        fig: Matplotlib figure object.
    """
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    
    # Generate meshgrid of angles and velocities
    angles = np.arange(35.0, 75.1, 0.5)
    velocities = np.arange(5.5, 10.0, 0.05)
    
    # Prepare matrix to store results
    # 0 = Miss, 1 = Made
    success_matrix = np.zeros((len(velocities), len(angles)))
    
    for i, v in enumerate(velocities):
        for j, theta in enumerate(angles):
            shot = bm.check_shot(theta, v, h)
            if shot['result'] == 'made':
                success_matrix[i, j] = 1.0
                
    # Plot the success region
    extent = [angles[0], angles[-1], velocities[0], velocities[-1]]
    ax.imshow(success_matrix, extent=extent, origin='lower', aspect='auto', cmap='Greens', alpha=0.45)
    
    # Plot the center-hoop required velocity curve
    center_angles = np.arange(40.0, 75.1, 0.2)
    center_velocities = []
    valid_center_angles = []
    
    for theta in center_angles:
        v = bm.required_v0(theta, h)
        if v is not None and velocities[0] <= v <= velocities[-1]:
            center_velocities.append(v)
            valid_center_angles.append(theta)
            
    ax.plot(valid_center_angles, center_velocities, color='darkgreen', linestyle='-', linewidth=2, 
            label='Center-Hoop Shot Line')
            
    # Mark the user's selected shot
    chosen_shot = bm.check_shot(chosen_theta, chosen_v0, h)
    chosen_marker_color = COLOR_MADE if chosen_shot['result'] == 'made' else COLOR_MISS
    ax.plot(chosen_theta, chosen_v0, '*', color=chosen_marker_color, markersize=12, markeredgecolor='black', 
            label=f"Selected Shot ({chosen_theta:.1f}°, {chosen_v0:.2f} m/s)")
            
    # Mark the optimal shot
    ax.plot(best_theta, best_v0, 'o', color=COLOR_OPTIMAL, markersize=8, markeredgecolor='black',
            label=f"Optimal Shot ({best_theta:.1f}°, {best_v0:.2f} m/s)")
            
    # Labels and legend
    ax.set_xlabel('Release Angle (degrees)', fontsize=10)
    ax.set_ylabel('Release Velocity (m/s)', fontsize=10)
    ax.set_title('Feasible Region (Green Zone = Success)', fontsize=11, fontweight='bold')
    
    ax.set_xlim(35.0, 75.0)
    ax.set_ylim(5.5, 10.0)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='upper right', fontsize=8)
    
    return fig
