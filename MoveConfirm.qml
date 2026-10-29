import QtQuick
import qs.Commons
import "Logic.js" as Logic

// Asks before a card move on a project in settings.confirmMoves: which issue,
// from which list to which, what it changes on GitLab. Move (or Enter) goes
// ahead; Cancel (or Escape) leaves the card where it is.
Rectangle {
  id: confirm
  required property var host
  property var pending: null
  implicitHeight: column.implicitHeight + Style.space(20)
  color: "transparent"
  border { width: 1; color: host.accent }
  Column {
    id: column
    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: Style.space(10) }
    spacing: Style.space(8)
    BoardText {
      width: parent.width; wrapMode: Text.Wrap
      text: confirm.pending ? "Move #" + confirm.pending.row.iid + " from " + confirm.pending.from.name + " to " + confirm.pending.to.name + "?" : ""
      font.bold: true
    }
    BoardText {
      width: parent.width; wrapMode: Text.Wrap
      text: confirm.pending ? Logic.moveNote(confirm.pending.from, confirm.pending.to) : ""
      color: confirm.host.dim; font.pixelSize: Style.font.bodySmall
    }
    Row {
      spacing: Style.space(8)
      ActionButton { host: confirm.host; small: true; main: true; label: "Move"; onClicked: confirm.host.confirmMove() }
      ActionButton { host: confirm.host; small: true; label: "Cancel"; onClicked: confirm.host.cancelMove() }
    }
  }
}
