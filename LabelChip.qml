import QtQuick
import "Logic.js" as Logic

// A label as a Pill in its GitLab color; plain theme pill if the color is unknown.
Pill {
  required property var host
  required property string name
  property var colors: host.labelColors
  readonly property var style: Logic.labelStyle(colors[name])
  label: name
  color: style ? style.bg : "transparent"
  textColor: style ? style.fg : host.dim
  border.color: style ? style.bg : host.faint
}
