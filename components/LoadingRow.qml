import QtQuick
import qs.Commons

// One quiet loading line: the accent Spinner and a dim italic text beside it,
// as the project picker shows while its list loads. The picker and the issue
// view both use it, so the plugin has one loading look. With spinning off it
// is just the dim line (the picker's error).
Row {
  id: row
  required property var host
  property string text: "Loading…"
  property bool spinning: true
  spacing: Style.space(6)
  Spinner { id: spinner; running: row.spinning && row.visible; anchors.verticalCenter: label.verticalCenter }
  BoardText {
    id: label
    width: row.width - (spinner.visible ? spinner.width + row.spacing : 0); wrapMode: Text.Wrap
    text: row.text
    color: row.host.dim; font.italic: true
  }
}
