import QtQuick
import qs.Commons
import qs.Commons as Commons
// Stand-in bar button: glyph text, pressed(button) on click.
Item {
  id: b
  property var bar: null
  property string text: ""
  property string tooltipText: ""
  readonly property bool hovered: mouse.containsMouse
  signal pressed(int buttonCode)
  signal clicked()
  implicitWidth: 28; implicitHeight: 28
  Text { anchors.centerIn: parent; text: b.text; color: Commons.Color.foreground; font.family: Style.font.family; font.pixelSize: 14 }
  MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.AllButtons
    onClicked: function(m) { b.pressed(m.button); b.clicked() } }
}
