import QtQuick
import qs.Commons
import "Logic.js" as Logic
import "components"

// Says why writes are off on this project (Board.qml accessNote) and, when
// the account is view-only there, how to sign glab in with a token that can
// only read: the server's own token page (https, read_api prefilled), then
// glab auth login in a terminal. This plugin never asks for, stores or shows a
// token. Not now hides it for this project (settings.accessHintDismissed).
Rectangle {
  id: hint
  required property var host
  readonly property var words: Logic.accessHint(host.accessNote, host.accessEntry, host.project, host.gitlabHost)
  visible: host.view === "board" && host.setup === "" && host.boardState === "ready" && host.accessNote !== "" && !host.hintDismissed
  implicitHeight: column.implicitHeight + Style.space(20)
  color: "transparent"
  radius: Style.space(6)
  border { width: 1; color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.25) }
  Column {
    id: column
    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: Style.space(10) }
    spacing: Style.space(6)
    Row {
      width: parent.width; spacing: Style.space(8)
      BoardText { id: lock; text: "\uf023"; color: hint.host.dim; font.pixelSize: Style.font.bodySmall }
      BoardText {
        objectName: "accessTitle"
        width: parent.width - lock.width - parent.spacing; wrapMode: Text.Wrap
        text: hint.words.title; font { pixelSize: Style.font.bodySmall; bold: true }
      }
    }
    BoardText {
      objectName: "accessBody"
      width: parent.width; wrapMode: Text.Wrap
      text: hint.words.body; color: hint.host.dim; font.pixelSize: Style.font.bodySmall
    }
    Row {
      spacing: Style.space(8)
      ActionButton {
        objectName: "accessTokenPage"
        visible: hint.words.link; host: hint.host; small: true; main: true
        label: "Open GitLab's token page"
        onClicked: hint.host.openUrl(Logic.patUrl(hint.host.gitlabHost))
      }
      ActionButton { objectName: "accessNotNow"; host: hint.host; small: true; label: "Not now"; onClicked: hint.host.dismissHint() }
      BoardText {
        anchors.verticalCenter: parent.verticalCenter; leftPadding: Style.space(6)
        text: "This plugin never asks for, stores or shows a token."
        color: hint.host.dim; font.pixelSize: Style.font.caption
      }
    }
  }
}
