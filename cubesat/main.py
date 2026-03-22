from spacecraft import Spacecraft
from lifecycle import update
from telemetry import generate
from fdir import detect_faults, isolate_faults, recover_faults, recovery_complete
from schedular import schedule
from util import print_telemetry, print_fault, print_action
import time

sc = Spacecraft()

for step in range(1, 100):

    update(sc)
    print_telemetry(step, sc)

    # ── Autonomous Scheduling ─────────────────
    sched_cmds = schedule(generate(sc))
    if sched_cmds:
        print_action("📅 SCHEDULER", sched_cmds)
        for cmd in sched_cmds:
            sc.execute(cmd)

    # ── FDIR Pipeline ─────────────────────────
    faults = detect_faults(sc)
    for fault in faults:
        print_fault(fault)

    if faults:
        isolation_actions = isolate_faults(sc, faults)
        print_action("🔎 ISOLATION", isolation_actions)
        for a in isolation_actions:
            sc.execute(a)

        recovery_actions = recover_faults(sc, faults)
        print_action("🛠️  RECOVERY", recovery_actions)
        for a in recovery_actions:
            sc.execute(a)

    # ── Recovery Validation ───────────────────
    if sc.mode in ("SAFE", "EMERGENCY"):
        resolved = recovery_complete(sc)

        if resolved:
            print(f"\n✅ RESOLVED: {resolved}")
            sc.active_faults -= resolved

        if not sc.active_faults:
            sc.execute("EXIT_SAFE_MODE")
            sc.execute("EXIT_EMERGENCY")

            if sc.pre_fault_payload_state:
                if sc.battery > 40 and sc.temperature < 45 and sc.in_sunlight:
                    sc.execute("PAYLOAD_ON")
                    print("   Payload restored to ON")

            sc.pre_fault_payload_state = None
            print("   Spacecraft returned to NOMINAL")

    time.sleep(0.3)