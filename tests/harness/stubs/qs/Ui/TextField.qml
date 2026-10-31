import QtQuick
import QtQuick.Controls.Basic as B
import qs.Commons
import qs.Commons as Commons
// Stand-in for Ui/TextField.qml: a Controls TextField with the kit's colours.
B.TextField {
  id: root
  property color foreground: Commons.Color.foreground
  property color accent: Commons.Color.accent
  property bool password: false
  property bool hasCursor: false
  // Like the real one: padding from these plus its 1px border.
  property real horizontalPadding: Style.spacing.controlPaddingX
  property real verticalPadding: Style.spacing.inputPaddingY
  leftPadding: horizontalPadding + 1; rightPadding: horizontalPadding + 1
  topPadding: verticalPadding + 1; bottomPadding: verticalPadding + 1
  echoMode: password ? TextInput.Password : TextInput.Normal
  color: foreground
  placeholderTextColor: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.45)
  font.family: Style.font.family; font.pixelSize: Style.font.body
  background: Rectangle { radius: 4; color: "transparent"; border.width: 1; border.color: root.activeFocus ? root.accent : Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.25) }
}
