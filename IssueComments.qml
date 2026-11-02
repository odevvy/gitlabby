import QtQuick
import QtQuick.Controls
import qs.Commons
import "Logic.js" as Logic
import "components"

// The issue view's comments: the count, the thread, the box and Post.
// IssueView.qml (owner) keeps the notes, their loading and post(); this file
// draws them and hands the box back to it.
Column {
  id: comments
  required property Item owner  // the IssueView
  property alias box: box
  spacing: Style.space(8)

  Rectangle { width: parent.width; height: 1; color: owner.host.faint }

  Row {
    spacing: Style.space(6)
    BoardText {
      text: "Comments" + (owner.notes.length > 0 ? " · " + owner.notes.length : "")
      color: owner.host.dim
      font { pixelSize: Style.font.bodySmall; bold: true }
    }
  }
  BoardText {
    width: parent.width; wrapMode: Text.Wrap
    visible: text !== ""
    text: owner.notesError !== "" ? owner.notesError
      : owner.notesLoading && owner.notes.length === 0 ? ""
      : owner.notes.length === 0 ? "No comments yet."
      : owner.more ? "Showing the latest 100 notes. Older ones are on GitLab." : ""
    color: owner.notesError !== "" ? owner.host.urgent : owner.host.dim
    font.italic: true
  }
  // Still waiting for the comments once the description is in: the one
  // loading row (the issue view's), here.
  LoadingRow {
    objectName: "notesLoading"
    width: parent.width; host: owner.host
    visible: owner.waited && owner.described && owner.notesReadyFor !== owner.key && owner.notes.length === 0
  }

  Repeater {
    model: owner.notes
    delegate: Row {
      id: note
      required property var modelData
      NumberAnimation on opacity { from: 0; to: 1; duration: 150 }
      width: parent.width
      spacing: Style.space(8)
      Avatar { host: owner.host; person: note.modelData.author || ({}) }
      Column {
        width: note.width - Style.space(18) - note.spacing
        spacing: Style.space(2)
        BoardText {
          textFormat: Text.StyledText
          text: Logic.escaped((note.modelData.author || {}).username || "?")
            + "&nbsp; <font color='" + owner.host.dim + "'>" + Logic.age(note.modelData.createdAt, owner.notesAt) + "</font>"
          font { pixelSize: Style.font.bodySmall; bold: true }
        }
        BoardText {
          width: parent.width; wrapMode: Text.WrapAtWordBoundaryOrAnywhere
          text: String(note.modelData.body || "")
          font.pixelSize: Style.font.bodySmall
        }
      }
    }
  }

  TextArea {
    id: box
    width: parent.width
    enabled: owner.loaded && !owner.posting
    wrapMode: TextEdit.Wrap
    placeholderText: "Write a comment…  (Ctrl+Enter to post)"
    placeholderTextColor: owner.host.dim
    color: owner.host.foreground
    selectionColor: owner.host.accent
    selectedTextColor: owner.host.background
    font { family: Style.font.family; pixelSize: Style.font.bodySmall }
    padding: Style.space(8)
    background: Rectangle {
      implicitHeight: Style.space(64)
      radius: Style.space(6)
      color: "transparent"
      border { width: 1; color: box.activeFocus ? owner.host.accent : owner.host.faint }
    }
    Keys.onPressed: function(event) {
      if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && (event.modifiers & Qt.ControlModifier)) {
        owner.post(); event.accepted = true
      } else if (event.key === Qt.Key_Escape) {
        owner.host.showView("issue"); event.accepted = true  // hand the keys back to the panel
      }
    }
  }

  Item {
    width: parent.width
    implicitHeight: Math.max(postButton.implicitHeight, postStatus.implicitHeight)
    BoardText {
      id: postStatus
      // Its own width beside Post: it wraps, never runs under the button.
      anchors.verticalCenter: parent.verticalCenter
      width: parent.width - postButton.width - Style.space(12)
      wrapMode: Text.Wrap
      readonly property bool slash: Logic.quickAction(box.text)
      text: owner.postError !== "" ? owner.postError
        : slash ? "A line starts with /, which GitLab runs as a quick action, so this can't be posted. Wrap it in `backticks`."
        : "Posts as you. Lines starting with / aren't sent."
      color: owner.postError !== "" || slash ? owner.host.urgent : owner.host.dim
      font.pixelSize: Style.font.caption
    }
    ActionButton {
      id: postButton
      anchors { right: parent.right; verticalCenter: parent.verticalCenter }
      host: owner.host; small: true; main: true
      enabled: owner.loaded && !owner.posting && box.text.trim() !== "" && !postStatus.slash
      label: owner.posting ? "Posting…" : "Post"
      onClicked: owner.post()
    }
  }
}
