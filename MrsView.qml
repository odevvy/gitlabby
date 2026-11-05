import QtQuick
import qs.Commons
import "Logic.js" as Logic
import "components"

// Open merge requests: waiting on his review (no drafts), then his own, with
// each one's pipeline, GitLab's merge status and every reviewer's state.
// Read-only: a row only opens the merge request in the browser. The lists and
// their chrome are a ScopedList over the shared service's mrs (a ScopedFetch),
// asked for when this view opens, its scope changes, or r; never on a timer.
// m toggles it. Quiet (v152 design A; v0.1.71: "read-only" is a chip after
// the header's tabs, and the header's Updated says when the lists were read).
// The header's Merge requests tab names the view, and Esc or the Board tab goes
// back; the status as coloured text. No footer: the keys live behind the
// keyboard icon.
ScopedList {
  id: view
  fetch: host.feed.mrs
  names: ({ tab: "scopeTab", underline: "scopeUnderline", count: "mrsCount", row: "mrRow", bar: "mrFocusBar" })
  sections: function(a) {
    return [["review", "Waiting on your review", a.review, "Nothing waiting on your review."],
            ["mine", "Yours", a.mine, "No open merge requests of yours."]]
  }
  copySign: function(row) { return "!" }

  // The header shows a reload of lists already on screen; the first load is
  // the spinner row only (as To-do).
  busy: loading && answer !== null

  // The first load: a spinner row; an error or sign-in: the same row, still.
  messageShown: !view.answer ? view.loading : view.answer.state !== "ready"
  message: Component {
    LoadingRow {
      objectName: "mrsMessage"
      host: view.host
      spinning: view.loading
      text: !view.answer ? "Loading merge requests\u2026"
        : view.answer.message + (view.loading ? "" : "  Press r to try again.")
    }
  }

  rowContent: Component {
    Column {
      id: mr
      readonly property var row: parent ? parent.row : ({ reviewers: [], author: {} })
      readonly property string section: parent ? parent.section : ""
      readonly property var status: Logic.mrStatus(row)
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
          BoardText {
            objectName: "mrStatus"
            readonly property string label: mr.status.text
            visible: label !== ""
            anchors.verticalCenter: parent.verticalCenter
            text: label
            color: mr.status.color !== "" ? mr.status.color : view.host.dim
            font.pixelSize: Style.font.caption
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
            text: Logic.age(mr.row.updatedAt); color: view.host.quiet; font.pixelSize: Style.font.caption
          }
        }
      }
      BoardText {
        leftPadding: Style.space(20)
        width: parent.width
        text: Logic.mrSubline(mr.row, mr.section)
        elide: Text.ElideRight
        color: view.host.quiet; font.pixelSize: Style.font.caption
      }
    }
  }
}
