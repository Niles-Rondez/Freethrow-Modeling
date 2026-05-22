# Basketball Free Throw Simulator 🏀

**Live Demo:** [freethrow-model.streamlit.app](https://freethrow-model.streamlit.app)

This application is an educational mathematical modeling tool designed to simulate the flight path of a basketball free throw, analyze rim-clearance criteria, and optimize release conditions (angle and velocity) for players of different heights.

## Features

- **Trajectory Visualizer:** Simulates and plots the flight path of a basketball relative to the court floor. Detects if a shot is successful or misses (clipping the front/back rim, landing short, or failing to reach the hoop height).
- **Sweet Spot Analysis (Error Margin):** Evaluates the allowed angle error margin (in $\pm$ degrees) for different release angles. Displays the sweet spot where the shooter has the largest margin for error.
- **Feasible Region Heatmap:** Generates a 2D success map mapping release angle vs. release velocity, showing the green success zone and how the optimal center shot lies within it.
- **Height Comparison Table:** Compares optimal release angles, required velocities, and error margins for shooter heights ranging from 5'0" to 7'3".

---

## Installation & Setup

1. **Clone or Navigate to the Directory:**
   Make sure you are in the project folder where the source files are located.

2. **Install Dependencies:**
   Install the required Python libraries using the package manager `pip`:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `streamlit`, `numpy`, `matplotlib`, and `pytest` (for running tests).*

---

## How to Run

### 1. Launch the Streamlit Web Application
Run the following command to start the interactive web interface:
```bash
streamlit run app.py
```
This will start a local web server (usually at `http://localhost:8501`) and automatically open the application in your default web browser.

### 2. Run the Unit Tests
To verify the math and search algorithms, run the test suite using `pytest`:
```bash
pytest test_basketball.py
```

---

## File Structure

- `basketball_model.py`: Pure mathematics and physics calculations. Implements equations of motion, flight time solvers, required velocity formulas, and rim checks.
- `optimizer.py`: Handles optimization routines. Implements binary search for success boundaries, error margin calculations, and grid search to locate the optimal angle.
- `visualization.py`: Contains all the Matplotlib rendering functions for the trajectory, error margin curve, and feasible region heatmap.
- `app.py`: The Streamlit frontend that builds the interactive UI dashboard.
- `requirements.txt`: Project dependencies list.
- `test_basketball.py`: Automated unit tests verifying the correctness of the physical formulas and optimizer bounds.
- `blueprint.md`: The original design specification blueprint.
