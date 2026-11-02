import QtQuick
import qs.Commons

// The bottom edge of a scrolling view fades into the popup's own background
// (the theme's) while there is more below, so a cut-off view reads as one
// that goes on. It fades away at the end and lets every click through.
// Place it beside the Flickable: ScrollHint { flick: flick; host: view.host }.
Rectangle {
  id: hint
  required property Flickable flick
  required property var host
  readonly property bool more: flick.contentHeight - flick.contentY - flick.height > 1
  readonly property color bg: host.background
  objectName: "scrollHint"
  anchors { left: flick.left; right: flick.right; bottom: flick.bottom }
  height: Style.space(48)
  opacity: more ? 1 : 0
  visible: opacity > 0
  Behavior on opacity { NumberAnimation { duration: 180 } }
  gradient: Gradient {
    GradientStop { position: 0; color: Qt.rgba(hint.bg.r, hint.bg.g, hint.bg.b, 0) }
    GradientStop { position: 1; color: hint.bg }
  }
}
