import QtQuick 2
import com.victron.velib 1.0

MbPage {
	title: qsTr("Huawei Inverter")

	property string bindPrefix: "com.victronenergy.pvinverter.sun2000"

	model: VisibleItemModel {
		MbItemRow {
			description: qsTr("Status")
			values: [
				MbTextBlock { item.bind: service.path("/Status"); width: 150; height: 25 }
			]
		}

		MbItemValue {
			description: qsTr("Total Power")
			item.bind: service.path("/Ac/Power")
		}

		MbItemValue {
			description: qsTr("Max Power")
			item.bind: service.path("/Ac/MaxPower")
		}

		MbItemValue {
			description: qsTr("Total Voltage")
			item.bind: service.path("/Ac/Voltage")
		}

		MbItemValue {
			description: qsTr("Total Current")
			item.bind: service.path("/Ac/Current")
		}

		MbItemValue {
			description: qsTr("Total Energy")
			item.bind: service.path("/Ac/Energy/Forward")
		}

		MbSubMenu {
			id: dcMenu
			description: qsTr("DC Power")
			show: dcPower.valid
			subpage: Component {
				MbPage {
					title: qsTr("DC Power")
					model: VisibleItemModel {
						MbItemValue {
							description: qsTr("DC Power")
							item.bind: service.path("/Dc/Power")
						}
					}
				}
			}
		}

		MbSubMenu {
			description: qsTr("Phase L1")
			subpage: Component {
				MbPage {
					title: qsTr("Phase L1")
					model: VisibleItemModel {
						MbItemValue {
							description: qsTr("Power")
							item.bind: service.path("/Ac/L1/Power")
						}
						MbItemValue {
							description: qsTr("Voltage")
							item.bind: service.path("/Ac/L1/Voltage")
						}
						MbItemValue {
							description: qsTr("Current")
							item.bind: service.path("/Ac/L1/Current")
						}
						MbItemValue {
							description: qsTr("Frequency")
							item.bind: service.path("/Ac/L1/Frequency")
						}
						MbItemValue {
							description: qsTr("Energy")
							item.bind: service.path("/Ac/L1/Energy/Forward")
						}
					}
				}
			}
		}

		MbSubMenu {
			description: qsTr("Phase L2")
			subpage: Component {
				MbPage {
					title: qsTr("Phase L2")
					model: VisibleItemModel {
						MbItemValue {
							description: qsTr("Power")
							item.bind: service.path("/Ac/L2/Power")
						}
						MbItemValue {
							description: qsTr("Voltage")
							item.bind: service.path("/Ac/L2/Voltage")
						}
						MbItemValue {
							description: qsTr("Current")
							item.bind: service.path("/Ac/L2/Current")
						}
						MbItemValue {
							description: qsTr("Frequency")
							item.bind: service.path("/Ac/L2/Frequency")
						}
						MbItemValue {
							description: qsTr("Energy")
							item.bind: service.path("/Ac/L2/Energy/Forward")
						}
					}
				}
			}
		}

		MbSubMenu {
			description: qsTr("Phase L3")
			subpage: Component {
				MbPage {
					title: qsTr("Phase L3")
					model: VisibleItemModel {
						MbItemValue {
							description: qsTr("Power")
							item.bind: service.path("/Ac/L3/Power")
						}
						MbItemValue {
							description: qsTr("Voltage")
							item.bind: service.path("/Ac/L3/Voltage")
						}
						MbItemValue {
							description: qsTr("Current")
							item.bind: service.path("/Ac/L3/Current")
						}
						MbItemValue {
							description: qsTr("Frequency")
							item.bind: service.path("/Ac/L3/Frequency")
						}
						MbItemValue {
							description: qsTr("Energy")
							item.bind: service.path("/Ac/L3/Energy/Forward")
						}
					}
				}
			}
		}

		MbSubMenu {
			description: qsTr("Device Info")
			subpage: Component {
				MbPage {
					title: qsTr("Device Info")
					model: VisibleItemModel {
						MbItemRow {
							description: qsTr("Product")
							values: [
								MbTextBlock { item.bind: service.path("/ProductName"); width: 150; height: 25 }
							]
						}
						MbItemRow {
							description: qsTr("Serial")
							values: [
								MbTextBlock { item.bind: service.path("/Serial"); width: 150; height: 25 }
							]
						}
						MbItemRow {
							description: qsTr("Custom Name")
							values: [
								MbTextBlock { item.bind: service.path("/CustomName"); width: 150; height: 25 }
							]
						}
						MbItemValue {
							description: qsTr("Firmware")
							item.bind: service.path("/FirmwareVersion")
						}
						MbItemRow {
							description: qsTr("Connection")
							values: [
								MbTextBlock { item.bind: service.path("/Mgmt/Connection"); width: 200; height: 25 }
							]
						}
					}
				}
			}
		}
	}

	VBusItem {
		id: dcPower
		bind: service.path("/Dc/Power")
	}

	VBusItem {
		id: service
		bind: bindPrefix
	}
}
