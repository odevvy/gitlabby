import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// GitLab issue board in the Omarchy bar. Left click opens the popup, right or
// middle click refreshes. Data comes from ./board-fetch (read-only glab api).
Panel {
  id: root
  moduleName: "odevvy.gitlab-board"
  ipcTarget: "odevvy.gitlab-board"

  readonly property color foreground: bar ? bar.foreground : Commons.Color.foreground
  readonly property color dim: Qt.darker(foreground, 1.55)
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property string project: String(setting("project", "firelink21/phrase41")).trim()
  readonly property int refreshIntervalSec: Math.max(30, parseInt(String(setting("refreshIntervalSec", 60)), 10) || 60)
  readonly property int columnWidth: Style.space(200)

  property bool loading: false
  property string boardState: "loading"
  property string message: "Loading GitLab issues…"
  property string updatedAt: ""
  property var columns: []
  // "unlabeled" is only shown when it has issues.
  readonly property var visibleColumns: columns.filter(function(c) {
    return c.name !== "unlabeled" || (c.issues || []).length > 0
  })

  function helperPath() {
    return decodeURIComponent(Qt.resolvedUrl("board-fetch").toString().replace(/^file:\/\//, ""))
  }

  function refresh() {
    if (fetchProcess.running) return
    loading = true
    fetchProcess.command = [helperPath(), "--project", project]
    fetchProcess.running = true
  }

  function apply(raw) {
    try {
      var data = JSON.parse(String(raw || ""))
      boardState = String(data.state || "error")
      message = String(data.message || "")
      updatedAt = String(data.updatedAt || "")
      columns = Array.isArray(data.columns) ? data.columns : []
    } catch (error) {
      boardState = "error"
      message = "board-fetch returned no readable output."
      columns = []
    }
  }

  function openUrl(url) {
    var value = String(url || "")
    if (value === "") return
    Quickshell.execDetached(["omarchy-launch-browser", value])
    close()
  }

  function statusText() {
    if (boardState === "ready") {
      var time = updatedAt !== "" ? new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : ""
      return (loading ? "Refreshing…" : "Updated " + time)
    }
    if (boardState === "loading") return "Loading GitLab issues…"
    if (boardState === "logged-out") return message !== "" ? message : "Not signed in. Run: glab auth login"
    return message !== "" ? message : "Could not load issues."
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onOpenedChanged: if (opened) refresh()

  Timer {
    interval: root.refreshIntervalSec * 1000
    repeat: true
    running: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Process {
    id: fetchProcess
    running: false
    command: []
    onExited: root.loading = false
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.apply(text)
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "\uf296"
    tooltipText: "GitLab board · " + root.project
    onPressed: function(buttonCode) {
      if (buttonCode === Qt.RightButton || buttonCode === Qt.MiddleButton) root.refresh()
      else root.toggle()
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: panel.loadedContent
    contentWidth: panel.fittedContentWidth(Math.max(Style.space(320), root.visibleColumns.length * (root.columnWidth + Style.space(10))))
    contentHeight: panel.fittedContentHeight(panel.loadedContentHeight, Style.space(600))

    content: PanelKeyCatcher {
      id: keyCatcher
      implicitHeight: header.implicitHeight + Style.space(10) + board.implicitHeight
      onCloseRequested: root.close()
      onTextKey: function(text, modifiers) { if (text === "r" || text === "R") root.refresh() }

      Column {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Style.space(2)
        Text {
          text: "GitLab · " + root.project
          color: root.foreground
          font.family: root.fontFamily
          font.pixelSize: Style.font.title
          font.bold: true
        }
        Text {
          width: parent.width
          text: root.statusText()
          color: root.boardState === "ready" ? root.dim : root.foreground
          font.family: root.fontFamily
          font.pixelSize: Style.font.bodySmall
          wrapMode: Text.Wrap
        }
      }

      Flickable {
        anchors.top: header.bottom
        anchors.topMargin: Style.space(10)
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        contentWidth: board.implicitWidth
        contentHeight: board.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }

        Row {
          id: board
          spacing: Style.space(10)
          Repeater {
            model: root.boardState === "ready" ? root.visibleColumns : []
            delegate: Column {
              id: boardColumn
              required property var modelData
              width: root.columnWidth
              spacing: Style.space(4)
              Text {
                text: boardColumn.modelData.name + "  " + (boardColumn.modelData.issues || []).length
                color: root.dim
                font.family: root.fontFamily
                font.pixelSize: Style.font.caption
                font.capitalization: Font.AllUppercase
              }
              Repeater {
                model: boardColumn.modelData.issues || []
                delegate: Rectangle {
                  id: issueRow
                  required property var modelData
                  width: boardColumn.width
                  implicitHeight: issueText.implicitHeight + chips.implicitHeight + Style.space(12)
                  radius: Style.cornerRadius
                  color: rowMouse.containsMouse ? Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.08) : "transparent"
                  border.width: 1
                  border.color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.15)
                  Text {
                    id: issueText
                    x: Style.space(6)
                    y: Style.space(4)
                    width: parent.width - Style.space(12)
                    text: "#" + issueRow.modelData.iid + "  " + issueRow.modelData.title
                    textFormat: Text.PlainText
                    color: root.foreground
                    font.family: root.fontFamily
                    font.pixelSize: Style.font.bodySmall
                    wrapMode: Text.Wrap
                  }
                  Flow {
                    id: chips
                    x: Style.space(6)
                    anchors.top: issueText.bottom
                    anchors.topMargin: Style.space(4)
                    width: parent.width - Style.space(12)
                    spacing: Style.space(4)
                    Repeater {
                      model: issueRow.modelData.labels || []
                      delegate: Rectangle {
                        id: chip
                        required property var modelData
                        width: chipText.implicitWidth + Style.space(8)
                        height: chipText.implicitHeight + Style.space(2)
                        radius: height / 2
                        color: "transparent"
                        border.width: 1
                        border.color: root.dim
                        Text {
                          id: chipText
                          anchors.centerIn: parent
                          text: String(chip.modelData)
                          textFormat: Text.PlainText
                          color: root.dim
                          font.family: root.fontFamily
                          font.pixelSize: Style.font.caption
                        }
                      }
                    }
                  }
                  MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.openUrl(issueRow.modelData.url)
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
