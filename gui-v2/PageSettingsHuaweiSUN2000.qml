/*
** Copyright (C) 2023 Victron Energy B.V.
** See LICENSE file for license information.
*/

import QtQuick
import Victron.VenusOS

Page {
	id: root

	property string settingsBindPrefix: "com.victronenergy.settings/Settings/HuaweiSUN2000"

	GradientListView {
		model: ObjectModel {
			ListTextItem {
				text: qsTr("Modbus Host IP")
				dataItem.uid: root.settingsBindPrefix + "/ModbusHost"
				allowed: VenusOS.User_AccessType_User
			}

			ListTextField {
				text: qsTr("Modbus Port")
				dataItem.uid: root.settingsBindPrefix + "/ModbusPort"
				allowed: VenusOS.User_AccessType_User
			}

			ListTextField {
				text: qsTr("Modbus Unit")
				dataItem.uid: root.settingsBindPrefix + "/ModbusUnit"
				allowed: VenusOS.User_AccessType_User
			}

			ListTextField {
				text: qsTr("Custom Name")
				dataItem.uid: root.settingsBindPrefix + "/CustomName"
				allowed: VenusOS.User_AccessType_User
			}

			ListRadioButtonGroup {
				text: qsTr("Position")
				dataItem.uid: root.settingsBindPrefix + "/Position"
				optionModel: [
					{ display: qsTr("AC Input 1"), value: 0 },
					{ display: qsTr("AC Input 2"), value: 2 },
					{ display: qsTr("AC Output"), value: 1 }
				]
			}

			ListTextField {
				text: qsTr("Update Time (ms)")
				dataItem.uid: root.settingsBindPrefix + "/UpdateTimeMS"
				allowed: VenusOS.User_AccessType_User
			}

			ListSpinBox {
				text: qsTr("Power Correction Factor")
				dataItem.uid: root.settingsBindPrefix + "/PowerCorrectionFactor"
				decimals: 3
				stepSize: 0.001
				to: 2.0
				from: 0.5
			}
		}
	}
}
