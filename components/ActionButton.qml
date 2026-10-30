import QtQuick
import qs.Commons

// A button styled like Omarchy's ConfirmDialog buttons (Ui/ConfirmDialog.qml):
// the main one in the accent on a faint fill, the other a quiet outline;
// square, so it never reads as a label. small: the issue view's size.
// danger: the urgent color, for a step that can't be taken back (Sign out).
Rectangle {
  id: button
  required property var host
  property string label: ""
  property bool main: false
  property bool small: false
  property bool danger: false
  readonly property bool hovered: mouse.containsMouse  // for a tooltip
  signal clicked()
  readonly property color fg: host.foreground
  readonly property color tone: danger ? host.urgent : host.accent
  readonly property bool lit: enabled && (main || mouse.containsMouse)
  implicitWidth: Math.max(Style.space(small ? 72 : 120), buttonText.implicitWidth + Style.space(small ? 24 : 32))
  implicitHeight: Style.space(small ? 28 : 34)
  opacity: enabled ? 1 : 0.5
  color: lit ? Qt.rgba(fg.r, fg.g, fg.b, 0.08) : "transparent"
  border { width: 1; color: lit || danger ? tone : Qt.rgba(fg.r, fg.g, fg.b, 0.38) }
  BoardText {
    id: buttonText
    anchors.centerIn: parent
    text: button.label
    color: button.danger ? button.tone : button.main && button.enabled ? button.tone : button.fg
    font { pixelSize: button.small ? Style.font.bodySmall : Style.font.body; bold: button.main }
  }
  MouseArea { id: mouse; anchors.fill: parent; enabled: button.enabled; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: button.clicked() }
}
