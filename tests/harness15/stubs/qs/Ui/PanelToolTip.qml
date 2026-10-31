import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Commons as Commons
// Stand-in for Ui/PanelToolTip.qml: a ToolTip like the real one (plain text,
// 400 ms delay), drawn simply.
ToolTip {
  id: tip
  property color panelForeground: Commons.Color.tooltip.text
  property color panelBackground: Commons.Color.tooltip.background
  property color panelBorder: Commons.Color.tooltip.border
  property string fontFamily: Style.font.family
  property real fontSize: Style.font.bodySmall
  delay: 400
  padding: 0
  background: Rectangle { color: tip.panelBackground; border.width: 1; border.color: tip.panelBorder; radius: 6 }
  contentItem: Text {
    textFormat: Text.PlainText
    text: tip.text; color: tip.panelForeground
    font.family: tip.fontFamily; font.pixelSize: tip.fontSize
    leftPadding: 8; rightPadding: 8; topPadding: 4; bottomPadding: 4
  }
}
