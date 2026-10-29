import QtQuick
import qs.Commons
import qs.Ui

// Who is busy, per bot, from the board on screen (Logic.botStates; no GitLab
// call). Filled dot: working; hollow accent dot: waiting (only approved or
// review); dim: idle. The first few issue numbers follow (hover: the title;
// click: open the issue), then "+N more" (hover: the rest). Shown only when
// settings.bots has an entry for this project. The height follows the Flow
// live (wrapping, refreshes, config edits); Board.qml makes it 0 when hidden.
Item {
  id: row
  required property var host
  property var states: []
  readonly property int shown: 5  // issue numbers per bot before "+N more"
  implicitHeight: flow.implicitHeight + Style.space(10)
  // A tooltip's x under item, kept inside the row (so inside the popup card).
  function tipX(item, width) {
    var at = item.mapToItem(row, 0, 0).x
    return Math.max(-at, Math.min(0, row.width - at - width))
  }

  Flow {
    id: flow
    width: parent.width
    spacing: Style.space(6)  // between wrapped lines too; bots get rightPadding
    Repeater {
      model: row.states
      delegate: Row {
        id: bot
        required property var modelData
        readonly property bool busy: modelData.state !== "idle"
        readonly property var rest: modelData.issues.slice(row.shown)
        spacing: Style.space(6)
        rightPadding: Style.space(12)
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
          model: bot.modelData.issues.slice(0, row.shown)
          delegate: BoardText {
            id: ref
            required property var modelData
            required property int index
            text: (index > 0 ? "· " : "") + "#" + modelData.iid + (bot.modelData.byList ? "" : " " + modelData.list)
            color: refMouse.containsMouse ? row.host.accent : row.host.dim
            font.pixelSize: Style.font.bodySmall
            MouseArea { id: refMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: row.host.openIssue(ref.modelData.row) }
            PanelToolTip {
              y: parent.height + Style.space(4); visible: refMouse.containsMouse
              text: "#" + ref.modelData.iid + " " + String(ref.modelData.row.title || "")
              onAboutToShow: x = row.tipX(parent, implicitWidth)
            }
          }
        }
        BoardText {
          id: more
          visible: bot.rest.length > 0
          text: "+" + bot.rest.length + " more"
          color: moreMouse.containsMouse ? row.host.accent : row.host.dim
          font { pixelSize: Style.font.bodySmall; underline: moreMouse.containsMouse }
          MouseArea { id: moreMouse; anchors.fill: parent; hoverEnabled: true }
          PanelToolTip {
            y: parent.height + Style.space(4)  // below: the row sits at the top of the popup
            onAboutToShow: x = row.tipX(parent, implicitWidth)
            visible: moreMouse.containsMouse
            text: bot.rest.map(function(i) { return "#" + i.iid + (bot.modelData.byList ? "" : " " + i.list) + "  " + String(i.row.title || "") }).join("\n")
          }
        }
      }
    }
  }
  Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: row.host.faint }
}
