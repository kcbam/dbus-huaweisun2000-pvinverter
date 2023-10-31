import logging

## CONFIGURATION ##
# Default IP: 192.168.200.1
HOST = "192.168.200.1"

# Default Port: 6607 / Old firmware has 502
PORT = 6607

# Default modbus unit: 0 (may need 1 for some inverters or even higher number if using a SmartLogger)
MODBUS_UNIT = 0

# Uncomment for no custom name
CUSTOM_NAME = "Huawei SUN2000"

# Instance Number in VRM
DEVICE_INSTANCE = 40

# Position: 0 = AC Input, 1 = AC-Out 1, AC-Out 2
POSITION = 0

# Loglevel: INFO, DEBUG, ERROR
LOGGING = logging.DEBUG

# Time between calling the update method
UPDATE_TIME_IN_MS=1000

# power correction factor per phase (in case a little calibration is needed)
POWER_CORRECTION_FACTOR = 0.995
