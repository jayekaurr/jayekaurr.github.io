import math
import random
from config import *


class Spacecraft:
    def __init__(self):
        self.name = SATELLITE_NAME
        self.mission_id = MISSION_ID

        # ── Mode ─────────────────────────────
        self.mode = "NOMINAL"          # NOMINAL | SAFE | EMERGENCY | COMMISSIONING

        # ── Power Subsystem ──────────────────
        self.battery = 85.0
        self.solar_array_active = True
        self.power_draw_w = 0.0

        # ── Thermal Subsystem ────────────────
        self.temperature = 22.0
        self.heater_on = False

        # ── Payload ──────────────────────────
        self.payload_on = True
        self.payload_duty_cycle = 1.0   # 0.0 – 1.0

        # ── ADCS ─────────────────────────────
        self.attitude_stable = True
        self.pointing_error_deg = 0.3

        # ── Communications ───────────────────
        self.in_ground_contact = True
        self.comms_available = True
        self.link_quality = 92.0        # %
        self.uplink_packets = 0
        self.downlink_packets = 0

        # ── Orbit ────────────────────────────
        self.orbit_step = 0
        self.in_sunlight = True
        self.eclipse_duration = 0       # consecutive eclipse steps
        self.orbit_number = 1

        # ── Fault Management ─────────────────
        self.active_faults = set()
        self.fault_history = []
        self.pre_fault_payload_state = None

        # ── Telemetry History ─────────────────
        self.history = {
            "battery":     [],
            "temperature": [],
            "link_quality": [],
            "pointing_error": []
        }

        # ── Statistics ───────────────────────
        self.total_steps = 0
        self.total_faults = 0
        self.uptime_steps = 0

    # ─────────────────────────────────────────
    def update_orbit(self):
        """Advance orbital position and update sunlight/eclipse state."""
        self.orbit_step = (self.orbit_step + 1) % ORBIT_PERIOD_STEPS
        phase = self.orbit_step / ORBIT_PERIOD_STEPS

        prev_sunlight = self.in_sunlight
        self.in_sunlight = phase < SUNLIGHT_FRACTION

        if not self.in_sunlight:
            self.eclipse_duration += 1
        else:
            self.eclipse_duration = 0

        if self.orbit_step == 0:
            self.orbit_number += 1

        # Ground contact: simplified – contacts during first 20% of orbit
        self.in_ground_contact = phase < 0.20 or (0.55 < phase < 0.65)

        return prev_sunlight != self.in_sunlight   # True if transition occurred

    def update_history(self):
        for key, val in [
            ("battery", self.battery),
            ("temperature", self.temperature),
            ("link_quality", self.link_quality),
            ("pointing_error", self.pointing_error_deg)
        ]:
            self.history[key].append(round(val, 2))
            self.history[key] = self.history[key][-60:]

    def execute(self, command):
        cmd_map = {
            "ENTER_SAFE_MODE": self._enter_safe_mode,
            "EXIT_SAFE_MODE":  self._exit_safe_mode,
            "ENTER_EMERGENCY": self._enter_emergency,
            "EXIT_EMERGENCY":  self._exit_emergency,
            "PAYLOAD_OFF":     lambda: setattr(self, "payload_on", False),
            "PAYLOAD_ON":      lambda: setattr(self, "payload_on", True),
            "ENABLE_CHARGING": self._enable_charging,
            "ENABLE_HEATER":   lambda: setattr(self, "heater_on", True),
            "DISABLE_HEATER":  lambda: setattr(self, "heater_on", False),
            "REDUCE_THERMAL_LOAD": lambda: setattr(self, "temperature",
                                       max(TEMP_MIN, self.temperature - 5)),
            "STABILISE_ATTITUDE": lambda: setattr(self, "pointing_error_deg",
                                       max(0.1, self.pointing_error_deg * 0.5)),
        }
        fn = cmd_map.get(command)
        if fn:
            fn()

    def _enter_safe_mode(self):
        self.mode = "SAFE"
        if self.pre_fault_payload_state is None:
            self.pre_fault_payload_state = self.payload_on
        self.payload_on = False

    def _exit_safe_mode(self):
        self.mode = "NOMINAL"

    def _enter_emergency(self):
        self.mode = "EMERGENCY"
        if self.pre_fault_payload_state is None:
            self.pre_fault_payload_state = self.payload_on
        self.payload_on = False

    def _exit_emergency(self):
        self.mode = "NOMINAL"

    def _enable_charging(self):
        if self.in_sunlight and self.solar_array_active:
            self.battery = min(BATTERY_MAX, self.battery + 8)