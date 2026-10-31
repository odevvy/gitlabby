import QtQuick
import qs.Commons
import "components"

// The issue view's label editor: a filter with Done, then the labels the issue
// could take. IssueView.qml (owner) keeps the labels, their loading and every
// change (relabel); this file draws the editor and hands picks back to it.
Column {
  id: editor
  required property Item owner  // the IssueView
  readonly property Item field: labelPicker.field
  visible: owner.editing
  spacing: Style.space(6)

  LabelPicker {
    id: labelPicker
    width: parent.width
    host: owner.host; colors: owner.colors
    options: owner.addable; shown: owner.addableShown
    labelsState: owner.labelsState
    error: owner.labelError !== "" ? owner.labelError : owner.labelsState === "error" ? owner.labelsError : ""
    busyText: owner.labelBusy !== "" ? "Saving " + owner.labelBusy + "…" : ""
    busyName: owner.labelBusy
    onPicked: function(name) { owner.relabel("add", name) }
    onEscaped: owner.doneEditing()
    ActionButton {
      id: doneButton
      host: owner.host; small: true
      height: labelPicker.field.height
      label: "Done"
      onClicked: owner.doneEditing()
    }
  }
  BoardText {
    width: parent.width; wrapMode: Text.Wrap
    text: "Board list labels change only by dragging the card."
    color: owner.host.dim; font.pixelSize: Style.font.caption
  }
}
