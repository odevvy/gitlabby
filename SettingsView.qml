import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui

// In-popup settings: which of this board's columns start collapsed, and how
// often to refresh. Changes are saved to shell.json right away.
Item {
  id: view
  required property var host

  implicitHeight: content.implicitHeight

  Flickable {
    anchors.fill: parent
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(8)

      Row {
        spacing: Style.space(8)
        Pill { label: "‹ Back"; clickable: true; textColor: view.host.foreground; onClicked: view.host.back() }
        BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Settings"; font { pixelSize: Style.font.bodySmall; bold: true } }
      }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        text: "Collapsed by default: used for boards you have not collapsed or expanded yet. Matches column names on every board."
        color: view.host.dim
      }

      Repeater {
        model: view.host.availableColumns
        delegate: Toggle {
          required property var modelData
          width: content.width
          label: modelData.name
          description: "Collapsed by default"
          checked: view.host.isDefaultCollapsed(modelData.name)
          foreground: view.host.foreground
          onClicked: view.host.toggleDefaultCollapsed(modelData.name)
        }
      }

      BoardText { text: "Refresh every"; color: view.host.dim }
      Flow {
        width: parent.width; spacing: Style.space(4)
        Repeater {
          model: [30, 60, 120, 300, 900]
          delegate: Pill {
            required property int modelData
            readonly property bool current: view.host.refreshIntervalSec === modelData
            label: modelData < 60 ? modelData + "s" : (modelData / 60) + " min"
            clickable: true
            textColor: current ? view.host.foreground : view.host.dim
            color: current ? view.host.faint : "transparent"
            border.color: current ? view.host.accent : view.host.faint
            onClicked: view.host.setRefreshInterval(modelData)
          }
        }
      }
    }
  }
}
