"""Constants for the Clash Controller."""

DOMAIN = "clash_controller"

# Configs

CONF_API_URL = "api_url"
CONF_BEAR_TOKEN = "bearer_token"
CONF_USE_SSL = "use_ssl"
CONF_ALLOW_UNSAFE = "allow_unsafe"

# Options

MIN_SCAN_INTERVAL = 10
DEFAULT_SCAN_INTERVAL = 60

MIN_CONCURRENT_CONNECTIONS = 1
DEFAULT_CONCURRENT_CONNECTIONS = 5
CONF_CONCURRENT_CONNECTIONS = "concurrent_connections"

# Service names

API_CALL_SERVICE_NAME = "api_call_service"
DNS_QUERY_SERVICE_NAME = "dns_query_service"
FILTER_CONNECTION_SERVICE_NAME = "filter_connection_service"
GET_LATENCY_SERVICE_NAME = "get_latency_service"
GET_RULE_SERVICE_NAME = "get_rule_service"
REBOOT_CORE_SERVICE_NAME = "reboot_core_service"

# Signal names
SIGNAL_UPLOAD_SPEED_UPDATE = "clash_upload_speed_update"
SIGNAL_DOWNLOAD_SPEED_UPDATE = "clash_download_speed_update"
SIGNAL_UPLOAD_TOTAL_UPDATE = "clash_upload_total_update"
SIGNAL_DOWNLOAD_TOTAL_UPDATE = "clash_download_total_update"
SIGNAL_PROXY_GROUPS_UPDATE = "clash_proxy_group_update"
SIGNAL_ACTIVE_CONNECTIONS_UPDATE = "clash_connection_update"
SIGNAL_MODE_UPDATE = "clash_mode_update"
SIGNAL_MEMORY_USAGE_UPDATE = "clash_memory_usage_update"
SIGNAL_DEVICE_INFO_UPDATE = "clash_device_info_update"
