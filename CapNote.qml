import QtQuick
import qs.Commons
import "components"

// The board read only its first 500 open issues (board-fetch open_cap), so the
// popup's card count stays bounded. One line at the top of the popup says so
// and opens the board on GitLab (openSeeAll) through the host-checked openUrl.
// Below the cap it is not there at all.
Rectangle {
  id: note
  required property var host
  readonly property bool linked: host.openSeeAll !== ""
  visible: host.setup === "" && host.boardState === "ready" && host.openCapped
  implicitHeight: line.implicitHeight + Style.space(12)
  color: "transparent"
  radius: Style.space(6)
  border { width: 1; color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.25) }
  Row {
    id: line
    anchors { left: parent.left; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    BoardText { objectName: "capNoteText"; text: "First 500 open issues shown"; font.pixelSize: Style.font.bodySmall }
    BoardText {
      objectName: "capNoteLink"
      visible: note.linked
      text: " · View all on GitLab ↗"
      color: capMouse.containsMouse ? note.host.accent : note.host.foreground
      font.pixelSize: Style.font.bodySmall
      MouseArea { id: capMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: note.host.openUrl(note.host.openSeeAll) }
    }
  }
}
