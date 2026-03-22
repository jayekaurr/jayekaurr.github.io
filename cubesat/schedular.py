"""
Autonomous Command Scheduler
Runs after each telemetry cycle to issue standing orders.
"""

from config import POWER_LOW_THRESHOLD, TEMP_FAULT_HIGH, TEMP_FAULT_LOW


def schedule(telemetry):
    """Return a list of commands to execute based on current telemetry."""
    commands = []
    mode    = telemetry.get("mode", "NOMINAL")
    battery = telemetry.get("battery", 100)
    temp    = telemetry.get("temperature", 20)
    sunlit  = telemetry.get("sunlight", False)

    if mode == "NOMINAL":
        # Payload on only if power and thermal margins are safe
        if battery > 60 and sunlit and TEMP_FAULT_LOW < temp < TEMP_FAULT_HIGH:
            commands.append("PAYLOAD_ON")
        elif battery < POWER_LOW_THRESHOLD or temp >= TEMP_FAULT_HIGH:
            commands.append("PAYLOAD_OFF")

        # Heater on if cold risk
        if temp < -8:
            commands.append("ENABLE_HEATER")

    return commands