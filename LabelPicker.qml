import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui

// Pick a project label: a compact filter (children go beside it, e.g. Done),
// the labels to choose from as chips, and one status line (red error, or a
// Spinner while busy). The filter is off until the labels have loaded. The
// owner filters `options` with `filter` and handles `picked`.
Column {
  id: picker
  required property var host
  property var colors: host.labelColors
  property var options: []        // [{ name, color, textColor }], already filtered
  property int shown: 60          // chips before "N more: filter to find them."
  property string labelsState: ""  // "", loading, ready, error
  property string error: ""        // shown in red; wins over the rest
  property string busyText: ""     // e.g. "Saving bug…", with the spinner
  property string busyName: ""     // the chip being saved; the others dim and wait
  property bool choose: false      // pick one (a check on `selected`) rather than add ("+ ")
  property string selected: ""
  property string emptyText: "No other labels to add."
  property alias filter: field.text
  readonly property alias field: field
  default property alias beside: row.data
  signal picked(string name)
  signal escaped()
  spacing: Style.space(6)

  Row {
    id: row
    spacing: Style.space(8)
    // Compact; off (dimmed) until the labels have loaded.
    TextField {
      id: field
      readonly property real besideWidth: {
        var w = 0
        for (var i = 0; i < row.children.length; i++) if (row.children[i] !== field) w += row.children[i].width + row.spacing
        return w
      }
      width: Math.min(picker.width - besideWidth, Style.space(220))
      enabled: picker.labelsState === "ready"
      opacity: enabled ? 1 : 0.5
      verticalPadding: Style.space(3)
      font.pixelSize: Style.font.bodySmall
      foreground: picker.host.foreground
      placeholderText: "Filter labels"
      onAccepted: if (picker.options.length > 0) picker.picked(picker.options[0].name)
      Keys.onEscapePressed: picker.escaped()
    }
  }
  Flow {
    width: parent.width; spacing: Style.space(4)
    visible: picker.options.length > 0
    Repeater {
      model: picker.options.slice(0, picker.shown)
      delegate: LabelChip {
        required property var modelData
        host: picker.host; colors: picker.colors; name: String(modelData.name)
        label: (!picker.choose ? "+ " : picker.selected === name ? "\uf00c  " : "") + name
        clickable: picker.busyName === ""
        opacity: picker.busyName === "" || picker.busyName === name ? 1 : 0.5
        onClicked: picker.picked(name)
      }
    }
  }
  Row {
    width: parent.width; spacing: Style.space(6)
    visible: status.text !== ""
    Spinner { id: spinner; running: status.busy; anchors.verticalCenter: status.verticalCenter }
    BoardText {
      id: status
      width: parent.width - (spinner.visible ? spinner.width + parent.spacing : 0); wrapMode: Text.Wrap
      readonly property bool bad: picker.error !== ""
      readonly property bool busy: !bad && (picker.busyText !== "" || picker.labelsState === "loading")
      text: picker.error !== "" ? picker.error
        : picker.busyText !== "" ? picker.busyText
        : picker.labelsState === "loading" ? "Loading labels…"
        : picker.labelsState !== "ready" ? ""
        : picker.options.length > picker.shown ? (picker.options.length - picker.shown) + " more: filter to find them."
        : picker.options.length === 0 ? (picker.filter.trim() !== "" ? "No label matches." : picker.emptyText)
        : ""
      color: bad ? picker.host.urgent : picker.host.dim
      font.pixelSize: Style.font.bodySmall
    }
  }
}
