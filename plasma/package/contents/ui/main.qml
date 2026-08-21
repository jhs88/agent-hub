import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasmoid
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    property var snapshot: ({
        "schemaVersion": 1,
        "providers": [],
        "agents": [],
        "defaultAgent": "",
        "privacy": {"contentRetained": false}
    })
    property int selectedProviderIndex: 0
    property bool loading: false
    property string errorText: ""

    readonly property var providers: snapshot.providers || []
    readonly property var agents: snapshot.agents || []
    readonly property var selectedProvider: providers.length > 0
        ? providers[Math.min(selectedProviderIndex, providers.length - 1)]
        : null

    preferredRepresentation: Plasmoid.compactRepresentation
    toolTipMainText: i18n("Agent Hub")
    toolTipSubText: selectedProvider
        ? i18n("%1 · %2 tokens today", selectedProvider.name, formatNumber(selectedProvider.todayTotalTokens || 0))
        : (errorText || i18n("No usage data"))

    function formatNumber(value) {
        const number = Number(value || 0)
        if (number >= 1000000000)
            return (number / 1000000000).toFixed(1) + "B"
        if (number >= 1000000)
            return (number / 1000000).toFixed(1) + "M"
        if (number >= 1000)
            return (number / 1000).toFixed(1) + "K"
        return Math.round(number).toString()
    }

    function unpack(result) {
        let payload = result
        if (payload && payload.value !== undefined)
            payload = payload.value
        if (Array.isArray(payload) && payload.length > 0)
            payload = payload[0]
        return payload
    }

    function consume(result) {
        try {
            const decoded = JSON.parse(unpack(result))
            snapshot = decoded
            if (selectedProviderIndex >= providers.length)
                selectedProviderIndex = 0
            errorText = ""
        } catch (error) {
            errorText = i18n("Invalid helper response")
        }
        loading = false
    }

    function call(member, arguments, onSuccess) {
        loading = true
        DBus.SessionBus.asyncCall({
            "service": "io.github.jhs88.AgentHub",
            "path": "/io/github/jhs88/AgentHub",
            "iface": "io.github.jhs88.AgentHub1",
            "member": member,
            "arguments": arguments || []
        }, function(result) {
            if (onSuccess)
                onSuccess(result)
            else
                consume(result)
        }, function(error) {
            loading = false
            errorText = error && error.error ? String(error.error.message || error.error) : i18n("Agent Hub helper unavailable")
        })
    }

    function getSnapshot() {
        call("GetSnapshot", [], consume)
    }

    function refresh() {
        call("Refresh", [], consume)
    }

    function setDefaultAgent(agent) {
        call("SetDefaultAgent", [agent], consume)
    }

    function launchAgent(agent) {
        call("Launch", [agent || ""], consume)
    }

    Component.onCompleted: getSnapshot()

    DBus.DBusServiceWatcher {
        id: helperWatcher
        busType: DBus.BusType.Session
        watchedService: "io.github.jhs88.AgentHub"
        onRegisteredChanged: {
            if (registered)
                root.getSnapshot()
        }
    }

    Timer {
        interval: 60000
        repeat: true
        running: helperWatcher.registered
        onTriggered: root.getSnapshot()
    }

    compactRepresentation: MouseArea {
        Layout.minimumWidth: Kirigami.Units.iconSizes.small
        Layout.minimumHeight: Kirigami.Units.iconSizes.small
        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        onClicked: root.expanded = !root.expanded

        Kirigami.Icon {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            source: root.errorText ? "data-error" : "view-statistics"
        }

        PlasmaComponents.BusyIndicator {
            anchors.centerIn: parent
            width: parent.width
            height: parent.height
            running: root.loading
            visible: running
        }
    }

    fullRepresentation: Kirigami.ScrollablePage {
        id: page
        implicitWidth: Kirigami.Units.gridUnit * 25
        implicitHeight: Kirigami.Units.gridUnit * 35
        title: i18n("Agent Hub")

        ColumnLayout {
            width: page.availableWidth
            spacing: Kirigami.Units.largeSpacing

            RowLayout {
                Layout.fillWidth: true

                Kirigami.Heading {
                    Layout.fillWidth: true
                    level: 2
                    text: root.selectedProvider ? root.selectedProvider.name : i18n("Agent Hub")
                    textFormat: Text.PlainText
                }

                PlasmaComponents.ToolButton {
                    icon.name: "view-refresh"
                    text: i18n("Refresh")
                    enabled: !root.loading
                    onClicked: root.refresh()
                }

                PlasmaComponents.ToolButton {
                    icon.name: "utilities-terminal"
                    text: i18n("Launch default agent")
                    enabled: root.snapshot.defaultAgent !== ""
                    onClicked: root.launchAgent("")
                }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.errorText !== ""
                type: Kirigami.MessageType.Error
                text: root.errorText
            }

            PlasmaComponents.ComboBox {
                Layout.fillWidth: true
                visible: root.providers.length > 1
                model: root.providers.map(provider => provider.name)
                currentIndex: root.selectedProviderIndex
                onActivated: index => root.selectedProviderIndex = index
            }

            Kirigami.Heading {
                visible: root.selectedProvider && root.selectedProvider.limits.length > 0
                level: 3
                text: i18n("Subscription limits")
            }

            Repeater {
                model: root.selectedProvider ? root.selectedProvider.limits : []

                ColumnLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        PlasmaComponents.Label {
                            Layout.fillWidth: true
                            text: modelData.label
                            textFormat: Text.PlainText
                        }
                        PlasmaComponents.Label {
                            text: Math.round(Number(modelData.percent || 0) * 100) + "%"
                        }
                    }
                    PlasmaComponents.ProgressBar {
                        Layout.fillWidth: true
                        from: 0
                        to: 1
                        value: Number(modelData.percent || 0)
                    }
                }
            }

            Kirigami.Heading {
                visible: root.selectedProvider !== null
                level: 3
                text: i18n("Today")
            }

            RowLayout {
                Layout.fillWidth: true
                visible: root.selectedProvider !== null

                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: i18n("%1 tokens", root.formatNumber(root.selectedProvider ? root.selectedProvider.todayTotalTokens : 0))
                }
                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: i18n("%1 prompts", root.selectedProvider ? root.selectedProvider.todayPrompts : 0)
                }
                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: i18n("%1 sessions", root.selectedProvider ? root.selectedProvider.todaySessions : 0)
                }
            }

            Kirigami.Heading {
                level: 3
                text: i18n("Default agent")
            }

            RowLayout {
                Layout.fillWidth: true

                Repeater {
                    model: root.agents
                    PlasmaComponents.Button {
                        required property var modelData
                        text: modelData.id
                        enabled: modelData.installed
                        checkable: true
                        checked: root.snapshot.defaultAgent === modelData.id
                        onClicked: root.setDefaultAgent(modelData.id)
                    }
                }
            }

            Kirigami.PlaceholderMessage {
                Layout.fillWidth: true
                visible: root.providers.length === 0 && root.errorText === ""
                icon.name: "view-statistics"
                text: i18n("No aggregate usage data yet")
                explanation: i18n("Refresh after a coding-agent session has recorded token usage.")
            }
        }
    }
}
