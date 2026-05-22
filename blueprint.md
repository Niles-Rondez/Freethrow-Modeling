# Basketball Free Throw Simulator — Implementation Blueprint

---

## Overview

**What it does:** Simulates the trajectory of a basketball free throw and finds the optimal release angle and velocity for a shooter of a given height.

**Real-world purpose:** Helps understand why some players miss free throws and what release angle/velocity they should target to maximize their margin for error.

**Core modelling idea:** Model the ball as a projectile (ignoring air resistance for simplicity). Given a shooter's height, compute which (angle, velocity) combinations result in a successful basket, then find the pair that maximizes the allowed error in both angle and velocity — the most forgiving shot.

---

## Mathematical Model

### Coordinate System
- Origin: ball release point
- x: horizontal (toward basket)
- y: vertical (upward)

### Equations of Motion (no air resistance)

**Horizontal:**
```
x(t) = v0 * cos(θ0) * t
```

**Vertical:**
```
y(t) = v0 * sin(θ0) * t + 0.5 * g * t²
```

### Required Initial Velocity for a Center-Hoop Shot
To send the ball through the center of the hoop at horizontal distance `l` and height `h`:
```
v0 = (l / cos(θ0)) * sqrt(-g / (2 * (l * tan(θ0) - h)))
```
Valid only when `l * tan(θ0) - h > 0`, i.e., `θ0 > arctan(h / l)`.

### Landing Position with Angle Error
When the player mis-releases at angle `θ_oops` (keeping `v0` fixed):
```
x_land = (v0 * cos(θ_oops) / (-g)) * (v0 * sin(θ_oops) + sqrt(v0² * sin²(θ_oops) + 2*g*h))
```

### Ball-Goes-In Criteria
1. **Clears front rim** — the distance from the ball center to the front rim coordinates `(l - Dr/2, h)` must exceed ball radius `Db/2` throughout the trajectory:
   ```
   s² = (x(t) - (l - Dr/2))² + (y(t) - h)² > (Db/2)²
   ```
2. **Doesn't overshoot back rim** — when ball reaches basket height, the ball's right edge must not pass the back rim:
   ```
   x_land + Db/2 <= l + Dr/2
   ```

### Error Function
For each candidate angle `θ0`, compute:
- `θ_low`: lowest angle that still clears the front rim
- `θ_high`: highest angle that still hits at or before the back rim

```
e(θ0) = min(θ_high - θ0, θ0 - θ_low)
```

The **best release angle** maximizes `e(θ0)`.

---

## Variable & Constant Definitions

| Symbol | Description | Value / Source |
|--------|-------------|----------------|
| `l` | Horizontal distance from release to hoop center | 13 ft 6.5 in = 4.115 m |
| `h` | Net vertical rise from release to hoop center | depends on shooter height |
| `Dr` | Rim diameter | 1.5 ft = 0.457 m |
| `Db` | Ball diameter | 0.8 ft = 0.244 m |
| `g` | Gravitational acceleration | -9.8 m/s² |
| `θ0` | Release angle (degrees from horizontal) | user input / optimized |
| `v0` | Release speed (m/s) | computed or user input |
| `shooter_height` | Shooter's height | user input |
| `release_height` | Ball release height = 1.25 × shooter height | derived |
| `hoop_height` | Standard hoop height | 3.05 m (10 ft) |
| `h` | `hoop_height - release_height` | derived (can be negative for tall players) |

---

## Program Inputs

All adjustable by the user:

- **Shooter height** (feet/inches or cm) — determines release height and thus `h`
- **Release angle** (degrees) — for single-shot trajectory visualization
- **Release velocity** (m/s) — for single-shot visualization (or auto-compute for center shot)
- **Mode toggle**: "Visualize single shot" vs "Find optimal angle"

Optional advanced inputs:
- Custom `l` (horizontal distance) if the user shoots from a different spot
- Ball diameter `Db` (if non-standard)

---

## Program Outputs

### Single Shot Mode
- Animated or static trajectory arc plot (x vs y)
- Whether the shot goes in (pass/fail with reason: front rim, back rim, missed entirely)
- Exact landing position relative to hoop

### Optimal Angle Mode
- Plot of error function `e(θ0)` vs angle — shows the sweet spot
- Best release angle `θ*` (in degrees)
- Required release velocity `v0*` (m/s) for that angle
- Allowed angle error range `[θ_low, θ_high]`
- Table of optimal angles for heights from 5'0" to 7'3"

### Feasible Region Plot (stretch goal)
- 2D contour plot of angle vs velocity showing which combinations result in a made basket

---

## Simulation Logic

### Step 1 — Setup constants
```
g = -9.8
Dr = 0.457  # meters
Db = 0.244
l = 4.115
hoop_height = 3.048
```

### Step 2 — Compute geometry from shooter height
```
release_height = shooter_height * 1.25
h = hoop_height - release_height
```

### Step 3 — Single trajectory
Given `θ0` and `v0`:
- Compute time steps `t` from 0 to time of descent to basket height
- Compute `x(t)` and `y(t)` arrays
- Check front rim clearance at each time step near the rim
- Check back rim constraint at landing
- Plot the arc

### Step 4 — Compute required velocity for center shot
Given `θ0`, use:
```python
v0 = (l / cos(θ0)) * sqrt(-g / (2 * (l * tan(θ0) - h)))
```
Skip angles where `l * tan(θ0) - h <= 0`.

