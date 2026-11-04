CONFIG_DIR = "/etc/protoplaster"
REPORTS_DIR = "/var/lib/protoplaster/reports"
ARTIFACTS_DIR = "/var/lib/protoplaster/artifacts"
LOCAL_DEVICE_NAME = "Local device"
LOCAL_DEVICE_HOST = "localhost"
WEBUI_POLLING_INTERVAL = 1  # seconds
SERVE_IP = "127.0.0.1"
SECURE_TOKEN_ENV = "PROTOPLASTER_SECURE_TOKEN"
SECURE_SIGNATURE_HEADER = "X-Protoplaster-Signature"
REMOTE_RUN_TRIGGER_TIMEOUT = 10  # seconds
PROTOPLASTER = "protoplaster"
TEST_FILE = "test.yaml"
# test parameters that should not be reported as "unexpected"
SPECIAL_KEYS = ["override", "_execution_order"]
