import QtQuick
import qs.Commons

// A button styled like Omarchy's ConfirmDialog buttons (Ui/ConfirmDialog.qml):
// the main one in the accent on a faint fill, the other a quiet outline;
// square, so it never reads as a label. small: the issue view's size.
Rectangle {
  id: button
  required property var host
  property string label: ""
  property bool main: false
  property bool small: false
  signal clicked()
  readonly property color fg: host.foreground
  readonly property bool lit: enabled && (main || mouse.containsMouse)
  implicitWidth: Math.max(Style.space(small ? 72 : 120), buttonText.implicitWidth + Style.space(small ? 24 : 32))
  implicitHeight: Style.space(small ? 28 : 34)
  opacity: enabled ? 1 : 0.5
  color: lit ? Qt.rgba(fg.r, fg.g, fg.b, 0.08) : "transparent"
  border { width: 1; color: lit ? host.accent : Qt.rgba(fg.r, fg.g, fg.b, 0.38) }
  BoardText {
    id: buttonText
    anchors.centerIn: parent
    text: button.label
    color: button.main && button.enabled ? button.host.accent : button.fg
    font { pixelSize: button.small ? Style.font.bodySmall : Style.font.body; bold: button.main }
  }
  MouseArea { id: mouse; anchors.fill: parent; enabled: button.enabled; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: button.clicked() }
}
