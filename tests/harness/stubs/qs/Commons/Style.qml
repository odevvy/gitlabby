pragma Singleton
import QtQuick
// Stand-in for Omarchy 4.0.6 Commons/Style.qml: default tokens at scale 1.
QtObject {
  property int cornerRadius: 0
  property int gapsOut: 5
  property string fontFamily: "JetBrainsMono Nerd Font"
  function space(px) { return Math.round(px) }
  function spaceReal(px) { return px }
  readonly property QtObject font: QtObject {
    readonly property string family: "JetBrainsMono Nerd Font"
    readonly property int caption: 10
    readonly property int bodySmall: 11
    readonly property int body: 12
    readonly property int subtitle: 13
    readonly property int title: 14
    readonly property int icon: 14
    readonly property int iconSmall: 11
  }
  readonly property QtObject spacing: QtObject {
    readonly property int sm: 4
    readonly property int popupPadding: 14
    readonly property int controlPaddingX: 10  // Omarchy defaults (Commons/Style.qml)
    readonly property int inputPaddingY: 7
  }
}
