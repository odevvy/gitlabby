import QtQuick
import qs.Commons
import "Logic.js" as Logic
import "components"

// To-do (v177 design A): his pending GitLab to-dos, each with why in a few
// words (mentioned you, review requested, pipeline failed, ...), then the open
// issues assigned to him with their column on this board when known.
// Read-only: a row only opens its item as Open links in says; a right-click or
// y copies its link. The lists and their chrome are a ScopedList over the
// shared service's todos (a ScopedFetch), asked for when this view opens, its
// scope changes, or r; never on popup open or a timer. t toggles it. The first
// load (or an error) is one LoadingRow, as the project picker shows.
ScopedList {
  id: view
  fetch: host.feed.todos
  names: ({ tab: "todoScopeTab", underline: "", count: "todoCount", row: "todoRow", bar: "todoFocusBar" })
  sections: function(a) {
    return [["todos", "To-dos", a.todos, "No pending to-dos.", Logic.listCaps.todos],
            ["assigned", "Assigned to you", a.assigned, "No open issues assigned to you.", Logic.listCaps.assigned]]
  }
  function refSign(r) { return r.kind === "mr" ? "!" : "#" }
  copySign: refSign
  // The header shows a reload of lists already on screen; the first load is
  // the spinner row only.
  busy: loading && answer !== null

  // The first load: a spinner row; an error or sign-in: the same row, still.
  messageShown: !view.answer ? view.loading : view.answer.state !== "ready"
  message: Component {
    LoadingRow {
      objectName: "todoLoading"
      host: view.host
      spinning: view.loading
      text: !view.answer ? "Loading your to-dos\u2026"
        : view.answer.message + (view.loading ? "" : "  Press r to try again.")
    }
  }

  rowContent: Component {
    Column {
      id: rowBox
      readonly property var row: parent ? parent.row : ({})
      readonly property bool isTodo: parent ? parent.section === "todos" : false
      readonly property var reason: isTodo ? Logic.todoAction(row) : { text: Logic.issueColumn(row, view.host.project, view.host.columns), color: "", glyph: "\uf06a" }
      spacing: Style.space(2)
      Item {
        width: parent.width; implicitHeight: Math.max(title.implicitHeight, right.implicitHeight)
        BoardText {
          objectName: "todoGlyph"
          anchors.verticalCenter: parent.verticalCenter
          text: rowBox.reason.glyph
          color: rowBox.reason.color !== "" ? rowBox.reason.color : view.host.dim
          font.pixelSize: Style.font.caption
        }
        BoardText {
          id: ref
          anchors { left: parent.left; leftMargin: Style.space(20); verticalCenter: parent.verticalCenter }
          text: rowBox.isTodo ? Logic.todoRef(rowBox.row) : "#" + rowBox.row.iid
          color: view.host.dim; font.pixelSize: Style.font.bodySmall
        }
        BoardText {
          id: title
          anchors { left: ref.right; leftMargin: Style.space(6); right: right.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          text: rowBox.row.title || ""; elide: Text.ElideRight; font.pixelSize: Style.font.bodySmall
        }
        Row {
          id: right
          anchors { right: parent.right; verticalCenter: parent.verticalCenter }
          spacing: Style.space(8)
          BoardText {
            objectName: "todoReason"
            anchors.verticalCenter: parent.verticalCenter
            text: rowBox.reason.text
            color: rowBox.reason.color !== "" ? rowBox.reason.color : view.host.dim
            font.pixelSize: Style.font.caption
          }
          BoardText {
            anchors.verticalCenter: parent.verticalCenter
            width: Style.space(34); horizontalAlignment: Text.AlignRight
            text: Logic.age(rowBox.isTodo ? rowBox.row.at : rowBox.row.updatedAt); color: view.host.quiet; font.pixelSize: Style.font.caption
          }
        }
      }
      BoardText {
        objectName: "todoSubline"
        leftPadding: Style.space(20)
        width: parent.width
        text: rowBox.isTodo ? Logic.todoSubline(rowBox.row) : Logic.issueSubline(rowBox.row)
        elide: Text.ElideRight
        color: view.host.quiet; font.pixelSize: Style.font.caption
      }
    }
  }
}
