import QtQuick
import qs.Commons

// Keyboard focus for a custom control (Tab / Shift+Tab, v0.1.103). Put one
// inside the control: it adds the control to the host's tab order and draws
// the accent outline while the control holds focus. Enter or Space then runs
// the control's kbActivate() if it has one, else its clicked().
Rectangle {
  id: ring
  objectName: "focusRing"
  required property var host
  property Item target: parent
  property real inset: -Style.space(2)
  readonly property bool on: !!host && host.kbFocus === target
  anchors.fill: target
  anchors.margins: inset
  visible: on
  z: 100
  color: "transparent"
  radius: Style.space(6)
  border { width: Math.max(2, Style.space(2)); color: host ? host.accent : "transparent" }
  Component.onCompleted: if (host && target) host.addFocusable(target)
  Component.onDestruction: if (host && target) host.removeFocusable(target)
}
