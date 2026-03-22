from config import SATELLITE_NAME, MISSION_ID, ORBIT_ALTITUDE_KM


def get_telemetry(sc):
    return {
        # Identification
        "name":        SATELLITE_NAME,
        "mission_id":  MISSION_ID,
        "altitude_km": ORBIT_ALTITUDE_KM,

        # Power
        "battery":          round(sc.battery, 1),
        "power_draw_w":     round(sc.power_draw_w, 2),
        "solar_charging":   sc.in_sunlight and sc.solar_array_active,

        # Thermal
        "temperature":  round(sc.temperature, 1),
        "heater_on":    sc.heater_on,

        # Attitude
        "pointing_error_deg": round(sc.pointing_error_deg, 2),
        "attitude_stable":    sc.attitude_stable,

        # Comms
        "in_ground_contact": sc.in_ground_contact,
        "link_quality":      round(sc.link_quality, 1),
        "uplink_packets":    sc.uplink_packets,
        "downlink_packets":  sc.downlink_packets,
        "comms":             sc.comms_available,

        # Orbit
        "in_sunlight":       sc.in_sunlight,
        "orbit_number":      sc.orbit_number,
        "eclipse_duration":  sc.eclipse_duration,

        # Payload
        "payload_on":        sc.payload_on,
        "payload_duty_cycle": sc.payload_duty_cycle,

        # Health summary
        "total_faults":  sc.total_faults,
        "uptime_steps":  sc.uptime_steps,
        "total_steps":   sc.total_steps,

        # History
        "history": {
            "battery":       sc.history["battery"],
            "temperature":   sc.history["temperature"],
            "link_quality":  sc.history["link_quality"],
        }
    }