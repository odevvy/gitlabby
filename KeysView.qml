import QtQuick
import QtQuick.Controls
import qs.Commons
import "Logic.js" as Logic
import "components"

// The popup's keys (Logic.keyGroups, also in the README), grouped by where
// they work. Laid out like Settings: no cards, each group under Settings'
// thin rule (fg at 12%) with a caption heading, and every shortcut is one 22 px line: compact
// caps (a chord's caps joined, "/" between choices), then short words and a
// quiet note. Two columns when there is room (Board's four groups on the
// left); it scrolls if the screen is short. ? toggles it; ✕ or Esc returns.
Item {
  id: view
  required property var host
  readonly property color fg: host.foreground
  readonly property color pane: Qt.rgba(fg.r, fg.g, fg.b, 0.035)
  readonly property real gap: Style.space(14)
  readonly property real pad: 0
  readonly property bool twoColumns: width >= Style.space(640)
  readonly property real columnWidth: twoColumns ? (width - gap) / 2 : width
  readonly property real capsWidth: Style.space(122)

  implicitHeight: top.implicitHeight + Style.space(10) + groups.implicitHeight

  // One key: caps, a chord's caps joined (2 px), choices split by a quiet "/".
  component Caps: Row {
    id: caps
    property string key: ""
    spacing: Style.space(5)
    Repeater {
      model: Logic.keyParts(caps.key)
      delegate: Item {
        id: part
        required property var modelData
        width: part.modelData.cap !== undefined ? cap.width - (part.modelData.joined ? Style.space(3) : 0) : sep.implicitWidth
        height: Style.space(20)
        Rectangle {
          id: cap
          objectName: "keyCap"
          visible: part.modelData.cap !== undefined
          // A joined cap sits 2 px after the one before it (the row puts 5 px).
          x: part.modelData.joined ? -Style.space(3) : 0
          width: Math.max(Style.space(20), capText.implicitWidth + Style.space(10)); height: Style.space(20)
          radius: Style.space(4)
          color: Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.07)
          BoardText { id: capText; anchors.centerIn: parent; text: part.modelData.cap || ""; color: view.host.foreground; font { pixelSize: Style.font.caption; bold: true } }
        }
        BoardText {
          id: sep
          objectName: "keySep"
          visible: part.modelData.text !== undefined
          anchors.verticalCenter: parent.verticalCenter
          text: part.modelData.text || ""
          color: view.host.quiet
          font.pixelSize: Style.font.caption
        }
      }
    }
  }

  Item {
    id: top
    width: parent.width
    implicitHeight: close.implicitHeight
    BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Keyboard shortcuts"; font { pixelSize: Style.font.subtitle; bold: true } }
    GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; tip: "Back to the board (Esc)"; onClicked: view.host.back() }
  }

  Flickable {
    id: flick
    anchors { top: top.bottom; topMargin: Style.space(6); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentHeight: groups.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    // Groups fill the left column (the first four: the board's), then the right.
    Row {
      id: groups
      width: parent.width
      spacing: view.gap
      Repeater {
        model: view.twoColumns ? [Logic.keyGroups.slice(0, 4), Logic.keyGroups.slice(4)] : [Logic.keyGroups]
        delegate: Column {
          id: side
          required property var modelData
          width: view.columnWidth
          spacing: view.gap
          Repeater {
            model: side.modelData
            delegate: Rectangle {
              id: card
              objectName: "keyGroup"
              required property var modelData
              width: side.width
              height: body.implicitHeight + Style.space(8)
              radius: 0
              color: "transparent"
              Rectangle { objectName: "keyRule"; width: parent.width; height: 1; color: Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.12) }
              Column {
                id: body
                x: 0; y: Style.space(8)
                width: parent.width - view.pad * 2
                BoardText {  // the group's heading, like Settings' (Omarchy's PanelSectionHeader)
                  text: card.modelData.title; bottomPadding: Style.space(4)
                  color: view.host.dim
                  font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
                }
                Repeater {
                  model: card.modelData.keys
                  delegate: Item {
                    id: keyRow
                    objectName: "keyRow"
                    required property var modelData
                    readonly property string what: String(modelData[1]).split(" · ")[0].replace("Open in browser", Logic.openLabel(view.host.linkMode))
                    readonly property string note: String(modelData[1]).split(" · ")[1] || ""
                    // Fits one line: the caps in their column, the words in the rest.
                    readonly property bool fits: caps.implicitWidth <= view.capsWidth && words.implicitWidth <= width - words.x
                    width: body.width
                    implicitHeight: Style.space(22)
                    Caps { id: caps; key: keyRow.modelData[0]; anchors.verticalCenter: parent.verticalCenter }
                    Row {
                      id: words
                      x: view.capsWidth + Style.space(12)
                      anchors.verticalCenter: parent.verticalCenter
                      spacing: Style.space(8)
                      BoardText { id: whatText; objectName: "keyWhat"; text: keyRow.what; font.pixelSize: Style.font.bodySmall }
                      BoardText { objectName: "keyNote"; visible: keyRow.note !== ""; y: whatText.baselineOffset - baselineOffset; text: keyRow.note; color: view.host.quiet; font.pixelSize: Style.font.caption }
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
  // More below: the bottom edge fades (ScrollHint.qml).
  ScrollHint { flick: flick; host: view.host }
}
