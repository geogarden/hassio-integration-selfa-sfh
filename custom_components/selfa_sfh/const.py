"""Connection defaults and the two documented controls."""

DOMAIN = "selfa_sfh"
CONF_PROTOCOL = "protocol"
CONF_SLAVE_ID = "slave_id"
CONF_SETTINGS_INTERVAL = "settings_interval"
CONF_REQUEST_DELAY = "request_delay"
CONF_TIMEOUT = "timeout"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 247
DEFAULT_PROTOCOL = "rtu_over_tcp"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SETTINGS_INTERVAL = 300
DEFAULT_REQUEST_DELAY = 200
DEFAULT_TIMEOUT = 3
PROTOCOLS = ["rtu_over_tcp", "tcp", "udp"]
CONTROL_REGISTERS = {"unbalanced_output": 50006, "peak_load_shifting": 50007}
WORK_STATES = {
    0: "waiting_for_grid",
    1: "self_test",
    2: "on_grid",
    3: "fault",
    4: "firmware_update",
    5: "off_grid",
}
BATTERY_STATES = {0: "discharging", 1: "charging"}
