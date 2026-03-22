from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from spacecraft import Spacecraft
from lifecycle import update
from telemetrysources import get_telemetry
from fdir import detect_faults, isolate_faults, recover_faults, recovery_complete
from config import SATELLITE_NAME, MISSION_ID, POWER_LOW_THRESHOLD, TEMP_FAULT_HIGH, TEMP_FAULT_LOW

app = FastAPI(title=f"{SATELLITE_NAME} Mission Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simulation State ──────────────────────────────────────────────────────────
sc = Spacecraft()
step_counter = 0
event_log = []   # rolling 100 entries


def log_event(step, kind, detail):
    event_log.append({"step": step, "kind": kind, "detail": detail})
    if len(event_log) > 100:
        event_log.pop(0)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/step")
def step_simulation():
    global step_counter
    step_counter += 1

    update(sc)

    faults = detect_faults(sc)
    isolation_actions = []
    recovery_actions  = []
    resolved_faults   = []

    if faults:
        for f in faults:
            log_event(step_counter, "FAULT", f"{f['type']} ({f['subsystem']})")

        isolation_actions = isolate_faults(sc, faults)
        for action in isolation_actions:
            sc.execute(action)

        recovery_actions = recover_faults(sc, faults)
        for action in recovery_actions:
            sc.execute(action)

    if sc.mode in ("SAFE", "EMERGENCY"):
        resolved_faults = recovery_complete(sc)

        if resolved_faults:
            sc.active_faults -= resolved_faults
            for r in resolved_faults:
                log_event(step_counter, "RESOLVED", r)

        if not sc.active_faults:
            sc.execute("EXIT_SAFE_MODE")
            sc.execute("EXIT_EMERGENCY")

            if sc.pre_fault_payload_state:
                if (sc.battery > 40 and
                        TEMP_FAULT_LOW < sc.temperature < TEMP_FAULT_HIGH and
                        sc.in_sunlight):
                    sc.execute("PAYLOAD_ON")
                    log_event(step_counter, "RECOVERY", "Payload restored to ON")

            sc.pre_fault_payload_state = None
            log_event(step_counter, "NOMINAL", "Spacecraft returned to NOMINAL")

    # Orbit transition logging
    if sc.orbit_step == 0:
        log_event(step_counter, "ORBIT", f"Orbit #{sc.orbit_number} started")

    return {
        "step":       step_counter,
        "mode":       sc.mode,
        "telemetry":  get_telemetry(sc),
        "faults":     faults,
        "active_faults": list(sc.active_faults),
        "isolation":  isolation_actions,
        "recovery":   recovery_actions,
        "resolved":   list(resolved_faults),
        "events":     event_log[-10:],
    }


@app.get("/status")
def get_status():
    return {
        "step":    step_counter,
        "mode":    sc.mode,
        "telemetry": get_telemetry(sc),
        "active_faults": list(sc.active_faults),
    }


@app.get("/events")
def get_events():
    return {"events": event_log}


@app.post("/reset")
def reset_simulation():
    global sc, step_counter, event_log
    sc = Spacecraft()
    step_counter = 0
    event_log = []
    return {"status": "reset", "message": "Simulation reset to initial state"}


@app.post("/command/{cmd}")
def send_command(cmd: str):
    sc.execute(cmd)
    log_event(step_counter, "COMMAND", cmd)
    return {"status": "ok", "command": cmd}