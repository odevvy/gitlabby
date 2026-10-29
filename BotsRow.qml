import QtQuick
import qs.Commons

// Who is busy, per bot, from the board on screen (Logic.botStates; no GitLab
// call). Filled dot: working; hollow accent dot: waiting (only approved or
// review); dim: idle. Each issue number opens that issue. Shown only when
// settings.bots has an entry for this project.
Item {
  id: row
  required property var host
  property var states: []
  implicitHeight: flow.implicitHeight + Style.space(10)

  Flow {
    id: flow
    width: parent.width
    spacing: Style.space(18)
    Repeater {
      model: row.states
      delegate: Row {
        id: bot
        required property var modelData
        readonly property bool busy: modelData.state !== "idle"
        spacing: Style.space(6)
        Rectangle {
          y: (bot.height - height) / 2
          width: Style.space(8); height: width; radius: width / 2
          color: bot.modelData.state === "working" ? row.host.accent : "transparent"
          border { width: 1; color: bot.busy ? row.host.accent : row.host.dim }
        }
        BoardText {
          text: bot.modelData.name
          color: bot.busy ? row.host.foreground : row.host.dim
          font { pixelSize: Style.font.bodySmall; bold: bot.busy }
        }
        BoardText {
          visible: !bot.busy
          text: "idle"
          color: row.host.dim
          font { pixelSize: Style.font.bodySmall; italic: true }
        }
        Repeater {
          model: bot.modelData.issues
          delegate: BoardText {
            id: ref
            required property var modelData
            required property int index
            text: (index > 0 ? "· " : "") + "#" + modelData.iid + (bot.modelData.byList ? "" : " " + modelData.list)
            color: refMouse.containsMouse ? row.host.accent : row.host.dim
            font.pixelSize: Style.font.bodySmall
            MouseArea { id: refMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: row.host.openIssue(ref.modelData.row) }
          }
        }
      }
    }
  }
  Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: row.host.faint }
}
