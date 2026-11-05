pragma Singleton
import QtQuick
// Stand-in for Omarchy 4.0.6 Commons/Style.qml. scale 1 is the default; the
// harness sets Style.scale = 1.5 (OGB_SCALE) for the screenshot tests that
// used to live under tests/harness15/.
QtObject {
  id: style
  property real scale: 1
  property int cornerRadius: 0
  property int gapsOut: Math.round(5 * scale)
  property string fontFamily: "JetBrainsMono Nerd Font"
  function space(px) { return Math.round(px * scale) }
  function spaceReal(px) { return px * scale }
  readonly property QtObject font: QtObject {
    readonly property string family: "JetBrainsMono Nerd Font"
    readonly property int caption: Math.round(10 * style.scale)
    readonly property int bodySmall: Math.round(11 * style.scale)
    readonly property int body: Math.round(12 * style.scale)
    readonly property int subtitle: Math.round(13 * style.scale)
    readonly property int title: Math.round(14 * style.scale)
    readonly property int icon: Math.round(14 * style.scale)
    readonly property int iconSmall: Math.round(11 * style.scale)
  }
  readonly property QtObject spacing: QtObject {
    readonly property int sm: Math.round(4 * style.scale)
    readonly property int popupPadding: Math.round(14 * style.scale)
    readonly property int controlPaddingX: Math.round(10 * style.scale)  // Omarchy defaults (Commons/Style.qml)
    readonly property int inputPaddingY: Math.round(7 * style.scale)
  }
}
