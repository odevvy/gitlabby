import QtQuick
import qs.Commons

// Quiet × inside a filter TextField. Same mark as the picker's close GlyphButton
// (\uf00d). Only while the field has text; click clears and keeps focus so the
// next keystrokes go into the field. Parent must be that TextField. Set the
// field's rightPadding to horizontalPadding + 1 + clear.reserve so typed text
// stops short of the mark.
Item {
  id: clear
  required property var host
  property string tip: "Clear"
  readonly property var field: parent
  // Space the field should add on the right while we show (glyph + gap).
  readonly property real reserve: visible ? width + Style.space(6) : 0

  objectName: "filterClear"
  visible: field && field.text.length > 0
  width: Math.max(Style.space(18), Style.font.icon)
  height: width
  anchors.right: parent.right
  anchors.rightMargin: field && field.horizontalPadding !== undefined ? field.horizontalPadding : Style.spacing.controlPaddingX
  anchors.verticalCenter: parent.verticalCenter
  z: 1

  BoardText {
    anchors.centerIn: parent
    text: "\uf00d"
    color: mouse.containsMouse ? clear.host.foreground : clear.host.dim
    font.pixelSize: Style.font.icon
  }
  MouseArea {
    id: mouse
    anchors.fill: parent
    anchors.margins: -Style.space(4)
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onClicked: {
      clear.field.clear()
      clear.field.forceActiveFocus()
    }
  }
  IconTip { host: clear.host; shown: mouse.containsMouse && clear.tip !== ""; text: clear.tip }
}
