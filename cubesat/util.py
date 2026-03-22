def print_telemetry(step, sc):
    print(f"\n{'─'*50}")
    print(f" [STEP {step:04d}] {sc.name}  |  Mode: {sc.mode}")
    print(f"{'─'*50}")
    print(f"  EPS     Battery : {sc.battery:6.1f}%  {'⚡ Charging' if sc.in_sunlight else '🌑 Eclipse'}")
    print(f"          Draw    : {sc.power_draw_w:5.2f} W")
    print(f"  THERMAL Temp    : {sc.temperature:6.1f} °C  {'🔥 Heater ON' if sc.heater_on else ''}")
    print(f"  ADCS    Err     : {sc.pointing_error_deg:5.2f} °  {'✅ Stable' if sc.attitude_stable else '⚠️  Unstable'}")
    print(f"  COMMS   Quality : {sc.link_quality:5.1f}%  {'📡 GS contact' if sc.in_ground_contact else '📵 No contact'}")
    print(f"  PAYLOAD         : {'ON' if sc.payload_on else 'OFF'}")
    print(f"  ORBIT   #       : {sc.orbit_number}  (step {sc.orbit_step}/{48})")
    if sc.active_faults:
        print(f"\n  ⚠️  ACTIVE FAULTS: {', '.join(sc.active_faults)}")


def print_fault(fault):
    sev = fault.get("severity", "UNKNOWN")
    icon = {"CRITICAL": "🔴", "WARNING": "🟡", "CAUTION": "🔵"}.get(sev, "⚠️")
    print(f"\n{icon} FAULT  {fault['type']}  [{fault['subsystem']}]  {sev}")
    print(f"   {fault.get('description', '')}")


def print_action(title, actions):
    if not actions:
        return
    print(f"\n  {title}")
    for a in actions:
        print(f"    → {a}")