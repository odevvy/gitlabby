import QtQuick
import qs.Commons
import "../Logic.js" as Logic

// The head pipeline of a Review card's merge request (board-fetch adds it):
// a status glyph in its color; hovering says which, a click opens the pipeline
// on GitLab. No pipeline (or one GitLab gave no https link for): no click.
BoardText {
  id: mark
  required property var host
  property var pipeline: null
  readonly property var info: Logic.pipelineMark(pipeline)
  visible: info !== null
  text: info ? info.glyph : ""
  color: info ? info.color : "transparent"
  font.pixelSize: Style.font.bodySmall
  MouseArea {
    id: mouse; anchors.fill: parent; anchors.margins: -Style.space(3)
    enabled: mark.visible; hoverEnabled: true
    cursorShape: mark.info && mark.info.url !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor
    onClicked: if (mark.info && mark.info.url !== "") mark.host.openUrl(mark.info.url)
  }
  IconTip { host: mark.host; shown: mouse.containsMouse; text: mark.info ? mark.info.tip : "" }
}