### Step 5 — Compute allowed angle error for each θ0
For each `θ0` in range (e.g., 40° to 75° in 0.1° steps):
1. Compute `v0` for a center shot at that angle
2. Binary search for `θ_low` (below θ0) where ball just grazes front rim
3. Binary search for `θ_high` (above θ0) where ball just hits back rim (or grazes front rim if back rim isn't reachable first)
4. `e(θ0) = min(θ0 - θ_low, θ_high - θ0)`

### Step 6 — Find optimal angle
```python
best_theta = θ0_values[argmax(e_values)]
```

### Step 7 — Output table for all heights
Loop over heights from 1.52 m to 2.21 m, repeat steps 2–6 for each.

---

## Recommended Simplifications

For a manageable school project, drop or simplify these:

| Paper Feature | Simplification |
|---|---|
| Multiobjective optimization (angle + velocity) | Just maximize angle error `e(θ0)` — the first model |
| Air resistance model (ODEs) | Skip entirely; paper shows it barely changes results |
| Weighted percent-error optimization | Optional stretch feature |
| Back rim bounce trajectories | Ignore; only "nearly nothing but net" shots |
| 3D sideways error | Keep 2D only |
| Transverse spin | Ignore |

**Keep:** trajectory equations, front/back rim criteria, error function, optimal angle plot, height-based table.

---

## Suggested Features

**Beginner:**
- Input height → get optimal release angle and velocity
- Single trajectory plot with pass/fail result
- Error function plot `e(θ0)` for chosen height

**Intermediate:**
- Side-by-side trajectory comparison (ideal vs user-specified angle)
- Table of optimal angles for common heights
- Highlight the "forgiving zone" on the angle plot

**Stretch:**
- Feasible region heatmap (angle × velocity grid, colored by in/out)
- Animated ball flight

---

## Python Implementation Notes

### Libraries
```
numpy        # array math, trig, root-finding
matplotlib   # trajectory and error function plots
scipy.optimize  # brentq() for binary search on θ_low, θ_high
streamlit    # UI (see below)
```

### Architecture
```
basketball_model.py      # pure math: equations, criteria checks, error function
optimizer.py             # finds θ_low, θ_high, best angle for a given height
visualization.py         # all matplotlib figures
app.py                   # Streamlit UI calling the above
```

### Key Implementation Notes

**Angle search (θ_low, θ_high):** Use `scipy.optimize.brentq` on the front-rim distance function and back-rim overshoot function. Search in intervals `[θ_min, θ0]` and `[θ0, θ_max]` respectively.

**Front rim check:** Evaluate `s²(t) - (Db/2)²` at many time points near the rim. The ball fails if this ever goes negative.

**Time array:** Use `np.linspace(0, T, 500)` where `T` is time to reach hoop height on descent.

**Degrees vs radians:** Keep user-facing values in degrees; convert to radians internally with `np.radians()`.

**Edge case:** For `θ0` below `arctan(h/l)`, the ball never reaches hoop height — skip these angles.

**Potential challenge:** The error function `e(θ0)` is non-smooth (has a kink at its maximum due to the `min()` function). Use `argmax` over a dense grid instead of calculus-based optimization.

---

## Frontend — Streamlit UI

```
app.py layout:

Sidebar:
  - Slider: Shooter height (ft or cm)
  - Slider: Release angle (30° – 75°)
  - Slider: Release velocity (optional override)
  - Button: "Use optimal velocity" (auto-compute v0 for center shot)
  - Button: "Find best angle"

Main area (tabs):
  Tab 1 — Trajectory
    - Plot: ball arc with hoop drawn, front/back rim marked
    - Text: "Shot result: MADE / MISSED (front rim / back rim)"

  Tab 2 — Error Analysis
    - Plot: e(θ0) vs angle with vertical line at chosen angle
    - Text: Best angle, allowed error range

  Tab 3 — Height Table
    - Table: Height | Best Angle | Release Velocity
    - Rows for 5'0" through 7'3"
```

### Hoop Drawing Helper
```python
# Draw hoop on trajectory plot
front_rim_x = l - Dr/2
back_rim_x  = l + Dr/2
rim_y       = h  # relative to release point
plt.hlines(rim_y, front_rim_x, back_rim_x, color='orange', linewidth=3)
```

---

## Quick-Start Formula Reference

```python
import numpy as np

g = -9.8
l = 4.115      # meters
Dr = 0.457
Db = 0.244
hoop_height = 3.048

def get_h(shooter_height_m):
    return hoop_height - shooter_height_m * 1.25

def required_v0(theta_deg, h):
    t = np.radians(theta_deg)
    denom = 2 * (l * np.tan(t) - h)
    if denom <= 0:
        return None
    return (l / np.cos(t)) * np.sqrt(-g / denom)

def trajectory(theta_deg, v0, n=500):
    t = np.radians(theta_deg)
    T = (-v0*np.sin(t) - np.sqrt((v0*np.sin(t))**2 + 2*g*h)) / g
    ts = np.linspace(0, T, n)
    x = v0 * np.cos(t) * ts
    y = v0 * np.sin(t) * ts + 0.5 * g * ts**2
    return x, y
```
