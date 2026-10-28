import QtQuick
import qs.Commons

// Small square glyph button in a view's top row: ✕ back to the board, ‹ back a
// picker step. Hover fills it, like the clear button in Omarchy's weather panel.
Rectangle {
  id: button
  required property var host
  property alias glyph: glyphText.text
  readonly property alias hovered: mouse.containsMouse
  signal clicked()

  implicitWidth: Style.space(22); implicitHeight: implicitWidth
  radius: Style.space(4)
  color: hovered ? host.faint : "transparent"
  BoardText { id: glyphText; anchors.centerIn: parent; color: button.hovered ? button.host.foreground : button.host.dim; font.pixelSize: Style.font.body }
  MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: button.clicked() }
}
