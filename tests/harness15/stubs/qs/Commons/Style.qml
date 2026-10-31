pragma Singleton
import QtQuick
// Stand-in for Omarchy 4.0.6 Commons/Style.qml: default tokens at scale 1.
QtObject {
  property int cornerRadius: 0
  property int gapsOut: 8
  property string fontFamily: "JetBrainsMono Nerd Font"
  function space(px) { return Math.round(px * 1.5) }
  function spaceReal(px) { return px * 1.5 }
  readonly property QtObject font: QtObject {
    readonly property string family: "JetBrainsMono Nerd Font"
    readonly property int caption: 15
    readonly property int bodySmall: 16
    readonly property int body: 18
    readonly property int subtitle: 20
    readonly property int title: 21
    readonly property int icon: 21
    readonly property int iconSmall: 16
  }
  readonly property QtObject spacing: QtObject {
    readonly property int sm: 6
    readonly property int popupPadding: 21
    readonly property int controlPaddingX: 15  // Omarchy defaults (Commons/Style.qml)
    readonly property int inputPaddingY: 10
  }
}
