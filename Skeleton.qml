import QtQuick
import qs.Commons

// Placeholder board while nothing is on screen yet (first run, no saved
// copy): chips and columns of faded cards that pulse, with "Loading…" over
// them. Columns are unnamed: names come only with the board answer. Same
// sizes as BoardView, so the popup opens at board size.
Item {
  id: skeleton
  required property var host
  readonly property var cards: [3, 2, 3, 2]  // placeholder cards per column
  readonly property int cardHeight: Style.space(64)
  readonly property color fg: host.foreground
  implicitWidth: cards.length * (host.columnWidth + host.gap)
  implicitHeight: chips.height + host.gap + Style.space(18) + Math.max.apply(null, cards) * (cardHeight + Style.space(6)) + Style.space(12)

  Item {
    anchors.fill: parent
    // Same pulse as Omarchy's tailscale panel (panels/tailscale/Panel.qml).
    SequentialAnimation on opacity {
      running: skeleton.visible
      loops: Animation.Infinite
      NumberAnimation { from: 0.5; to: 1; duration: 700; easing.type: Easing.InOutQuad }
      NumberAnimation { to: 0.5; duration: 700; easing.type: Easing.InOutQuad }
    }

    Row {
      id: chips
      spacing: Style.space(4)
      Repeater {
        model: skeleton.cards
        delegate: Rectangle { width: Style.space(64); height: Style.space(18); radius: height / 2; color: skeleton.host.faint }
      }
    }

    Row {
      anchors { top: chips.bottom; topMargin: skeleton.host.gap; bottom: parent.bottom }
      spacing: skeleton.host.gap
      Repeater {
        model: skeleton.cards
        delegate: Rectangle {
          required property int modelData
          width: skeleton.host.columnWidth; height: parent.height
          radius: Style.space(8)
          color: Qt.rgba(skeleton.fg.r, skeleton.fg.g, skeleton.fg.b, 0.035)
          border { width: 1; color: Qt.rgba(skeleton.fg.r, skeleton.fg.g, skeleton.fg.b, 0.08) }
          Column {
            x: Style.space(6); y: Style.space(6)
            width: parent.width - Style.space(12)
            spacing: Style.space(6)
            Rectangle { width: parent.width * 0.45; height: Style.space(12); radius: height / 2; color: skeleton.host.faint }
            Repeater {
              model: modelData
              delegate: Rectangle {
                width: parent.width; height: skeleton.cardHeight; radius: Style.space(6)
                color: Qt.rgba(skeleton.fg.r, skeleton.fg.g, skeleton.fg.b, 0.05)
                border { width: 1; color: Qt.rgba(skeleton.fg.r, skeleton.fg.g, skeleton.fg.b, 0.1) }
              }
            }
          }
        }
      }
    }
  }

  BoardText {
    anchors.centerIn: parent
    text: "Loading GitLab issues…"
    color: skeleton.host.foreground
  }
}
