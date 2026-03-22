from config import *


# ── Fault Definitions ────────────────────────────────────────────────────────
FAULT_DEFS = {
    "LOW_BATTERY": {
        "subsystem": "EPS",
        "severity": "WARNING",
        "description": "Battery below minimum threshold",
    },
    "CRITICAL_BATTERY": {
        "subsystem": "EPS",
        "severity": "CRITICAL",
        "description": "Battery critically low – imminent power loss",
    },
    "HIGH_TEMP": {
        "subsystem": "THERMAL",
        "severity": "WARNING",
        "description": "Spacecraft temperature above operating limit",
    },
    "LOW_TEMP": {
        "subsystem": "THERMAL",
        "severity": "WARNING",
        "description": "Spacecraft temperature below safe operating range",
    },
    "ATTITUDE_FAULT": {
        "subsystem": "ADCS",
        "severity": "WARNING",
        "description": "Pointing error exceeds 1.5 degrees",
    },
    "COMMS_DEGRADED": {
        "subsystem": "COMMS",
        "severity": "CAUTION",
        "description": "Downlink quality below acceptable threshold",
    },
}


def _make_fault(fault_type):
    defn = FAULT_DEFS.get(fault_type, {})
    return {
        "type":        fault_type,
        "subsystem":   defn.get("subsystem", "UNK"),
        "severity":    defn.get("severity", "UNKNOWN"),
        "description": defn.get("description", ""),
    }


# ── Detection ────────────────────────────────────────────────────────────────
def detect_faults(sc):
    faults = []

    def _check(condition, key):
        if condition and key not in sc.active_faults:
            faults.append(_make_fault(key))
            sc.active_faults.add(key)

    _check(sc.battery < POWER_CRITICAL_THRESHOLD, "CRITICAL_BATTERY")
    _check(POWER_CRITICAL_THRESHOLD <= sc.battery < POWER_LOW_THRESHOLD, "LOW_BATTERY")
    _check(sc.temperature > TEMP_FAULT_HIGH, "HIGH_TEMP")
    _check(sc.temperature < TEMP_FAULT_LOW, "LOW_TEMP")
    _check(sc.pointing_error_deg > 1.5, "ATTITUDE_FAULT")
    _check(sc.in_ground_contact and sc.link_quality < 50, "COMMS_DEGRADED")

    if faults:
        sc.total_faults += len(faults)

    return faults


# ── Isolation ────────────────────────────────────────────────────────────────
def isolate_faults(sc, faults):
    actions = []
    severities = {f["severity"] for f in faults}

    for f in faults:
        ft = f["type"]
        if ft in ("LOW_BATTERY", "CRITICAL_BATTERY", "HIGH_TEMP"):
            if "PAYLOAD_OFF" not in actions:
                actions.append("PAYLOAD_OFF")
        if ft == "LOW_TEMP":
            actions.append("ENABLE_HEATER")
        if ft == "ATTITUDE_FAULT":
            actions.append("STABILISE_ATTITUDE")

    if "CRITICAL" in severities:
        actions.append("ENTER_EMERGENCY")
    elif "WARNING" in severities:
        if "ENTER_SAFE_MODE" not in actions:
            actions.append("ENTER_SAFE_MODE")

    return actions


# ── Recovery ─────────────────────────────────────────────────────────────────
def recover_faults(sc, faults):
    actions = []
    for f in faults:
        ft = f["type"]
        if ft in ("LOW_BATTERY", "CRITICAL_BATTERY"):
            actions.append("ENABLE_CHARGING")
        if ft == "HIGH_TEMP":
            actions.append("REDUCE_THERMAL_LOAD")
        if ft == "LOW_TEMP":
            actions.append("ENABLE_HEATER")
    return actions


# ── Resolution Check ─────────────────────────────────────────────────────────
def recovery_complete(sc):
    resolved = set()

    if "CRITICAL_BATTERY" in sc.active_faults and sc.battery > POWER_LOW_THRESHOLD:
        resolved.add("CRITICAL_BATTERY")
    if "LOW_BATTERY" in sc.active_faults and sc.battery > POWER_RECOVER_THRESHOLD:
        resolved.add("LOW_BATTERY")
    if "HIGH_TEMP" in sc.active_faults and sc.temperature < TEMP_RECOVER_HIGH:
        resolved.add("HIGH_TEMP")
    if "LOW_TEMP" in sc.active_faults and sc.temperature > TEMP_RECOVER_LOW:
        resolved.add("LOW_TEMP")
    if "ATTITUDE_FAULT" in sc.active_faults and sc.pointing_error_deg < 0.8:
        resolved.add("ATTITUDE_FAULT")
    if "COMMS_DEGRADED" in sc.active_faults and sc.link_quality > 65:
        resolved.add("COMMS_DEGRADED")

    return resolved