import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// GitLab issue board in the Omarchy bar. Left click opens the popup, right or
// middle click refreshes. Data comes from ./board-fetch (read-only glab api).
// Column headers collapse a column; header chips show or hide columns. Both
// are saved inline on this widget's shell.json entry.
Panel {
  id: root
  moduleName: "odevvy.gitlab-board"
  ipcTarget: "odevvy.gitlab-board"

  readonly property color foreground: Commons.Color.popups.text
  readonly property color accent: Commons.Color.accent
  readonly property color background: Commons.Color.popups.background
  // Solid blends so they also work inside StyledText markup.
  readonly property color dim: Qt.tint(foreground, Qt.rgba(background.r, background.g, background.b, 0.45))
  readonly property color faint: Qt.tint(background, Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12))
  readonly property string project: String(setting("project", "firelink21/phrase41")).trim()
  readonly property int refreshIntervalSec: Math.max(30, parseInt(String(setting("refreshIntervalSec", 60)), 10) || 60)
  readonly property int columnWidth: Style.space(220)
  readonly property int stripWidth: Style.space(34)
  readonly property int gap: Style.space(10)

  property bool loading: false
  property string boardState: "loading"
  property string message: ""
  property string updatedAt: ""
  property var columns: []
  property var collapsed: listSetting("collapsedColumns")
  property var hidden: listSetting("hiddenColumns")
  // "unlabeled" exists only when it has issues; hidden columns disappear.
  readonly property var availableColumns: columns.filter(function(c) { return c.name !== "unlabeled" || count(c) > 0 })
  readonly property var shownColumns: availableColumns.filter(function(c) { return hidden.indexOf(c.name) === -1 })
  readonly property int boardWidth: shownColumns.reduce(function(sum, c) {
    return sum + (collapsed.indexOf(c.name) === -1 ? columnWidth : stripWidth) + gap
  }, 0)

  function count(column) { return (column.issues || []).length }

  function listSetting(name) {
    var value = setting(name, [])
    var list = Array.isArray(value) ? value : String(value || "").split(",")
    return list.map(function(v) { return String(v).trim() }).filter(function(v) { return v !== "" })
  }

  function toggled(list, name) {
    return list.indexOf(name) === -1 ? list.concat([name]) : list.filter(function(v) { return v !== name })
  }

  // Same write path as built-in widgets: merge into the inline entry and hand
  // it to the shell facade. Without the facade the state stays in memory.
  function persist() {
    if (!bar || !bar.shell || typeof bar.shell.updateEntryInline !== "function") return
    var entry = { id: moduleName }
    for (var key in settings) if (key !== "id") entry[key] = settings[key]
    entry.collapsedColumns = collapsed
    entry.hiddenColumns = hidden
    bar.shell.updateEntryInline(moduleName, entry)
  }

  function toggleCollapsed(name) { collapsed = toggled(collapsed, name); persist() }
  function toggleHidden(name) { hidden = toggled(hidden, name); persist() }

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
      boardState = "error"; message = "board-fetch returned no readable output."; columns = []
    }
  }

  function openUrl(url) {
    if (!url) return
    Quickshell.execDetached(["omarchy-launch-browser", String(url)])
    close()
  }

  function statusText() {
    if (boardState === "ready") {
      if (loading) return "Refreshing…"
      return updatedAt !== "" ? "Updated " + new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : ""
    }
    if (boardState === "loading") return "Loading GitLab issues…"
    if (boardState === "logged-out") return message || "Not signed in. Run: glab auth login"
    return message || "Could not load issues."
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onOpenedChanged: if (opened) refresh()

  Timer {
    interval: root.refreshIntervalSec * 1000
    repeat: true; running: true; triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Process {
    id: fetchProcess
    onExited: root.loading = false
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.apply(text) }
  }

  BarIconButton {
    id: button
    anchors.fill: parent; bar: root.bar
    text: "\uf296"
    tooltipText: "GitLab board · " + root.project
    onPressed: function(buttonCode) {
      if (buttonCode === Qt.RightButton || buttonCode === Qt.MiddleButton) root.refresh()
      else root.toggle()
    }
  }

  // Inline components cannot see outer ids, so they read theme tokens directly.
  component BoardText: Text {
    textFormat: Text.PlainText
    color: Commons.Color.popups.text
    font.family: Style.font.family
    font.pixelSize: Style.font.caption
  }

  // Small rounded text pill used for counts, label chips and column toggles.
  component Pill: Rectangle {
    readonly property color fg: Commons.Color.popups.text
    readonly property color bg: Commons.Color.popups.background
    property alias label: pillText.text
    property color textColor: Qt.tint(fg, Qt.rgba(bg.r, bg.g, bg.b, 0.45))
    property int pixelSize: Style.font.caption
    implicitWidth: pillText.implicitWidth + Style.space(10)
    implicitHeight: pillText.implicitHeight + Style.space(3)
    radius: height / 2
    color: "transparent"
    border { width: 1; color: Qt.tint(bg, Qt.rgba(fg.r, fg.g, fg.b, 0.2)) }
    BoardText { id: pillText; anchors.centerIn: parent; color: parent.textColor; font.pixelSize: parent.pixelSize }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button; owner: root; bar: root.bar
    open: root.opened; focusTarget: keyCatcher
    // fittedContentWidth caps at availableCardWidth (screen minus margins);
    // anything wider scrolls horizontally inside the board.
    contentWidth: panel.fittedContentWidth(Math.max(Style.space(380), root.boardWidth + panel.padding * 2 + Style.space(4)))
    contentHeight: panel.fittedContentHeight(keyCatcher.implicitHeight, Style.space(640))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      implicitHeight: header.implicitHeight + root.gap + Math.max(board.implicitHeight, Style.space(60))
      onCloseRequested: root.close()
      onTextKey: function(text) { if (text === "r" || text === "R") root.refresh() }

      Column {
        id: header
        width: parent.width; spacing: Style.space(6)

        Item {
          width: parent.width
          implicitHeight: Math.max(title.implicitHeight, status.implicitHeight)
          BoardText {
            id: title
            anchors.verticalCenter: parent.verticalCenter
            text: "GitLab · " + root.project
            font { pixelSize: Style.font.title; bold: true }
          }
          BoardText {
            id: status
            anchors { left: title.right; leftMargin: Style.space(12); right: refreshButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
            horizontalAlignment: Text.AlignRight
            elide: Text.ElideLeft
            text: root.statusText()
            color: root.boardState === "ready" ? root.dim : root.accent
            font.pixelSize: Style.font.bodySmall
          }
          BoardText {
            id: refreshButton
            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
            text: "\uf021"
            color: refreshMouse.containsMouse ? root.accent : root.dim
            opacity: root.loading ? 0.5 : 1
            font.pixelSize: Style.font.body
            RotationAnimation on rotation {
              running: root.loading; loops: Animation.Infinite; from: 0; to: 360; duration: 900
              onStopped: refreshButton.rotation = 0
            }
            MouseArea {
              id: refreshMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor
              onClicked: root.refresh()
            }
          }
        }

        Flow {
          width: parent.width; spacing: Style.space(4); visible: root.boardState === "ready"
          Repeater {
            model: root.availableColumns
            delegate: Pill {
              required property var modelData
              readonly property bool shown: root.hidden.indexOf(modelData.name) === -1
              label: modelData.name + " " + root.count(modelData)
              textColor: shown ? root.foreground : root.dim
              color: shown ? root.faint : "transparent"
              opacity: shown ? 1 : 0.6
              MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleHidden(parent.modelData.name) }
            }
          }
        }
      }

      Flickable {
        id: flick
        anchors { top: header.bottom; topMargin: root.gap; left: parent.left; right: parent.right; bottom: parent.bottom }
        contentWidth: board.implicitWidth; contentHeight: board.implicitHeight
        clip: true; boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }

        Row {
          id: board
          spacing: root.gap
          Repeater {
            model: root.boardState === "ready" ? root.shownColumns : []
            delegate: Item {
              id: boardColumn
              required property var modelData
              readonly property bool isCollapsed: root.collapsed.indexOf(modelData.name) !== -1
              readonly property var issues: modelData.issues || []
              width: isCollapsed ? root.stripWidth : root.columnWidth
              implicitHeight: isCollapsed ? Math.max(strip.implicitHeight, flick.height) : cards.implicitHeight

              // Collapsed: a narrow strip with the count and the rotated name.
              Rectangle {
                id: strip
                visible: boardColumn.isCollapsed
                anchors.fill: parent
                implicitHeight: stripCount.implicitHeight + stripName.implicitWidth + Style.space(24)
                radius: Style.space(6)
                color: stripMouse.containsMouse ? root.faint : "transparent"
                border { width: 1; color: root.faint }
                Pill { id: stripCount; anchors.horizontalCenter: parent.horizontalCenter; y: Style.space(6); label: String(boardColumn.issues.length); textColor: root.foreground }
                BoardText {
                  id: stripName
                  anchors.horizontalCenter: parent.horizontalCenter
                  y: stripCount.y + stripCount.height + Style.space(6) + (implicitWidth - implicitHeight) / 2
                  rotation: 90
                  text: boardColumn.modelData.name
                  color: root.dim
                  font.capitalization: Font.AllUppercase
                }
                MouseArea {
                  id: stripMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: root.toggleCollapsed(boardColumn.modelData.name)
                }
              }

              // Expanded: header with count badge and accent underline, then cards.
              Column {
                id: cards
                visible: !boardColumn.isCollapsed
                width: parent.width
                spacing: Style.space(6)

                Item {
                  width: parent.width
                  implicitHeight: headerRow.implicitHeight + Style.space(6)
                  Row {
                    id: headerRow
                    spacing: Style.space(6)
                    BoardText {
                      anchors.verticalCenter: parent.verticalCenter
                      text: boardColumn.modelData.name
                      font { bold: true; capitalization: Font.AllUppercase }
                    }
                    Pill { anchors.verticalCenter: parent.verticalCenter; label: String(boardColumn.issues.length); color: root.faint }
                  }
                  Rectangle {
                    anchors.bottom: parent.bottom; width: parent.width; height: Math.max(1, Style.space(2))
                    color: root.accent; opacity: headerMouse.containsMouse ? 1 : 0.6
                  }
                  MouseArea {
                    id: headerMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: root.toggleCollapsed(boardColumn.modelData.name)
                  }
                }

                BoardText { visible: boardColumn.issues.length === 0; text: "No issues"; color: root.dim; opacity: 0.7; font.italic: true }

                Repeater {
                  model: boardColumn.issues
                  delegate: Rectangle {
                    id: card
                    required property var modelData
                    readonly property var chips: (modelData.labels || []).filter(function(l) { return l !== boardColumn.modelData.name })
                    width: boardColumn.width
                    implicitHeight: cardText.implicitHeight + (chipFlow.visible ? chipFlow.implicitHeight + Style.space(6) : 0) + Style.space(16)
                    radius: Style.space(6)
                    opacity: boardColumn.modelData.name === "closed" ? 0.65 : 1
                    color: cardMouse.containsMouse ? root.faint : "transparent"
                    border { width: 1; color: cardMouse.containsMouse ? root.accent : root.faint }
                    BoardText {
                      id: cardText
                      x: Style.space(8); y: Style.space(8); width: parent.width - Style.space(16)
                      textFormat: Text.StyledText
                      text: "<font color='" + root.dim + "'>#" + card.modelData.iid + "</font>&nbsp; "
                        + String(card.modelData.title).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                      font.pixelSize: Style.font.bodySmall
                      wrapMode: Text.Wrap
                    }
                    Flow {
                      id: chipFlow
                      visible: card.chips.length > 0
                      x: Style.space(8); width: parent.width - Style.space(16); spacing: Style.space(4)
                      anchors { top: cardText.bottom; topMargin: Style.space(6) }
                      Repeater {
                        model: card.chips
                        delegate: Pill { required property var modelData; label: String(modelData); pixelSize: Math.max(8, Style.font.caption - 1) }
                      }
                    }
                    MouseArea {
                      id: cardMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                      onClicked: root.openUrl(card.modelData.url)
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
}
