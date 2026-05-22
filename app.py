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


# ---------------------------------------------------------------------------
# Cached computation helpers
# st.cache_data memoises results keyed by arguments, so heavy grid searches
# only re-run when the shooter height (h) or angle actually changes.
# ---------------------------------------------------------------------------

@st.cache_data
def cached_find_optimal_angle(h):
    """Grid-search for the angle that maximises the error margin."""
    return opt.find_optimal_angle(h)


@st.cache_data
def cached_error_curve(h):
    """Compute error margin for every angle in the display range."""
    angles = np.arange(40.0, 75.1, 0.2)
    errors = np.array([opt.compute_error_margin(a, h) for a in angles])
    return angles, errors


@st.cache_data
def cached_feasible_grid(h):
    """Evaluate the 2-D success grid (angle x velocity) once per height."""
    angles = np.arange(35.0, 75.1, 0.5)
    velocities = np.arange(5.5, 10.0, 0.05)
    grid = np.zeros((len(velocities), len(angles)))
    for i, v in enumerate(velocities):
        for j, theta in enumerate(angles):
            if bm.check_shot(theta, v, h)['result'] == 'made':
                grid[i, j] = 1.0
    return angles, velocities, grid


@st.cache_data
def cached_heights_table():
    """Build the comparison table across all standard player heights."""
    return opt.get_optimal_heights_table()

# Set page configuration
st.set_page_config(
    page_title="Basketball Free Throw Simulator",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state defaults
if "chosen_theta" not in st.session_state:
    st.session_state["chosen_theta"] = 52.0
if "apply_optimal" not in st.session_state:
    st.session_state["apply_optimal"] = False

# Custom CSS for modern styling and matching orange theme
st.markdown("""
<style>
    :root {
        --bg-light: #f8f9fa;
        --bg-dark: #212529;
        --sidebar-light: #f1f3f5;
        --sidebar-dark: #2c2f33;
        --text-light: #212529;
        --text-dark: #f8f9fa;
    }
    .main {
        background-color: var(--bg-light);
        color: var(--text-light);
    }
    .stApp {
    font-family: 'Outfit', 'Inter', sans-serif;
    color: var(--text-light);
    background-color: var(--bg-light);
}
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
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-light);
        border-right: 1px solid #dee2e6;
    }
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
    .highlight {
        color: #d9531e;
        font-weight: 700;
    }
    body {
        background-color: var(--bg-light);
        color: var(--text-light);
    }
    .stTabs {
        background-color: var(--bg-light);
    }
    @media (prefers-color-scheme: dark) {
        body {
            background-color: var(--bg-dark);
            color: var(--text-dark);
        }
        .stTabs {
            background-color: var(--bg-dark);
        }
        .stTabs > div {
            background-color: var(--bg-dark);
            color: var(--text-dark);
        }
        .main {
            background-color: var(--bg-dark);
            color: var(--text-dark);
        }
        .stApp {
            color: var(--text-dark);
            background-color: var(--bg-dark);
        }
        h1, h2, h3 {
            color: var(--text-dark) !important;
        }
        section[data-testid="stSidebar"] {
            background-color: var(--sidebar-dark);
        }
        .success-box {
            background-color: #155724;
            border-left: 5px solid #28a745;
            color: #d4edda;
        }
        .fail-box {
            background-color: #721c24;
            border-left: 5px solid #dc3545;
            color: #f8d7da;
        }
        .stTabs {
            background-color: var(--bg-dark);
        }
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

# If the 'Apply Optimal' button was clicked last run, update the angle
# BEFORE the slider is instantiated — this is the only safe moment to do so.
if st.session_state["apply_optimal"]:
    st.session_state["chosen_theta"] = st.session_state.pop("_pending_theta")
    st.session_state["apply_optimal"] = False

# Release angle slider (bound to session state key)
chosen_theta = st.sidebar.slider(
    "Release Angle (θ₀)",
    min_value=30.0,
    max_value=80.0,
    step=0.5,
    key="chosen_theta",
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

# Calculate optimal parameters (cached per shooter height)
best_theta, best_error, best_v0, t_low, t_high = cached_find_optimal_angle(h)

# Quick Sidebar Action
st.sidebar.markdown("---")
if st.sidebar.button("🎯 Apply Optimal Angle & Speed"):
    # Store the desired value in a staging key and set the flag.
    # The actual session state update happens BEFORE the slider renders
    # on the next rerun, avoiding the post-instantiation write error.
    st.session_state["_pending_theta"] = best_theta
    st.session_state["apply_optimal"] = True
    st.rerun()


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

    with st.spinner("Simulating trajectory..."):
        fig_traj = viz.plot_trajectory(
            chosen_theta, chosen_v0, h, result, min_d, r_edge, shooter_height_m
        )
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
                  delta=f"{(min_d - bm.Db/2):.3f} m margin",
                  delta_color="normal" if min_d > bm.Db/2 else "inverse")

with tab2:
    st.subheader("Release Angle Error Margin")
    st.markdown(
        "For a given height, each release angle has a corresponding speed that makes a perfect center shot. "
        "However, human players aren't perfect. This plot shows how much **release angle error (\u00b1 degrees)** "
        "the shooter is allowed before missing the shot. The peak represents the most forgiving release angle."
    )

    with st.spinner("Computing error margin curve..."):
        angles_arr, errors_arr = cached_error_curve(h)
        fig_error = viz.plot_error_function(
            angles_arr, errors_arr, best_theta, chosen_theta, h
        )
    st.pyplot(fig_error)

    # Show optimization statistics
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    chosen_margin = opt.compute_error_margin(chosen_theta, h)
    with col_opt1:
        st.markdown(
            f"""
            ### \U0001f31f Optimal Release Angle
            * Best Release Angle: <span class="highlight">{best_theta:.1f}\u00b0</span>
            * Allowed Error Margin: <span class="highlight">\u00b1{best_error:.2f}\u00b0</span>
            * Success Range: **{t_low:.1f}\u00b0 to {t_high:.1f}\u00b0**
            """,
            unsafe_allow_html=True
        )
    with col_opt2:
        if chosen_margin > 0:
            margin_str = f"\u00b1{chosen_margin:.2f}\u00b0"
        else:
            margin_str = "0.0\u00b0 (Misses at this angle)"
        st.markdown(
            f"""
            ### \U0001f4d0 Your Selected Angle
            * Selected Angle: <span class="highlight">{chosen_theta:.1f}\u00b0</span>
            * Allowed Error Margin: <span class="highlight">{margin_str}</span>
            """,
            unsafe_allow_html=True
        )
    with col_opt3:
        st.markdown(
            """
            ### \U0001f4a1 Physics Insight
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

    with st.spinner(
        "Building feasible region map \u2014 evaluating every angle \u00d7 velocity combination..."
    ):
        grid_angles, grid_velocities, success_grid = cached_feasible_grid(h)
        fig_feasible = viz.plot_feasible_region(
            h, chosen_theta, chosen_v0, best_theta, best_v0,
            grid_angles, grid_velocities, success_grid
        )
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

    with st.spinner("Calculating optimal parameters for all heights..."):
        table_raw = cached_heights_table()

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
