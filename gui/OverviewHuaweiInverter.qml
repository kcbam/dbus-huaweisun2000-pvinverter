import QtQuick 2
import com.victron.velib 1.0
import "utils.js" as Utils

Tile {
	id: root

	property string bindPrefix: "com.victronenergy.pvinverter.sun2000"
	property VBusItem power: VBusItem { bind: Utils.path(bindPrefix, "/Ac/Power") }
	property VBusItem energy: VBusItem { bind: Utils.path(bindPrefix, "/Ac/Energy/Forward") }
	property VBusItem productName: VBusItem { bind: Utils.path(bindPrefix, "/ProductName") }

	// Meter data (grid import/export)
	property VBusItem meterStatus: VBusItem { bind: Utils.path(bindPrefix, "/Meter/Status") }
	property VBusItem meterPower: VBusItem { bind: Utils.path(bindPrefix, "/Meter/Power") }
	property VBusItem meterImport: VBusItem { bind: Utils.path(bindPrefix, "/Meter/Energy/Import") }
	property VBusItem meterExport: VBusItem { bind: Utils.path(bindPrefix, "/Meter/Energy/Export") }

	width: 160
	height: parent.height
	title: qsTr("HUAWEI PV")
	color: "#F39C12"
	show: power.valid

	values: [
		TileText {
			text: power.valid ? power.value.toFixed(0) + " W" : "---"
			font.pixelSize: 25
		},
		TileText {
			text: energy.valid ? (energy.value / 1000).toFixed(2) + " MWh" : "---"
			font.pixelSize: 16
		},
		TileText {
			// Show grid import/export if meter is available
			text: {
				if (!meterStatus.valid || meterStatus.value === 0)
					return productName.valid ? productName.value : "---"

				var gridPower = meterPower.value
				if (gridPower < 0)
					return "Import: " + gridPower.toFixed(0) + " W"
				else if (gridPower > 0)
					return "Export: " + Math.abs(gridPower).toFixed(0) + " W"
				else
					return "Grid: 0 W"
			}
			font.pixelSize: 14
		}
	]

	MbIcon {
		iconId: "overview-pv-inverter-flow"
		anchors {
			top: parent.top
			right: parent.right
			margins: 5
		}
		visible: power.valid && power.value > 0
	}
}
