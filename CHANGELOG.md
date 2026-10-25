# Changelog

## Notes

* GitHub: <https://github.com/kcbam/dbus-huaweisun2000-pvinverter/>

## v1.9.0

New: ESS can now limit the inverter's feed-in (#32, by @okuegow)

The driver publishes `/Ac/PowerLimit`, so ESS limits a SUN2000 the same way it does a Fronius. Useful if you're on zero feed-in or the grid operator caps what you can push.

It's off by default. Switch it off or leave it alone and nothing changes. To use it:

1. Switch on "Allow ESS to limit the inverter" in the driver settings. Or `dbus -y com.victronenergy.settings /Settings/HuaweiSUN2000/PowerLimitEnabled SetValue 1`, or `settings["power_limit_enabled"] = 1` in `override_config.py`.
2. Set a feed-in limit in the ESS settings (Grid feed-in).

No feed-in limit set: ESS never writes the path and the switch does nothing. Off-grid isn't affected, the Multi still does that by shifting the frequency.

Good to know:
- It's slow on purpose. The inverter stores the limit (register 40125) in flash, so the driver writes 1 % steps, at most every 15 s, and steps up at most 120 times per hour. An 11 kW load takes about 3 minutes to follow. For zero feed-in within seconds you need a meter at the inverter.
- Driver or GX stops: the inverter goes back to 100 % by itself after 15 minutes (register 42019).
- On start the driver sets 42014 to 1 (needed for 40125) and 42019 to the fallback time.
- Tested on SUN2000-30KTL-M3 and 50KTL-M3, Venus OS v3.79 and v3.80. Running in production on a 50KTL since late September.

More in the README.

Upgrade:
`wget -qO- https://raw.githubusercontent.com/kcbam/dbus-huaweisun2000-pvinverter/main/setup/install_or_update.sh | bash`

## v1.8.3

Fix service/run file so that driver shutdown and restart work properly (by @okuegow)

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

## v1.7.0

Fix calculations for single phase inverters (by @SB10900)

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
