import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// GitLab issue board in the Omarchy bar. Left click opens the popup, right or
// middle click refreshes. Data comes from ./board-fetch through glab: reads are
// GET only; the writes are `board-fetch move`, run when a card is dropped on
// another column, and `board-fetch comment`, run by Post in the issue view.
// Views: the board, one issue, the board picker, and settings. Selection,
// per-board collapsed/hidden columns and defaults are saved inline in shell.json.
Panel {
  id: root
  moduleName: "odevvy.gitlab-board"
  ipcTarget: "odevvy.gitlab-board"

  readonly property color foreground: Commons.Color.popups.text
  readonly property color accent: Commons.Color.accent
  readonly property color background: Commons.Color.popups.background
  readonly property color muted: Commons.Color.muted
  readonly property color urgent: Commons.Color.urgent
  // Solid blends so they also work inside StyledText markup.
  readonly property color dim: Qt.tint(foreground, Qt.rgba(background.r, background.g, background.b, 0.45))
  readonly property color faint: Qt.tint(background, Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12))
  readonly property int columnWidth: Style.space(220)
  readonly property int stripWidth: Style.space(34)
  readonly property int gap: Style.space(10)

  // Saved default board (empty id = the project's first board).
  readonly property string defaultProject: String(setting("defaultProject", "firelink21/phrase41")).trim()
  readonly property string defaultBoardId: String(setting("defaultBoardId", ""))
  readonly property string defaultBoardName: String(setting("defaultBoardName", ""))
  // Board on screen: starts as the default on every shell start; browsing
  // assigns these (breaking the binding) and is never saved.
  property string project: defaultProject
  property string boardId: defaultBoardId
  property string boardName: defaultBoardName
  // Saved preferences.
  property int refreshIntervalSec: Math.max(30, parseInt(String(setting("refreshIntervalSec", 60)), 10) || 60)
  property var defaultCollapsed: lowerList(setting("defaultCollapsed", ["closed", "research", "open"]))
  property var boardStates: setting("boardStates", ({})) || ({})

  // Board data from the last fetch.
  property bool loading: false
  property bool refreshQueued: false
  property string boardState: "loading"
  property string message: ""
  property string updatedAt: ""
  property var columns: []
  property var labelColors: ({})
  property string resolvedBoardId: ""
  property bool fallback: false
  property string firstBoardId: ""
  readonly property bool onDefault: project === defaultProject && resolvedBoardId === (defaultBoardId || firstBoardId)
  readonly property string stateKey: project + "#" + (resolvedBoardId || "labels")
  readonly property var boardEntry: boardStates[stateKey] || null
  readonly property var availableColumns: columns.filter(function(c) { return c.name !== "Unlabeled" || (c.issues || []).length > 0 })
  readonly property var shownColumns: availableColumns.filter(function(c) { return !isHidden(c.name) })
  readonly property int boardWidth: shownColumns.reduce(function(sum, c) { return sum + (isCollapsed(c.name) ? stripWidth : columnWidth) + gap }, 0)

  // Views and their data.
  property string view: "board"
  property var issue: null
  property bool issueLoading: false
  property string issueError: ""
  property string pickerStep: "projects"
  property string pickerProject: ""
  property var projects: []
  property var pickerBoards: []
  property bool auxLoading: false
  property string auxError: ""
  property string auxKind: ""
  property var pendingAux: null

  // Drag-to-move: one move at a time. The card moves at once (optimistic);
  // the snapshot brings it back if GitLab refuses. moveSeq/fetchSeq drop any
  // board answer that was requested before the latest move.
  property bool moving: false
  property int movingIid: -1
  property var moveSnapshot: null
  property string moveKey: ""
  property string moveError: ""
  property int moveSeq: 0
  property int fetchSeq: 0
  readonly property bool canMove: boardState === "ready" && !fallback && resolvedBoardId !== ""

  function lowerList(value) {
    var list = Array.isArray(value) ? value : String(value || "").split(",")
    return list.map(function(v) { return String(v).trim().toLowerCase() }).filter(function(v) { return v !== "" })
  }
  function has(list, name) { return (list || []).indexOf(String(name).toLowerCase()) !== -1 }
  function toggled(list, name) {
    var key = String(name).toLowerCase()
    return has(list, key) ? list.filter(function(v) { return v !== key }) : list.concat([key])
  }
  // GitLab label colors (validated #rrggbb from board-fetch). Text color: the
  // label's own text_color, else black or white by luminance.
  function labelStyle(name) {
    var c = labelColors[name]
    if (!c || !c.color) return null
    var bg = Qt.color(c.color)
    var light = 0.299 * bg.r + 0.587 * bg.g + 0.114 * bg.b > 0.6
    return { bg: bg, fg: c.textColor ? Qt.color(c.textColor) : (light ? "#1f1e24" : "#ffffff") }
  }
  function columnAccent(column) {
    if (column.color) return Qt.color(column.color)
    return column.kind === "open" ? accent : column.kind === "closed" ? muted : dim
  }
  // "5m", "3h", "4d", "2w", "6mo", "1y", relative to the last refresh (or to since).
  function age(iso, since) {
    var ms = new Date(since || updatedAt || Date.now()) - new Date(iso)
    if (!iso || !(ms >= 0)) return ""
    var m = ms / 60000, h = m / 60, d = h / 24
    return m < 60 ? Math.floor(m) + "m" : h < 24 ? Math.floor(h) + "h" : d < 14 ? Math.floor(d) + "d"
      : d < 60 ? Math.floor(d / 7) + "w" : d < 365 ? Math.floor(d / 30) + "mo" : Math.floor(d / 365) + "y"
  }
  function escaped(text) { return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") }

  // Per board: stored lists win; a board never touched uses defaultCollapsed.
  function collapsedList() { return boardEntry && boardEntry.collapsed ? boardEntry.collapsed : defaultCollapsed }
  function hiddenList() { return boardEntry && boardEntry.hidden ? boardEntry.hidden : [] }
  function isCollapsed(name) { return has(collapsedList(), name) }
  function isHidden(name) { return has(hiddenList(), name) }
  function isDefaultCollapsed(name) { return has(defaultCollapsed, name) }

  function storeBoard(collapsed, hidden) {
    var next = {}
    for (var key in boardStates) next[key] = boardStates[key]
    next[stateKey] = { collapsed: collapsed, hidden: hidden }
    boardStates = next
    persist()
  }
  function toggleCollapsed(name) { storeBoard(toggled(collapsedList(), name), hiddenList()) }
  function toggleHidden(name) { storeBoard(collapsedList(), toggled(hiddenList(), name)) }
  function toggleDefaultCollapsed(name) {
    var on = !isDefaultCollapsed(name)
    defaultCollapsed = toggled(defaultCollapsed, name)
    // Apply to the board on screen too, so the change is visible at once.
    if (isCollapsed(name) !== on) toggleCollapsed(name)
    else persist()
  }
  // One-time update to settings revision 2 (v1.3): Open joins the collapsed
  // defaults and every saved board, without touching anything else. Runs again
  // only if it could not be saved.
  readonly property int settingsRevision: 2
  function migrateSettings() {
    if ((parseInt(String(setting("settingsRevision", 1)), 10) || 1) >= settingsRevision) return
    if (!bar || !bar.shell || typeof bar.shell.updateEntryInline !== "function") return
    if (setting("defaultCollapsed", null) === null && setting("boardStates", null) === null) return  // nothing saved yet
    // Read the saved values directly: the property bindings may not have caught up.
    var collapsed = lowerList(setting("defaultCollapsed", ["closed", "research"]))
    var saved = setting("boardStates", ({})) || ({})
    var next = {}
    for (var key in saved) {
      var entry = saved[key] || {}
      next[key] = Array.isArray(entry.collapsed) && !has(entry.collapsed, "open")
        ? { collapsed: entry.collapsed.concat(["open"]), hidden: entry.hidden || [] } : entry
    }
    defaultCollapsed = has(collapsed, "open") ? collapsed : collapsed.concat(["open"])
    boardStates = next
    persist()
  }
  onSettingsChanged: Qt.callLater(migrateSettings)

  function setRefreshInterval(seconds) { refreshIntervalSec = seconds; persist() }

  // Same write path as built-in widgets: merge into the inline entry and hand
  // it to the shell facade. Without the facade the state stays in memory.
  // nextDefault ({ project, id, name }) replaces the saved default board.
  function persist(nextDefault) {
    if (!bar || !bar.shell || typeof bar.shell.updateEntryInline !== "function") return
    var d = nextDefault || { project: defaultProject, id: defaultBoardId, name: defaultBoardName }
    var entry = { id: moduleName }
    var dropped = ["id", "collapsedColumns", "hiddenColumns", "project", "boardId", "boardName"]
    for (var key in settings) if (dropped.indexOf(key) === -1) entry[key] = settings[key]
    entry.defaultProject = d.project
    entry.defaultBoardId = d.id
    entry.defaultBoardName = d.name
    entry.refreshIntervalSec = refreshIntervalSec
    entry.defaultCollapsed = defaultCollapsed
    entry.boardStates = boardStates
    entry.settingsRevision = settingsRevision
    bar.shell.updateEntryInline(moduleName, entry)
  }

  function helperPath() {
    return decodeURIComponent(Qt.resolvedUrl("board-fetch").toString().replace(/^file:\/\//, ""))
  }

  function refresh() {
    if (fetchProcess.running || moving) { refreshQueued = true; return }
    loading = true
    fetchSeq = moveSeq
    fetchProcess.command = [helperPath(), "board", "--project", project, "--board", boardId]
    fetchProcess.running = true
  }

  function parse(raw) {
    try { return JSON.parse(String(raw || "")) } catch (error) { return { state: "error", message: "board-fetch returned no readable output." } }
  }

  function apply(raw) {
    var data = parse(raw)
    if (data.project && data.project !== project) return  // answer for a project we already left
    if (moving || fetchSeq !== moveSeq) { refreshQueued = true; return }  // older than the latest move
    boardState = String(data.state || "error")
    message = String(data.message || "")
    updatedAt = String(data.updatedAt || "")
    columns = Array.isArray(data.columns) ? data.columns : []
    labelColors = data.labelColors || {}
    resolvedBoardId = data.board ? String(data.board.id) : ""
    fallback = !!data.fallback
    firstBoardId = data.boards && data.boards.length > 0 ? String(data.boards[0].id) : ""
    if (data.board && boardName !== data.board.name) boardName = data.board.name
    if (data.fallback) boardName = ""
  }

  // Columns a card can be dropped on: Open, Closed and label lists of a real
  // board (not the workflow-label fallback, not assignee/milestone lists).
  function canDrop(column) {
    return canMove && !!column && (column.kind === "open" || column.kind === "closed" || (column.kind === "label" && !!column.listId))
  }
  function columnKey(column) { return column.kind + ":" + (column.listId || column.name) }
  function listSpec(column) { return column.kind === "label" ? String(column.listId) : column.kind }

  // Board columns after moving row from one column to another, as GitLab
  // would show them: label swapped (kept when closing), card on top of target.
  function movedColumns(row, from, to) {
    var fromKey = columnKey(from), toKey = columnKey(to)
    var labels = (row.labels || []).filter(function(l) { return !(from.kind === "label" && to.kind !== "closed" && l === from.name) })
    if (to.kind === "label" && labels.indexOf(to.name) === -1) labels = labels.concat([to.name])
    var moved = Object.assign({}, row, { labels: labels })
    return columns.map(function(c) {
      var key = columnKey(c)
      var issues = (c.issues || []).filter(function(i) { return i.iid !== row.iid || (key !== fromKey && key !== toKey && to.kind !== "closed") })
        .map(function(i) { return i.iid === row.iid ? moved : i })
      return Object.assign({}, c, { issues: key === toKey ? [moved].concat(issues) : issues })
    })
  }

  function moveIssue(row, from, to) {
    if (moving || !row || !canDrop(from) || !canDrop(to) || columnKey(from) === columnKey(to)) return false
    moveSnapshot = columns
    moveKey = stateKey
    movingIid = row.iid
    moveError = ""
    moving = true
    moveSeq++
    columns = movedColumns(row, from, to)
    moveProcess.command = [helperPath(), "move", "--project", project, "--board", resolvedBoardId,
      "--iid", String(row.iid), "--from", listSpec(from), "--to", listSpec(to)]
    moveProcess.running = true
    moveWatchdog.restart()
    return true
  }

  function moveDone(raw) {
    if (!moving) return  // late answer after the watchdog gave up
    moveWatchdog.stop()
    var data = parse(raw)
    moving = false
    movingIid = -1
    if (data.state !== "ready") {
      if (moveSnapshot && moveKey === stateKey) columns = moveSnapshot
      moveError = String(data.message || "Move failed.")
      moveErrorTimer.restart()
    }
    moveSnapshot = null
    // Success: load the board as GitLab now has it. Failure: only if a refresh was due.
    if (data.state === "ready" || refreshQueued) { refreshQueued = false; refresh() }
  }

  function runAux(kind, args) {
    if (auxProcess.running) { pendingAux = { kind: kind, args: args }; return }
    auxKind = kind
    auxError = ""
    auxLoading = kind !== "issue"
    auxProcess.command = [helperPath(), kind].concat(args)
    auxProcess.running = true
  }

  function applyAux(raw) {
    var data = parse(raw)
    var error = data.state === "ready" ? "" : String(data.message || "Request failed.")
    var kind = data.issue ? "issue" : data.projects ? "projects" : data.boards ? "boards" : auxKind
    auxLoading = false
    if (kind === "issue") {
      issueLoading = false
      issueError = error
      if (!error && issue && data.issue && data.issue.iid === issue.iid) issue = data.issue
    } else if (kind === "projects") {
      auxError = error
      projects = data.projects || []
    } else if (kind === "boards") {
      auxError = error
      var boards = data.boards || []
      pickerBoards = boards.length > 0 || error ? boards : [{ id: "", name: "Workflow labels (no boards)" }]
    }
  }

  function showView(name) {
    view = name
    Qt.callLater(function() {
      if (name === "picker" && picker.filterField.visible) picker.filterField.forceActiveFocus()
      else keyCatcher.forceActiveFocus()
    })
  }
  function back() { showView("board") }

  function openIssue(row) {
    issue = row
    issueError = ""
    issueLoading = true
    showView("issue")
    runAux("issue", ["--project", project, "--iid", String(row.iid)])
  }

  function openPicker() {
    pickProjectStep()
    if (projects.length === 0) runAux("projects", [])
  }
  function pickProjectStep() { pickerStep = "projects"; showView("picker") }
  function pickProject(path) {
    pickerProject = path
    pickerBoards = []
    pickerStep = "boards"
    runAux("boards", ["--project", path])
  }
  function pickBoard(b) { switchTo(pickerProject, String(b.id || ""), b.id ? String(b.name) : "") }
  function openDefault() { switchTo(defaultProject, defaultBoardId, defaultBoardName) }
  function switchTo(path, id, name) {
    project = path
    boardId = id
    boardName = name
    columns = []
    resolvedBoardId = id
    firstBoardId = ""
    moveError = ""
    boardState = "loading"
    back()
    refresh()
  }
  // Star in the picker: exactly one default, saved; the board on screen stays.
  function isDefaultBoard(b) {
    var first = pickerBoards.length > 0 ? String(pickerBoards[0].id || "") : ""
    return pickerProject === defaultProject && String(b.id || "") === (defaultBoardId || first)
  }
  function setDefault(b) {
    project = project; boardId = boardId; boardName = boardName  // freeze before the defaults change
    persist({ project: pickerProject, id: String(b.id || ""), name: b.id ? String(b.name) : "" })
  }

  function openUrl(url) {
    if (!url) return
    Quickshell.execDetached(["omarchy-launch-browser", String(url)])
    close()
  }
  // Markdown links: absolute http(s) as is; GitLab-relative paths on the issue's host.
  function openLink(link) {
    var value = String(link || "")
    if (/^\//.test(value) && issue && issue.url) value = String(issue.url).replace(/^(https?:\/\/[^\/]+).*$/, "$1") + value
    if (/^https?:\/\//.test(value)) openUrl(value)
  }

  function statusText() {
    if (moveError !== "") return moveError
    if (moving) return "Moving #" + movingIid + "…"
    if (boardState === "ready") {
      if (loading) return "Refreshing…"
      var time = updatedAt !== "" ? "Updated " + new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : ""
      return message !== "" ? message + "  " + time : time
    }
    if (boardState === "loading") return "Loading GitLab issues…"
    if (boardState === "logged-out") return message || "Not signed in. Run: glab auth login"
    return message || "Could not load issues."
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onOpenedChanged: if (opened) { view = "board"; refresh() }

  Timer {
    interval: root.refreshIntervalSec * 1000
    repeat: true; running: true; triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Process {
    id: fetchProcess
    onExited: { root.loading = false; if (root.refreshQueued) { root.refreshQueued = false; Qt.callLater(root.refresh) } }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.apply(text) }
  }

  Process {
    id: moveProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.moveDone(text) }
  }

  Timer { id: moveErrorTimer; interval: 8000; onTriggered: root.moveError = "" }
  // No answer in 30 s (glab hung or never started): put the card back and
  // reload, since the move may or may not have reached GitLab.
  Timer {
    id: moveWatchdog; interval: 30000
    onTriggered: { root.refreshQueued = true; root.moveDone(JSON.stringify({ state: "error", message: "No answer from glab; reloading the board." })) }
  }

  Process {
    id: auxProcess
    onExited: if (root.pendingAux) { var next = root.pendingAux; root.pendingAux = null; Qt.callLater(function() { root.runAux(next.kind, next.args) }) }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.applyAux(text) }
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

  KeyboardPanel {
    id: panel
    anchorItem: button; owner: root; bar: root.bar
    open: root.opened; focusTarget: keyCatcher
    // fittedContentWidth caps at availableCardWidth (screen minus margins);
    // anything wider scrolls horizontally inside the board.
    contentWidth: panel.fittedContentWidth(Math.max(Style.space(520), root.view === "board" ? root.boardWidth + panel.padding * 2 + Style.space(4) : 0))
    contentHeight: panel.fittedContentHeight(keyCatcher.implicitHeight, Style.space(640))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      blocked: issueView.typing  // the comment box gets every key (Omarchy PanelKeyCatcher.qml:27-31)
      implicitHeight: header.implicitHeight + root.gap + (root.view === "board" ? boardView.implicitHeight
        : root.view === "issue" ? issueView.implicitHeight : root.view === "picker" ? picker.implicitHeight : settingsView.implicitHeight)
      onCloseRequested: root.view !== "board" ? root.back() : root.close()
      onTextKey: function(text) { if (root.view === "board" && (text === "r" || text === "R")) root.refresh() }

      // Glass wash: a soft light from the top of the card (the card itself is
      // KeyboardPanel's, drawn in the theme's popups.background).
      Rectangle {
        anchors { fill: parent; margins: -panel.padding }
        radius: Style.cornerRadius
        gradient: Gradient {
          GradientStop { position: 0; color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.07) }
          GradientStop { position: 0.35; color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.015) }
          GradientStop { position: 1; color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.03) }
        }
      }

      Item {
        id: header
        width: parent.width
        implicitHeight: Math.max(title.implicitHeight, status.implicitHeight)

        BoardText {
          id: title
          anchors.verticalCenter: parent.verticalCenter
          width: Math.min(implicitWidth, parent.width * 0.6)
          elide: Text.ElideMiddle
          text: root.project + (root.boardName !== "" ? " · " + root.boardName : "") + " ▾"
          color: titleMouse.containsMouse ? root.accent : root.foreground
          font { pixelSize: Style.font.title; bold: true }
          MouseArea { id: titleMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openPicker() }
        }
        BoardText {
          id: defaultMark
          anchors { left: title.right; leftMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          text: root.onDefault ? "\uf005" : "\uf006 Default"
          color: root.onDefault || defaultMouse.containsMouse ? root.accent : root.dim
          font.pixelSize: Style.font.bodySmall
          MouseArea {
            id: defaultMouse; anchors.fill: parent; anchors.margins: -Style.space(4)
            enabled: !root.onDefault; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: root.openDefault()
          }
        }
        BoardText {
          id: status
          anchors { left: defaultMark.right; leftMargin: Style.space(12); right: refreshButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          horizontalAlignment: Text.AlignRight
          elide: Text.ElideLeft
          text: root.statusText()
          color: root.moveError !== "" ? root.urgent : root.boardState === "ready" && root.message === "" && !root.moving ? root.dim : root.accent
          font.pixelSize: Style.font.bodySmall
        }
        BoardText {
          id: refreshButton
          anchors { right: gear.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
          text: "\uf021"
          color: refreshMouse.containsMouse ? root.accent : root.dim
          opacity: root.loading ? 0.5 : 1
          font.pixelSize: Style.font.body
          RotationAnimation on rotation {
            running: root.loading; loops: Animation.Infinite; from: 0; to: 360; duration: 900
            onStopped: refreshButton.rotation = 0
          }
          MouseArea { id: refreshMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.refresh() }
        }
        BoardText {
          id: gear
          anchors { right: parent.right; verticalCenter: parent.verticalCenter }
          text: "\uf013"
          color: gearMouse.containsMouse || root.view === "settings" ? root.accent : root.dim
          font.pixelSize: Style.font.body
          MouseArea { id: gearMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.showView(root.view === "settings" ? "board" : "settings") }
        }
      }

      Item {
        anchors { top: header.bottom; topMargin: root.gap; left: parent.left; right: parent.right; bottom: parent.bottom }
        BoardView { id: boardView; host: root; anchors.fill: parent; visible: root.view === "board" && root.boardState === "ready" }
        IssueView { id: issueView; host: root; anchors.fill: parent; visible: root.view === "issue" }
        Picker { id: picker; host: root; anchors.fill: parent; visible: root.view === "picker" }
        SettingsView { id: settingsView; host: root; anchors.fill: parent; visible: root.view === "settings" }
      }
    }
  }
}
