import random
import math
from config import *


def update(sc):
    """Advance one simulation step with realistic power and thermal physics."""

    sc.total_steps += 1
    if sc.mode == "NOMINAL":
        sc.uptime_steps += 1

    # ── Orbit advancement ────────────────────
    transition = sc.update_orbit()

    # ── Power Model ──────────────────────────
    drain = IDLE_DRAIN_RATE
    if sc.payload_on:
        drain += PAYLOAD_DRAIN_RATE * sc.payload_duty_cycle

    if sc.heater_on:
        drain += 0.3

    solar = 0.0
    if sc.in_sunlight and sc.solar_array_active:
        solar = SOLAR_CHARGE_RATE
        # Reduced charging near terminator (orbit transitions)
        if transition:
            solar *= 0.5

    net = solar - drain
    sc.battery = max(BATTERY_MIN, min(BATTERY_MAX, sc.battery + net))

    sc.power_draw_w = drain * (BATTERY_CAPACITY_WH / 100) * 60

    # ── Thermal Model ────────────────────────
    if sc.in_sunlight:
        sc.temperature += TEMP_SUNLIGHT_GAIN
        if sc.payload_on:
            sc.temperature += TEMP_PAYLOAD_GAIN * sc.payload_duty_cycle
    else:
        sc.temperature -= TEMP_SHADOW_LOSS
        # Deep eclipse: additional cooling
        if sc.eclipse_duration > 6:
            sc.temperature -= 0.5

    if sc.heater_on:
        sc.temperature += 1.2

    # Small random thermal noise ±0.2 °C
    sc.temperature += random.uniform(-0.2, 0.2)
    sc.temperature = max(TEMP_MIN, min(TEMP_MAX, sc.temperature))

    # ── ADCS Drift ───────────────────────────
    # Pointing degrades slightly each step; eclipse can cause drift
    drift = random.uniform(-0.02, 0.05)
    if not sc.in_sunlight:
        drift += 0.03
    sc.pointing_error_deg = max(0.0, min(5.0, sc.pointing_error_deg + drift))
    sc.attitude_stable = sc.pointing_error_deg < 1.0

    # ── Comms Quality ────────────────────────
    if sc.in_ground_contact:
        base_lq = 95.0 - (sc.pointing_error_deg * 5)
        sc.link_quality = max(20.0, min(100.0,
            base_lq + random.uniform(-2, 2)))
        if sc.mode != "NOMINAL":
            sc.link_quality *= 0.85
        if sc.link_quality > 60:
            sc.downlink_packets += random.randint(0, 4)
            sc.uplink_packets   += random.randint(0, 2)
    else:
        sc.link_quality = max(0.0, sc.link_quality - 5)

    sc.update_history()