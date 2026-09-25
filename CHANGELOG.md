# Changelog

## Notes

* GitHub: <https://github.com/kcbam/dbus-huaweisun2000-pvinverter/>

## v1.8.2

Log the version number on startup.

## v1.8.1

Fixed bug in the installer when installing the latest release.

## v1.8.0

Registers are now read in blocks instead of one Modbus request per register
(#28, by @okuegow). A SUN2000 answers a request in about 300 ms no matter how
many registers it covers, so a cycle on a SUN2000-50KTL-M3 dropped from
about 5 s to about 1 s, and `UpdateTimeMS` down to about 1000 now takes effect.
If a model rejects a block, the driver falls back to single reads for that group
and warns once per start. Block reads can be switched off with the new setting
"Read registers in blocks" (`BlockRead`, default on).

Failed reads now raise an error instead of being reported as 0, so read errors
no longer show up as 0 W on D-Bus and in the yield statistics.

Added retries with exponential backoff for flaky connections (`MaxRetries`,
`BackoffInSeconds`, `BackoffFactor`). Fixed the energy counter for single phase
inverters. Fixed `override_config.py` so it takes effect right away.
The installer can now install a specific version (`bash -s v1.6.1`) or from any
zip URL, e.g. a PR branch.

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
