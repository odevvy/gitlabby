import QtQuick
import QtQuick.Controls
import qs.Commons
import "Logic.js" as Logic
import "components"

// To-do (v177 design A): his pending GitLab to-dos, each with why in a few
// words (mentioned you, review requested, pipeline failed, ...), then the open
// issues assigned to him with their column on this board when known.
// Read-only: a row only opens its item as Open links in says; a right-click or
// y copies its link. The lists come from the shared service
// (BoardService.requestTodos), asked for when this view opens, its scope
// changes, or r; never on popup open or a timer. t toggles it. Laid out as
// Merge requests; the first load (or an error) is one LoadingRow, as the
// project picker shows.
Item {
  id: view
  required property var host
  // "all" projects (the default), or "project": the board's project.
  property string mode: "all"
  readonly property string scope: mode === "project" && host.project !== "" ? host.project : "all"
  readonly property var entry: host.feed.todoAnswers[scope] || null
  readonly property var answer: entry ? entry.data : null
  readonly property bool loading: host.feed.todoRunning === scope
  readonly property var rows: answer && answer.state === "ready" ? answer.todos.concat(answer.assigned) : []
  property int cursor: 0
  // One flat list: headings, rows, and a line for an empty section.
  readonly property var items: {
    if (!answer || answer.state !== "ready") return []
    var out = [], n = 0
    ;[["todos", "To-dos", answer.todos, "No pending to-dos."],
      ["assigned", "Assigned to you", answer.assigned, "No open issues assigned to you."]].forEach(function(s) {
      out.push({ kind: "head", title: s[1], count: s[2].length })
      if (s[2].length === 0) out.push({ kind: "empty", text: s[3] })
      s[2].forEach(function(r) { out.push({ kind: "row", section: s[0], row: r, index: n++ }) })
    })
    return out
  }

  function open() { cursor = 0; host.feed.requestTodos(scope, false) }
  function refresh() { host.feed.requestTodos(scope, true) }
  function setMode(next) { if (next !== mode) { mode = next; cursor = 0 } }
  onScopeChanged: if (visible) host.feed.requestTodos(scope, false)
  onRowsChanged: cursor = Math.max(0, Math.min(cursor, rows.length - 1))
  function moveCursor(dy) {
    if (rows.length === 0) return
    cursor = Math.max(0, Math.min(rows.length - 1, cursor + dy))
    for (var i = 0; i < list.count; i++) {
      var it = list.itemAt(i)
      if (it && it.rowIndex === cursor) {
        if (it.y < flick.contentY) flick.contentY = it.y
        else if (it.y + it.height > flick.contentY + flick.height) flick.contentY = it.y + it.height - flick.height
      }
    }
  }
  function activate() { if (rows[cursor]) host.openUrl(rows[cursor].url) }
  function copyCurrent() { var r = rows[cursor]; return r ? host.copyLink(r, refSign(r)) : false }
  function refSign(r) { return r.kind === "mr" ? "!" : "#" }

  implicitHeight: top.implicitHeight + Style.space(10) + body.implicitHeight

  Item {
    id: top
    width: parent.width
    implicitHeight: tabs.implicitHeight
    // The scope: two text tabs, the current one underlined in the accent.
    Row {
      id: tabs
      anchors { right: parent.right; verticalCenter: parent.verticalCenter }
      spacing: Style.space(14)
      Repeater {
        model: [{ mode: "all", label: "All projects" }, { mode: "project", label: "This project" }]
        delegate: Item {
          id: tab
          objectName: "todoScopeTab"
          required property var modelData
          readonly property string label: modelData.label
          readonly property bool on: view.mode === modelData.mode
          visible: modelData.mode === "all" || view.host.project !== ""
          implicitWidth: tabText.implicitWidth
          implicitHeight: tabText.implicitHeight + Style.space(6)
          BoardText {
            id: tabText
            anchors.top: parent.top
            text: tab.label
            color: tab.on ? view.host.foreground : tabMouse.containsMouse ? view.host.dim : view.host.quiet
            font.pixelSize: Style.font.bodySmall
          }
          Rectangle {
            visible: tab.on
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 2; radius: 1
            color: view.host.accent
          }
          MouseArea { id: tabMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: view.setMode(tab.modelData.mode) }
        }
      }
    }
  }

  Flickable {
    id: flick
    anchors { top: top.bottom; topMargin: Style.space(10); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentHeight: body.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: body
      width: flick.width
      spacing: Style.space(2)
      // The first load: a spinner row; an error or sign-in: the same row, still.
      LoadingRow {
        objectName: "todoLoading"
        host: view.host
        visible: !view.answer ? view.loading : view.answer.state !== "ready"
        width: parent.width
        spinning: view.loading
        text: !view.answer ? "Loading your to-dos\u2026"
          : view.answer.message + (view.loading ? "" : "  Press r to try again.")
      }
      Repeater {
        id: list
        model: view.items
        delegate: Item {
          id: item
          required property var modelData
          readonly property int rowIndex: modelData.kind === "row" ? modelData.index : -1
          width: body.width
          implicitHeight: modelData.kind === "head" ? headRow.implicitHeight + (modelData.title === "Assigned to you" ? Style.space(14) : 0)
            : modelData.kind === "empty" ? emptyText.implicitHeight + Style.space(6)
            : rowBox.implicitHeight

          Row {
            id: headRow
            visible: item.modelData.kind === "head"
            anchors.bottom: parent.bottom
            spacing: Style.space(6)
            BoardText { text: item.modelData.title || ""; color: view.host.dim; font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 } }
            BoardText { objectName: "todoCount"; text: String(item.modelData.count || 0); color: view.host.quiet; font.pixelSize: Style.font.caption }
          }
          BoardText {
            id: emptyText
            visible: item.modelData.kind === "empty"
            anchors.verticalCenter: parent.verticalCenter
            text: item.modelData.text || ""
            color: view.host.quiet
            font.pixelSize: Style.font.bodySmall
          }
          Rectangle {
            id: rowBox
            objectName: "todoRow"
            visible: item.modelData.kind === "row"
            readonly property var row: item.modelData.row || ({})
            readonly property bool isTodo: item.modelData.section === "todos"
            readonly property bool current: item.rowIndex === view.cursor
            readonly property var reason: isTodo ? Logic.todoAction(row) : { text: Logic.issueColumn(row, view.host.project, view.host.columns), color: "", glyph: "\uf06a" }
            anchors { left: parent.left; right: parent.right }
            implicitHeight: lines.implicitHeight + Style.space(10)
            radius: Style.space(6)
            color: current ? Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, 0.05) : "transparent"
            Rectangle {
              objectName: "todoFocusBar"
              visible: rowBox.current
              anchors { left: parent.left; verticalCenter: parent.verticalCenter }
              width: 2; height: parent.height - Style.space(12); radius: 1
              color: view.host.accent
            }
            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: rowBox.row.url ? Qt.PointingHandCursor : Qt.ArrowCursor
              onEntered: view.cursor = item.rowIndex
              // A right-click copies its link (Board.copyLink); a click opens it.
              acceptedButtons: Qt.LeftButton | Qt.RightButton
              onClicked: function(mouse) { if (mouse.button === Qt.RightButton) view.host.copyLink(rowBox.row, view.refSign(rowBox.row)); else view.host.openUrl(rowBox.row.url) }
            }
            Column {
              id: lines
              anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: Style.space(8); rightMargin: Style.space(8) }
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
      }
    }
  }
}
