import QtQuick
import QtQuick.Controls
import qs.Commons
import "Logic.js" as Logic
import "components"

// Open merge requests: waiting on his review (no drafts), then his own, with
// each one's pipeline, GitLab's merge status and every reviewer's state.
// Read-only: a row only opens the merge request in the browser. The lists come
// from the shared service (BoardService.requestMrs), asked for when this view
// opens, its scope changes, or r; never on a timer. m toggles it.
Item {
  id: view
  required property var host
  // "all" projects (the default), or "project": the board's project.
  property string mode: "all"
  readonly property string scope: mode === "project" && host.project !== "" ? host.project : "all"
  readonly property var entry: host.feed.mrAnswers[scope] || null
  readonly property var answer: entry ? entry.data : null
  readonly property bool loading: host.feed.mrRunning === scope
  readonly property var rows: answer && answer.state === "ready" ? answer.review.concat(answer.mine) : []
  property int cursor: 0
  // One flat list: headings, rows, and a line for an empty section.
  readonly property var items: {
    if (!answer || answer.state !== "ready") return []
    var out = [], n = 0
    ;[["review", "Waiting on your review", answer.review, "Nothing waiting on your review."],
      ["mine", "Yours", answer.mine, "No open merge requests of yours."]].forEach(function(s) {
      out.push({ kind: "head", title: s[1], count: s[2].length })
      if (s[2].length === 0) out.push({ kind: "empty", text: s[3] })
      s[2].forEach(function(r) { out.push({ kind: "row", section: s[0], row: r, index: n++ }) })
    })
    return out
  }

  function open() { cursor = 0; host.feed.requestMrs(scope, false) }
  function refresh() { host.feed.requestMrs(scope, true) }
  function setMode(next) { if (next !== mode) { mode = next; cursor = 0 } }
  onScopeChanged: if (visible) host.feed.requestMrs(scope, false)
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
  function stamp(ms) { return ms > 0 ? Qt.formatTime(new Date(ms), "HH:mm") : "" }

  implicitHeight: top.implicitHeight + Style.space(10) + body.implicitHeight + Style.space(10) + footer.implicitHeight

  Item {
    id: top
    width: parent.width
    implicitHeight: close.implicitHeight
    BoardText { id: heading; anchors.verticalCenter: parent.verticalCenter; text: "Merge requests"; font { pixelSize: Style.font.bodySmall; bold: true } }
    Row {
      anchors { left: heading.right; leftMargin: Style.space(14); verticalCenter: parent.verticalCenter }
      spacing: Style.space(4)
      Repeater {
        model: [{ mode: "all", label: "All projects" }, { mode: "project", label: "This project" }]
        delegate: Pill {
          required property var modelData
          readonly property bool on: view.mode === modelData.mode
          visible: modelData.mode === "all" || view.host.project !== ""
          label: modelData.label
          clickable: true
          textColor: on ? view.host.background : view.host.dim
          color: on ? view.host.accent : "transparent"
          onClicked: view.setMode(modelData.mode)
        }
      }
    }
    GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; tip: "Back to the board (Esc)"; onClicked: view.host.back() }
  }

  Flickable {
    id: flick
    anchors { top: top.bottom; topMargin: Style.space(10); left: parent.left; right: parent.right; bottom: footer.top; bottomMargin: Style.space(10) }
    contentHeight: body.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: body
      width: flick.width
      spacing: Style.space(2)
      BoardText {
        objectName: "mrsMessage"
        visible: !view.answer || view.answer.state !== "ready"
        width: parent.width
        wrapMode: Text.Wrap
        color: view.host.dim
        font.pixelSize: Style.font.bodySmall
        text: !view.answer ? (view.loading ? "Loading merge requests\u2026" : "")
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
          implicitHeight: modelData.kind === "head" ? headRow.implicitHeight + (modelData.title === "Yours" ? Style.space(14) : 0)
            : modelData.kind === "empty" ? emptyText.implicitHeight + Style.space(6)
            : mr.implicitHeight

          Row {
            id: headRow
            visible: item.modelData.kind === "head"
            anchors.bottom: parent.bottom
            spacing: Style.space(6)
            BoardText { text: item.modelData.title || ""; color: view.host.dim; font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 } }
            Pill { label: String(item.modelData.count || 0); color: view.host.faint; anchors.verticalCenter: parent.verticalCenter }
          }
          BoardText {
            id: emptyText
            visible: item.modelData.kind === "empty"
            leftPadding: Style.space(8)
            anchors.verticalCenter: parent.verticalCenter
            text: item.modelData.text || ""
            color: view.host.dim
            font.pixelSize: Style.font.bodySmall
          }
          Rectangle {
            id: mr
            objectName: "mrRow"
            visible: item.modelData.kind === "row"
            readonly property var row: item.modelData.row || ({ reviewers: [], author: {} })
            readonly property bool current: item.rowIndex === view.cursor
            readonly property var status: Logic.mrStatus(row)
            anchors { left: parent.left; right: parent.right }
            implicitHeight: lines.implicitHeight + Style.space(10)
            radius: Style.space(6)
            color: current ? view.host.faint : "transparent"
            border { width: current ? 1 : 0; color: Qt.rgba(view.host.accent.r, view.host.accent.g, view.host.accent.b, 0.6) }
            MouseArea {
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: mr.row.url ? Qt.PointingHandCursor : Qt.ArrowCursor
              onEntered: view.cursor = item.rowIndex
              onClicked: view.host.openUrl(mr.row.url)
            }
            Column {
              id: lines
              anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: Style.space(8); rightMargin: Style.space(8) }
              spacing: Style.space(2)
              Item {
                width: parent.width; implicitHeight: Math.max(title.implicitHeight, right.implicitHeight)
                PipelineMark { host: view.host; pipeline: mr.row.pipeline; anchors.verticalCenter: parent.verticalCenter }
                BoardText {
                  id: ref
                  anchors { left: parent.left; leftMargin: Style.space(20); verticalCenter: parent.verticalCenter }
                  text: "!" + mr.row.iid; color: view.host.dim; font.pixelSize: Style.font.bodySmall
                }
                BoardText {
                  id: title
                  anchors { left: ref.right; leftMargin: Style.space(6); right: right.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
                  text: mr.row.title || ""; elide: Text.ElideRight; font.pixelSize: Style.font.bodySmall
                }
                Row {
                  id: right
                  anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                  spacing: Style.space(8)
                  Pill {
                    objectName: "mrStatus"
                    visible: mr.status.text !== ""
                    anchors.verticalCenter: parent.verticalCenter
                    label: mr.status.text
                    textColor: mr.status.color !== "" ? mr.status.color : view.host.dim
                    border.color: mr.status.color !== "" ? mr.status.color : view.host.faint
                  }
                  Row {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: -Style.space(3)
                    Repeater {
                      model: (mr.row.reviewers || []).slice(0, 4)
                      delegate: Item {
                        id: rev
                        objectName: "reviewer"
                        required property var modelData
                        readonly property var mark: Logic.reviewerMark(modelData)
                        implicitWidth: face.implicitWidth; implicitHeight: face.implicitHeight
                        Avatar { id: face; host: view.host; person: rev.modelData }
                        Rectangle {
                          visible: rev.mark.glyph !== ""
                          anchors { right: parent.right; bottom: parent.bottom; rightMargin: -Style.space(3); bottomMargin: -Style.space(3) }
                          width: Style.space(11); height: width; radius: width / 2
                          color: rev.mark.color; border { width: 1; color: view.host.background }
                          BoardText { anchors.centerIn: parent; text: rev.mark.glyph; color: "#ffffff"; font.pixelSize: Style.space(7) }
                        }
                        MouseArea { id: revMouse; anchors.fill: parent; hoverEnabled: true; onClicked: view.host.openUrl(mr.row.url) }
                        IconTip { host: view.host; shown: revMouse.containsMouse; text: rev.mark.tip }
                      }
                    }
                  }
                  BoardText {
                    visible: (mr.row.reviewers || []).length > 4
                    anchors.verticalCenter: parent.verticalCenter
                    text: "+" + ((mr.row.reviewers || []).length - 4); color: view.host.dim; font.pixelSize: Style.font.caption
                  }
                  BoardText {
                    anchors.verticalCenter: parent.verticalCenter
                    width: Style.space(34); horizontalAlignment: Text.AlignRight
                    text: Logic.age(mr.row.updatedAt); color: view.host.dim; font.pixelSize: Style.font.caption
                  }
                }
              }
              BoardText {
                leftPadding: Style.space(20)
                width: parent.width
                text: Logic.mrSubline(mr.row, item.modelData.section)
                elide: Text.ElideRight
                color: view.host.dim; font.pixelSize: Style.font.caption
              }
            }
          }
        }
      }
    }
  }

  BoardText {
    id: footer
    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
    elide: Text.ElideRight
    color: view.host.dim
    font.pixelSize: Style.font.caption
    text: "Read-only  \u00b7  Enter opens it in GitLab  \u00b7  j/k move  \u00b7  r refreshes"
      + (view.loading && view.entry ? "  \u00b7  refreshing\u2026" : view.entry ? "  \u00b7  updated " + view.stamp(view.entry.startedAt) : "")
  }
}
