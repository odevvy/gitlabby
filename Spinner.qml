import QtQuick
import qs.Commons
import qs.Commons as Commons

// Small busy spinner beside a "…ing" line, in the accent color. Omarchy 4.0.6
// has no spinner component; its Ui/Button.qml spins an icon glyph this way.
BoardText {
  id: spinner
  property bool running: false
  visible: running
  text: "\uf021"
  color: Commons.Color.accent
  font.pixelSize: Style.font.bodySmall
  RotationAnimation on rotation { running: spinner.running; loops: Animation.Infinite; from: 0; to: 360; duration: 900 }
}
