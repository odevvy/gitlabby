import QtQuick
import QtQuick.Controls
import qs.Commons

// One issue: title, state, labels, people, dates, then the description as
// Markdown. Back (or Esc) returns to the board.
Item {
  id: view
  required property var host
  readonly property var issue: host.issue || ({})

  function when(iso) {
    return iso ? new Date(iso).toLocaleString(Qt.locale(), "yyyy-MM-dd HH:mm") : "—"
  }

  implicitHeight: content.implicitHeight

  Flickable {
    anchors.fill: parent
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(8)

      Item {
        width: parent.width
        implicitHeight: back.implicitHeight
        Pill { id: back; label: "‹ Back"; clickable: true; textColor: view.host.foreground; onClicked: view.host.back() }
        Pill {
          anchors.right: parent.right
          visible: !!view.issue.url
          label: "Open in browser ↗"; clickable: true
          onClicked: view.host.openUrl(view.issue.url)
        }
      }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        textFormat: Text.StyledText
        text: "<font color='" + view.host.dim + "'>#" + (view.issue.iid || "") + "</font>&nbsp; " + view.host.escaped(view.issue.title || "")
        font { pixelSize: Style.font.title; bold: true }
      }

      Flow {
        width: parent.width; spacing: Style.space(4)
        Pill {
          visible: !!view.issue.state
          label: view.issue.state === "closed" ? "Closed" : "Open"
          textColor: view.issue.state === "closed" ? view.host.dim : view.host.accent
          border.color: textColor
        }
        Repeater {
          model: view.issue.labels || []
          delegate: Pill { required property var modelData; label: String(modelData) }
        }
      }

      Grid {
        columns: 2; columnSpacing: Style.space(12); rowSpacing: Style.space(3)
        Repeater {
          model: [
            "Assignees", (view.issue.assignees || []).join(", ") || "—",
            "Author", view.issue.author || "—",
            "Milestone", view.issue.milestone || "—",
            "Created", view.when(view.issue.createdAt),
            "Updated", view.when(view.issue.updatedAt)
          ]
          delegate: BoardText {
            required property var modelData
            required property int index
            text: String(modelData)
            color: index % 2 === 0 ? view.host.dim : view.host.foreground
            font.pixelSize: Style.font.bodySmall
          }
        }
      }

      Rectangle { width: parent.width; height: 1; color: view.host.faint }

      BoardText {
        width: parent.width; wrapMode: Text.Wrap
        visible: view.host.issueLoading || view.host.issueError !== "" || !view.issue.description
        text: view.host.issueLoading ? "Loading…" : (view.host.issueError || "No description.")
        color: view.host.dim; font.italic: true
      }

      Text {
        width: parent.width; wrapMode: Text.Wrap
        visible: !view.host.issueLoading && !!view.issue.description
        textFormat: Text.MarkdownText
        text: view.issue.description || ""
        color: view.host.foreground
        linkColor: view.host.accent
        font { family: Style.font.family; pixelSize: Style.font.bodySmall }
        onLinkActivated: function(link) { view.host.openLink(link) }
        HoverHandler { cursorShape: parent.hoveredLink !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor }
      }
    }
  }
}
