import QtQuick
import QtQuick.Controls
import qs.Commons
import "Logic.js" as Logic

// The popup's keys (Logic.keyGroups, also in the README), grouped by where
// they work, as keycaps. ? toggles it; ✕ or Esc returns to the board. Two
// columns when there is room; it scrolls if the screen is short.
Item {
  id: view
  required property var host
  readonly property bool twoColumns: width >= Style.space(640)
  readonly property real columnWidth: twoColumns ? (width - Style.space(28)) / 2 : width
  readonly property real capsWidth: Style.space(150)

  implicitHeight: top.implicitHeight + Style.space(10) + groups.implicitHeight

  Item {
    id: top
    width: parent.width
    implicitHeight: close.implicitHeight
    BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Keyboard shortcuts"; font { pixelSize: Style.font.bodySmall; bold: true } }
    GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; tip: "Back to the board (Esc)"; onClicked: view.host.back() }
  }

  Flickable {
    anchors { top: top.bottom; topMargin: Style.space(10); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentHeight: groups.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    // Groups fill the left column, then the right; each stays whole.
    Row {
      id: groups
      width: parent.width
      spacing: Style.space(28)
      Repeater {
        model: view.twoColumns ? [Logic.keyGroups.slice(0, 3), Logic.keyGroups.slice(3)] : [Logic.keyGroups]
        delegate: Column {
          id: side
          required property var modelData
          width: view.columnWidth
          spacing: Style.space(14)
          Repeater {
            model: side.modelData
            delegate: Column {
              id: group
              required property var modelData
              width: side.width
              spacing: Style.space(4)
              BoardText {
                text: group.modelData.title
                color: view.host.dim
                font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
              }
              Repeater {
                model: group.modelData.keys
                delegate: Item {
                  id: keyRow
                  required property var modelData
                  width: group.width
                  implicitHeight: Math.max(caps.implicitHeight, what.implicitHeight) + Style.space(4)
                  Flow {
                    id: caps
                    width: view.capsWidth
                    spacing: Style.space(4)
                    Repeater {
                      model: Logic.keyParts(keyRow.modelData[0])
                      delegate: Item {
                        id: part
                        required property var modelData
                        width: part.modelData.cap !== undefined ? cap.width : sep.implicitWidth
                        height: Style.space(22)
                        Rectangle {
                          id: cap
                          visible: part.modelData.cap !== undefined
                          anchors.verticalCenter: parent.verticalCenter
                          width: Math.max(Style.space(22), capText.implicitWidth + Style.space(12)); height: Style.space(22)
                          radius: Style.space(4)
                          color: Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, 0.06)
                          border { width: 1; color: view.host.faint }
                          BoardText { id: capText; anchors.centerIn: parent; text: part.modelData.cap || ""; color: view.host.accent; font { pixelSize: Style.font.caption; bold: true } }
                        }
                        BoardText {
                          id: sep
                          visible: part.modelData.text !== undefined
                          anchors.verticalCenter: parent.verticalCenter
                          text: part.modelData.text || ""
                          color: view.host.dim
                          font.pixelSize: Style.font.caption
                        }
                      }
                    }
                  }
                  BoardText {
                    id: what
                    x: view.capsWidth + Style.space(10)
                    width: group.width - x
                    topPadding: Style.space(2)
                    wrapMode: Text.Wrap
                    text: keyRow.modelData[1]
                    font.pixelSize: Style.font.bodySmall
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
