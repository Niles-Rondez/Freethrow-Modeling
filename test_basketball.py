"""
test_basketball.py

Unit tests for the Basketball Free Throw Simulator.
Verifies calculations in basketball_model.py and optimizer.py.
"""

import pytest
import numpy as np
import basketball_model as bm
import optimizer as opt

def test_get_h():
    # Test for 6'0" shooter (1.8288 m)
    # release height = 1.8288 * 1.25 = 2.286
    # h = 3.048 - 2.286 = 0.762
    h = bm.get_h(1.8288)
    assert pytest.approx(h, abs=1e-4) == 0.762

    # Test for 5'0" shooter (1.524 m)
    # release height = 1.524 * 1.25 = 1.905
    # h = 3.048 - 1.905 = 1.143
    h2 = bm.get_h(1.524)
    assert pytest.approx(h2, abs=1e-4) == 1.143


def test_required_v0():
    h = bm.get_h(1.8288)  # 0.762 m
    
    # 52 degrees center shot velocity should be ~6.9708 m/s
    v0 = bm.required_v0(52.0, h)
    assert v0 is not None
    assert pytest.approx(v0, abs=1e-2) == 6.97
    
    # Flat angle (e.g. 10 degrees) where denom <= 0
    # l * tan(10) - h = 4.115 * 0.1763 - 0.762 = 0.7255 - 0.762 = -0.0365 <= 0
    v0_flat = bm.required_v0(10.0, h)
    assert v0_flat is None


def test_trajectory():
    h = bm.get_h(1.8288)
    v0 = bm.required_v0(52.0, h)
    
    ts, x, y = bm.get_trajectory(52.0, v0, h)
    assert ts is not None
    assert len(ts) == 500
    assert x[0] == 0.0
    assert y[0] == 0.0
    
    # The final point in x should be l (horizontal target)
    assert pytest.approx(x[-1], abs=1e-4) == bm.l
    # The final point in y should be h (relative height target)
    assert pytest.approx(y[-1], abs=1e-4) == h


def test_check_shot():
    h = bm.get_h(1.8288)
    
    # Center shot at 52 degrees should be "made"
    v0_center = bm.required_v0(52.0, h)
    shot_center = bm.check_shot(52.0, v0_center, h)
    assert shot_center['result'] == 'made'
    
    # Check that a shot that lands short of the front rim is classified correctly
    # Release velocity too low (say 5.0 m/s at 52 deg)
    shot_short = bm.check_shot(52.0, 5.0, h)
    assert shot_short['result'] in ['undershoot_front_rim', 'miss_low']
    
    # Flat release angle (45 degrees) center shot should clip front rim
    v0_flat = bm.required_v0(45.0, h)
    shot_flat = bm.check_shot(45.0, v0_flat, h)
    assert shot_flat['result'] == 'hit_front_rim'


def test_optimizer_bounds():
    h = bm.get_h(1.8288)
    theta0 = 52.0
    v0 = bm.required_v0(theta0, h)
    
    # Made range for theta0 = 52 deg is approx [47.6, 54.6]
    t_low = opt.find_theta_low(theta0, v0, h)
    t_high = opt.find_theta_high(theta0, v0, h)
    
    assert t_low < theta0
    assert t_high > theta0
    assert pytest.approx(t_low, abs=0.2) == 47.6
    assert pytest.approx(t_high, abs=0.2) == 54.6


def test_optimal_angle():
    h = bm.get_h(1.8288)
    best_theta, best_error, v0, t_low, t_high = opt.find_optimal_angle(h)
    
    # Optimal angle should be around 51.1 degrees
    assert pytest.approx(best_theta, abs=0.5) == 51.1
    # Error margin should be positive
    assert best_error > 0.0
    # Success range should contain optimal angle
    assert t_low <= best_theta <= t_high


def test_heights_table():
    table = opt.get_optimal_heights_table()
    assert len(table) == 10
    
    # Verify values for 6'0" player (index 4 in list)
    row_6ft = table[4]
    assert row_6ft['height_str'] == "6'0\""
    assert pytest.approx(row_6ft['opt_angle'], abs=0.5) == 51.1
