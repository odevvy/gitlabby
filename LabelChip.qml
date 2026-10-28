import QtQuick

// A label as a Pill in its GitLab color; plain theme pill if the color is unknown.
Pill {
  required property var host
  required property string name
  readonly property var style: host.labelStyle(name)
  label: name
  color: style ? style.bg : "transparent"
  textColor: style ? style.fg : host.dim
  border.color: style ? style.bg : host.faint
}
