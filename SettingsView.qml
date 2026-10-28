import QtQuick
import QtQuick.Controls
import qs.Commons

// In-popup settings: which columns new boards start with folded, and how
// often to refresh. Changes are saved to shell.json right away.
Item {
  id: view
  required property var host
  readonly property color fg: host.foreground
  readonly property color pane: Qt.rgba(fg.r, fg.g, fg.b, 0.035)
  readonly property color line: Qt.rgba(fg.r, fg.g, fg.b, 0.08)

  implicitHeight: content.implicitHeight

  component Heading: BoardText {
    color: view.host.dim
    font { bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
  }

  Flickable {
    anchors.fill: parent
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(6)

      Row {
        spacing: Style.space(8)
        Pill { label: "‹ Back"; clickable: true; textColor: view.host.foreground; onClicked: view.host.back() }
        BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Settings"; font { pixelSize: Style.font.bodySmall; bold: true } }
      }

      Item { width: 1; height: Style.space(4) }
      Heading { text: "Start collapsed" }
      BoardText {
        width: parent.width; wrapMode: Text.Wrap; color: view.host.dim
        text: "New boards open with these columns folded. Your per-board choices win."
      }

      // One row per column: its board color, its name, a check box. The whole
      // row toggles.
      Rectangle {
        width: parent.width
        implicitHeight: rows.implicitHeight
        radius: Style.space(8)
        color: view.pane
        border { width: 1; color: view.line }
        clip: true

        Column {
          id: rows
          width: parent.width
          Repeater {
            model: view.host.availableColumns
            delegate: Rectangle {
              id: row
              required property var modelData
              required property int index
              readonly property string columnName: modelData.name
              readonly property bool on: view.host.isDefaultCollapsed(modelData.name)
              width: rows.width
              implicitHeight: name.implicitHeight + Style.space(14)
              color: rowMouse.containsMouse ? Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.06) : "transparent"
              Behavior on color { ColorAnimation { duration: 100 } }

              Rectangle { visible: row.index > 0; width: parent.width; height: 1; color: view.line }
              Rectangle {
                id: dot
                x: Style.space(12); anchors.verticalCenter: parent.verticalCenter
                width: Style.space(8); height: width; radius: width / 2
                color: view.host.columnAccent(row.modelData)
              }
              BoardText {
                id: name
                anchors { left: dot.right; leftMargin: Style.space(8); right: box.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
                elide: Text.ElideRight
                text: row.modelData.name
                font.pixelSize: Style.font.bodySmall
              }
              // On: filled in the theme accent with a check. Off: an empty outline.
              Rectangle {
                id: box
                anchors { right: parent.right; rightMargin: Style.space(12); verticalCenter: parent.verticalCenter }
                width: Style.space(16); height: width; radius: Style.space(4)
                color: row.on ? view.host.accent : "transparent"
                border { width: 1; color: row.on ? view.host.accent : rowMouse.containsMouse ? view.host.foreground : view.host.dim }
                Behavior on color { ColorAnimation { duration: 100 } }
                BoardText {
                  anchors.centerIn: parent
                  visible: row.on
                  text: "\uf00c"
                  color: view.host.background
                  font.pixelSize: Style.font.caption
                }
              }
              MouseArea {
                id: rowMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: view.host.toggleDefaultCollapsed(row.modelData.name)
              }
            }
          }
        }
      }

      Item { width: 1; height: Style.space(6) }
      Heading { text: "Refresh every" }

      // Segmented control: the current interval is filled in the accent.
      Rectangle {
        implicitWidth: segments.implicitWidth + Style.space(4)
        implicitHeight: segments.implicitHeight + Style.space(4)
        radius: Style.space(8)
        color: view.pane
        border { width: 1; color: view.line }

        Row {
          id: segments
          anchors.centerIn: parent
          spacing: Style.space(2)
          Repeater {
            model: [30, 60, 120, 300, 900]
            delegate: Rectangle {
              id: segment
              required property int modelData
              readonly property int seconds: modelData
              readonly property bool current: view.host.refreshIntervalSec === modelData
              implicitWidth: segText.implicitWidth + Style.space(16)
              implicitHeight: segText.implicitHeight + Style.space(8)
              radius: Style.space(6)
              color: current ? view.host.accent : segMouse.containsMouse ? Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.06) : "transparent"
              Behavior on color { ColorAnimation { duration: 100 } }
              BoardText {
                id: segText
                anchors.centerIn: parent
                text: segment.modelData < 60 ? segment.modelData + "s" : (segment.modelData / 60) + " min"
                color: segment.current ? view.host.background : segMouse.containsMouse ? view.host.foreground : view.host.dim
                font { pixelSize: Style.font.bodySmall; bold: segment.current }
              }
              MouseArea {
                id: segMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: view.host.setRefreshInterval(segment.modelData)
              }
            }
          }
        }
      }
    }
  }
}
