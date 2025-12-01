# Modbus Connection Troubleshooting Guide

## Current Issue

The service is experiencing connection failures with the error:
```
Connection unexpectedly closed 0.000065 seconds into read of 8 bytes
```

This means:
- TCP connection to inverter succeeds ✓
- But inverter immediately closes connection when register read is attempted ✗

## Recent Fixes Applied

The following changes have been implemented to address this issue:

1. **Connection lifecycle management**: Explicit disconnect/reconnect cycle for each data read
2. **Increased timeouts**: Connection timeout increased from 5s → 10s
3. **Increased wait time**: Post-connection wait increased from 2s → 3s
4. **Better error handling**: Proper try/catch blocks and cleanup
5. **Enhanced logging**: Shows modbus unit ID and connection state

## Next Steps to Try

### 1. Test Current Changes
Deploy the updated code and check if the connection issues are resolved:
```bash
# Restart the service
svc -t /service/dbus-huaweisun2000-pvinverter

# Wait for several update cycles
sleep 10

# Check logs for successful reads
tail -50 /var/log/dbus-huaweisun2000/current | tai64nlocal
```

Look for:
- "Successfully read inverter data" (good!)
- "Reading inverter data with modbus unit X" (shows which unit ID is being used)
- Any connection errors

### 2. Try Different Modbus Unit IDs

If the issue persists, the most common cause is wrong Modbus Unit ID.

**Current setting: Unit 0** (default)

To try different unit IDs via VenusOS GUI:
1. Go to Settings → Services → Huawei SUN2000
2. Change "Modbus Unit" setting
3. Try these values in order:
   - **1** (most common for Sun2000 inverters)
   - **255** (broadcast address, sometimes works)
   - **0** (current setting)

The service will automatically restart when you change this setting.

### 3. Increase Polling Interval

If the inverter is overwhelmed by frequent requests:

Current: 1000ms (1 second)
Try: 2000ms or 5000ms

Via VenusOS GUI:
- Settings → Services → Huawei SUN2000 → Update Time MS

### 4. Check Inverter Configuration

Some Huawei Sun2000 inverters need specific Modbus settings:
- Ensure Modbus TCP is enabled on the inverter
- Check if the inverter has any Modbus security settings
- Verify the inverter's IP address (currently: 192.168.0.30)
- Confirm port 6607 is correct (standard for Sun2000)

### 5. Network Issues

Check basic connectivity:
```bash
# Test TCP connection
nc -zv 192.168.0.30 6607

# Or with telnet
telnet 192.168.0.30 6607
```

## Diagnostic Logging

The code now provides detailed logging. Check for these messages:

**Good signs:**
- "Successfully connected to inverter (unit X)"
- "Reading inverter data with modbus unit X"
- "Successfully read inverter data"
- "Read phase powers: L1=XXX, L2=XXX, L3=XXX"

**Problem indicators:**
- "A connection error occurred"
- "Connection error Modbus TCP"
- "Error reading inverter registers"

## Common Solutions for Huawei Sun2000

Based on known issues with Sun2000 inverters:

1. **SDongle WLAN-FE models**: Require frequent disconnect/reconnect (now implemented)
2. **Unit ID**: Usually 1, not 0
3. **Polling interval**: Some models need ≥2 seconds between reads
4. **Time of day**: Some inverters disable Modbus when not generating power

## Testing Meter Functionality

Once inverter connection works, the meter data will be automatically read. You'll see:
- "getMeterData() called"
- "Meter status = X" (1 or higher means meter connected)
- "Read phase powers: L1=X, L2=X, L3=X"

If meter status is 0 or None, no external meter is connected.

## Contact Information

If none of these steps resolve the issue, please provide:
1. Full log output after restart
2. Inverter model (e.g., "SUN2000-5KTL-L1")
3. Modbus unit IDs tried
4. Inverter configuration screenshots
