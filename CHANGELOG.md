# Changelog

## Notes

* GitHub: <https://github.com/kcbam/dbus-huaweisun2000-pvinverter/>

## v1.6.0

Reworked logging completely. Fixed the StatusCode and Status fields to show
sensible data. Show status changes of devices in the logfile. Code improvements.

### BREAKING CHANGES

* The setting "PowerCorrectionFactor" has been renamed to "PCFOverride".

## v1.5.1

Fixed bug in the installer that would lead to the logging not starting.

## v1.5

Fixed critical bug that made it so that a significant amount of the DBus paths wouldn't be registered.
This inhibited the display of data on the gui-v2.
Added CHANGELOG.md, pre-commit support and VERSION file.

## v1.4.1

Fixed bug where the values would come from the Meter instead of the Inverter; enable sanity check of power factor

## v1.4

Detect QtQuick version and adapt accordingly.

## v1.3.0

Updated installation instructions.

## v1.2.0

First major version that allowed github releases.
Added installation script so it's easier to update and install the driver.

## v1.1.0

Added energy meter support, PR by @ricpax.
