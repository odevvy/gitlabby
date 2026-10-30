import QtQuick
import qs.Commons

// Small square glyph button in a view's top row: ✕ back to the board, ‹ back a
// picker step. Hover fills it, like the clear button in Omarchy's weather panel.
// Sized like Omarchy's PanelActionButton (Ui/PanelActionButton.qml: 22 px or
// the icon font plus small spacing); the click area reaches a little past it.
// tip: its IconTip, e.g. "Back to the board (Esc)".
Rectangle {
  id: button
  required property var host
  property alias glyph: glyphText.text
  property string tip: ""
  readonly property alias hovered: mouse.containsMouse
  signal clicked()

  implicitWidth: Math.max(Style.space(22), Style.font.icon + Style.spacing.sm * 2); implicitHeight: implicitWidth
  radius: Style.space(4)
  color: hovered ? host.faint : "transparent"
  BoardText { id: glyphText; anchors.centerIn: parent; color: button.hovered ? button.host.foreground : button.host.dim; font.pixelSize: Style.font.icon }
  MouseArea { id: mouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: button.clicked() }
  IconTip { host: button.host; shown: button.hovered; text: button.tip }
}
