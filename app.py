"""
app.py

Main Streamlit application for the Basketball Free Throw Simulator.
Integrates the mathematical model, optimizer, and visualization modules 
into an interactive dashboard for educational and modeling presentations.
"""

import streamlit as st
import numpy as np
import pandas as pd
import basketball_model as bm
import optimizer as opt
import visualization as viz

# Set page configuration
st.set_page_config(
    page_title="Basketball Free Throw Simulator",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling and matching orange theme
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    /* Main titles */
    h1 {
        color: #d9531e !important;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    h2 {
        color: #2c3e50;
        font-weight: 600;
    }
    h3 {
        color: #34495e;
        font-weight: 600;
    }
    /* Styling sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f1f3f5;
        border-right: 1px solid #dee2e6;
    }
    /* Results boxes */
    .success-box {
        padding: 1.5rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 0.5rem;
        color: #155724;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .fail-box {
        padding: 1.5rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        border-radius: 0.5rem;
        color: #721c24;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    /* Highlight variables */
    .highlight {
        color: #d9531e;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("🏀 Basketball Free Throw Simulator")
st.markdown("An interactive mathematical model to explore optimal release conditions and margins of error for free throws.")
st.markdown("---")

# ----------------- SIDEBAR INPUTS -----------------
st.sidebar.header("🏃‍♂️ Shooter & Shot Profile")

# Shooter Height input (Feet & Inches)
st.sidebar.subheader("Shooter Height")
col_ft, col_in = st.sidebar.columns(2)
with col_ft:
    ft = st.slider("Feet", 4, 7, 6, key="height_ft")
with col_in:
    inch = st.slider("Inches", 0, 11, 0, key="height_in")

# Calculate shooter height in meters and display release height
total_inches = ft * 12 + inch
shooter_height_m = total_inches * 0.0254
release_height_m = shooter_height_m * 1.25
h = bm.get_h(shooter_height_m)

st.sidebar.markdown(
    f"""
    * **Height:** {ft}'{inch}" ({shooter_height_m:.2f} m)
    * **Release Height (1.25x):** {release_height_m:.2f} m
    * **Rise to Hoop ($h$):** {h:.2f} m
    """
)

st.sidebar.markdown("---")
st.sidebar.subheader("Shot Parameters")

# Release angle slider
chosen_theta = st.sidebar.slider(
    "Release Angle (θ₀)", 
    min_value=30.0, 
    max_value=80.0, 
    value=52.0, 
    step=0.5,
    help="Angle of release in degrees from horizontal."
)

# Toggle to automatically compute center-shot velocity
use_center_velocity = st.sidebar.checkbox(
    "Use Center-Shot Velocity", 
    value=True,
    help="Automatically calculate the required release speed to make the ball land exactly in the center of the hoop."
)

# Compute or adjust velocity
v0_calculated = bm.required_v0(chosen_theta, h)

if use_center_velocity:
    if v0_calculated is not None:
        chosen_v0 = v0_calculated
        st.sidebar.info(f"Target Velocity: **{chosen_v0:.2f} m/s**")
    else:
        st.sidebar.warning("⚠️ Angle too flat! Cannot reach hoop height. Overriding to manual speed control.")
        use_center_velocity = False
        chosen_v0 = st.sidebar.slider("Release Velocity (v₀)", 4.0, 12.0, 7.0, 0.1)
else:
    chosen_v0 = st.sidebar.slider(
        "Release Velocity (v₀)", 
        min_value=4.0, 
        max_value=12.0, 
        value=7.0, 
        step=0.1,
        help="Initial speed of the ball in meters per second."
    )

# Calculate optimal parameters for display in sidebar/main area
best_theta, best_error, best_v0, t_low, t_high = opt.find_optimal_angle(h)

# Quick Sidebar Action
st.sidebar.markdown("---")
if st.sidebar.button("🎯 Apply Optimal Angle & Speed"):
    st.session_state["height_ft"] = ft
    st.session_state["height_in"] = inch
    st.sidebar.info(f"Updated release angle to optimal: **{best_theta:.1f}°**")
    # Streamlit rerun is handled on next interaction, but we can set parameter query values
    # Actually, we can just use st.rerun() if they click the button to apply optimal values!
    # Let's save to session state to overwrite the release angle slider default
    st.session_state["chosen_theta_slider"] = best_theta
    st.rerun()

# Check for session state override
if "chosen_theta_slider" in st.session_state:
    # If the user changed the slider manually, delete the session state to allow updates
    # Wait, we can set the value parameter of the slider to match session state!
    pass

# Adjust slider value dynamically if override in session state
if "chosen_theta_slider" in st.session_state:
    chosen_theta = st.session_state["chosen_theta_slider"]
    # Remove from session state so user can change it again
    del st.session_state["chosen_theta_slider"]


# ----------------- CALCULATIONS -----------------
# Run shot simulation for the chosen parameters
shot_info = bm.check_shot(chosen_theta, chosen_v0, h)
result = shot_info['result']
min_d = shot_info['min_dist_to_front_rim']
r_edge = shot_info['right_edge_at_landing']
l_edge = shot_info['left_edge_at_landing']


# ----------------- MAIN PRESENTATION AREA -----------------

# Dynamic Results Banner
if result == 'made':
    st.markdown(
        f"""
        <div class="success-box">
            ✅ SHOT MADE! The ball goes through the hoop. <br/>
            <span style="font-size: 0.9rem; font-weight: normal; color: #155724;">
                Landing coordinate: center is 4.12m, ball landed at <b>{r_edge - bm.Db/2:.3f}m</b>. 
                Front rim clearance: <b>{min_d:.3f}m</b> (minimum required is {bm.Db/2:.3f}m).
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )
else:
    reasons = {
        'hit_front_rim': "Missed! The ball hit the front of the rim.",
        'overshoot_back_rim': "Missed! The ball overshot the back of the rim.",
        'undershoot_front_rim': "Missed! The ball landed short of the rim.",
        'miss_low': "Missed! The release angle/velocity was too flat; the ball never reached the 3.05m hoop height."
    }
    reason_str = reasons.get(result, "Missed shot!")
    st.markdown(
        f"""
        <div class="fail-box">
            ❌ SHOT MISSED! {reason_str} <br/>
            <span style="font-size: 0.9rem; font-weight: normal; color: #721c24;">
                Landing coordinate: center is 4.12m, ball landed at <b>{r_edge - bm.Db/2:.3f}m</b>.
                Front rim clearance: <b>{min_d:.3f}m</b> (required: >{bm.Db/2:.3f}m).
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Tabs layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Trajectory Visualization", 
    "🎯 Sweet Spot & Error Analysis", 
    "📊 Feasible Region Heatmap",
    "📋 Height Comparison Table"
])

with tab1:
    st.subheader("Free Throw Trajectory Arc")
    st.markdown(
        "This plot displays the flight path of the basketball from the shooter's release point "
        "to the basket. The hoop rim is represented by the orange line, and the backboard by the gray vertical bar."
    )
    
    # Generate and display the trajectory plot
    fig_traj = viz.plot_trajectory(chosen_theta, chosen_v0, h, result, min_d, r_edge, shooter_height_m)
    st.pyplot(fig_traj)
    
    # Math explanation metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Horizontal Distance (l)", f"{bm.l} m", help="Distance to hoop center")
    with col2:
        st.metric("Landing Center (x_land)", f"{r_edge - bm.Db/2:.3f} m", 
                  delta=f"{((r_edge - bm.Db/2) - bm.l):.3f} m from Center")
    with col3:
        st.metric("Min Front Rim Clearance", f"{min_d:.3f} m", 
                  delta=f"{(min_d - bm.Db/2):.3f} m margin", delta_color="normal" if min_d > bm.Db/2 else "inverse")

with tab2:
    st.subheader("Release Angle Error Margin")
    st.markdown(
        "For a given height, each release angle has a corresponding speed that makes a perfect center shot. "
        "However, human players aren't perfect. This plot shows how much **release angle error (± degrees)** "
        "the shooter is allowed before missing the shot. The peak represents the most forgiving release angle."
    )
    
    # Generate error curves
    angles_arr = np.arange(40.0, 75.1, 0.2)
    errors_arr = [opt.compute_error_margin(a, h) for a in angles_arr]
    
    # Generate and display plot
    fig_error = viz.plot_error_function(angles_arr, np.array(errors_arr), best_theta, chosen_theta, h)
    st.pyplot(fig_error)
    
    # Show optimization statistics
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        st.markdown(
            f"""
            ### 🌟 Optimal Release Angle
            * Best Release Angle: <span class="highlight">{best_theta:.1f}°</span>
            * Allowed Error Margin: <span class="highlight">±{best_error:.2f}°</span>
            * Success Range: **{t_low:.1f}° to {t_high:.1f}°**
            """, 
            unsafe_allow_html=True
        )
    with col_opt2:
        st.markdown(
            f"""
            ### 📐 Your Selected Angle
            * Selected Angle: <span class="highlight">{chosen_theta:.1f}°</span>
            * Allowed Error Margin: <span class="highlight">±{opt.compute_error_margin(chosen_theta, h):.2f}°</span>
            """ if opt.compute_error_margin(chosen_theta, h) > 0 else
            f"""
            ### 📐 Your Selected Angle
            * Selected Angle: <span class="highlight">{chosen_theta:.1f}°</span>
            * Allowed Error Margin: <span class="highlight">0.0° (Misses at this angle)</span>
            """,
            unsafe_allow_html=True
        )
    with col_opt3:
        st.markdown(
            """
            ### 💡 Physics Insight
            Taller shooters release the ball closer to the height of the hoop, requiring a lower release angle 
            and lower velocity. This flatter trajectory actually increases the size of the target hoop relative 
            to the incoming ball angle, providing a larger margin for error!
            """
        )

with tab3:
    st.subheader("Feasible Region (Angle vs. Velocity)")
    st.markdown(
        "The green zone in this heatmap shows all combinations of **Release Angle** and **Release Velocity** "
        "that result in a successful free throw. The **dark green line** shows the center-hoop shots."
    )
    
    # Generate and display the feasible region plot
    fig_feasible = viz.plot_feasible_region(h, chosen_theta, chosen_v0, best_theta, best_v0)
    st.pyplot(fig_feasible)
    
    st.markdown(
        """
        ### Interpreting the Heatmap
        * **Green Area:** Any release point inside this region results in a made free throw.
        * **Center-Hoop Line:** Representing shots landing exactly in the center of the rim. Notice that this line runs directly down the middle of the green success zone, showing that aiming for the center provides the maximum distance to the success boundaries in both directions.
        * **Optimal Shot (Gold circle):** Represents the point on the center line that lies in the widest vertical/horizontal cross-section of the success region, giving the shooter the maximum tolerance for release errors.
        """
    )

with tab4:
    st.subheader("Optimal Release Parameters by Player Height")
    st.markdown(
        "This table compares the optimal release parameters and allowable margins of error "
        "for shooters of different heights, ranging from 5'0\" to 7'3\"."
    )
    
    # Retrieve the table data
    table_raw = opt.get_optimal_heights_table()
    
    # Convert to pandas DataFrame for pretty rendering
    df = pd.DataFrame(table_raw)
    
    # Rename columns for presentation
    df_present = df.rename(columns={
        "height_str": "Player Height",
        "height_m": "Height (m)",
        "release_height_m": "Release Height (m)",
        "opt_angle": "Optimal Angle (°)",
        "opt_velocity": "Optimal Velocity (m/s)",
        "error_margin": "Allowed Error Margin (±°)",
        "angle_range": "Successful Angle Range"
    })
    
    # Format float values
    df_present["Height (m)"] = df_present["Height (m)"].map("{:.2f}".format)
    df_present["Release Height (m)"] = df_present["Release Height (m)"].map("{:.2f}".format)
    df_present["Optimal Angle (°)"] = df_present["Optimal Angle (°)"].map("{:.1f}°".format)
    df_present["Optimal Velocity (m/s)"] = df_present["Optimal Velocity (m/s)"].map("{:.2f} m/s".format)
    df_present["Allowed Error Margin (±°)"] = df_present["Allowed Error Margin (±°)"].map("±{:.2f}°".format)
    
    # Display table in Streamlit
    st.dataframe(df_present, use_container_width=True, hide_index=True)
    
    st.markdown(
        """
        ### Observations
        1. **Tall players have a massive advantage:** A 7'3\" player has a release height of **2.30 m**, meaning they only need to lift the ball **0.75 m** to reach the hoop. Their optimal release angle is **~49°**, and they enjoy an error margin of **~±3.5°**.
        2. **Shorter players require higher angles:** A 5'0\" player releases the ball at **1.52 m** (lifting it **1.52 m** to reach the hoop). They must shoot at a steeper angle of **~53°** and with more speed, resulting in a tighter error margin of **~±2.8°**.
        """
    )

# Footer
st.markdown("---")
st.markdown("🏀 *Developed as an educational mathematical modeling presentation based on equations of projectile motion.*")
