import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "Logic.js" as Logic
import "components"

// GitLab issue board in the Omarchy bar. Left click opens the popup, right or
// middle click refreshes. Data comes from ./board-fetch through glab: reads are
// GET only; the writes are `board-fetch move` (a card dropped on another column,
// or Shift+H/L; asks first for projects in settings.confirmMoves), and from the
// issue view `comment`, `relabel`, `close` and `reopen`; Sign out runs `logout`.
// Views: the board, one issue, the board picker, settings and the key list.
// Until the first answer, the board shows its saved copy (`board-fetch
// cached`, read at shell start and on switching boards), else a placeholder.
// Selection, per-board collapsed/hidden columns and defaults are saved inline
// in shell.json.
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
  readonly property color dim: Qt.tint(foreground, Qt.rgba(background.r, background.g, background.b, 0.35))
  readonly property color faint: Qt.tint(background, Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12))
  readonly property int columnWidth: Style.space(220)
  readonly property int stripWidth: Style.space(34)
  readonly property int gap: Style.space(10)

  // settings as plain JSON (Logic.plainJson: Qt hands lists over as sequences,
  // which Array.isArray rejects). Read every setting through saved().
  readonly property var savedSettings: Logic.plainJson(settings)
  function saved(name, fallback) {
    var value = savedSettings[name]
    return value === undefined || value === null ? fallback : value
  }

  // Saved default board (empty id = the project's first board). The only
  // place the default project is set: none, so a new install starts in the
  // picker, and the first board opened there becomes the default.
  readonly property string defaultProject: String(saved("defaultProject", "")).trim()
  readonly property string defaultBoardId: String(saved("defaultBoardId", ""))
  readonly property string defaultBoardName: String(saved("defaultBoardName", ""))
  // Board on screen: starts as the default on every shell start; browsing
  // assigns these (breaking the binding) and is never saved.
  property string project: defaultProject
  property string boardId: defaultBoardId
  property string boardName: defaultBoardName
  // Saved preferences.
  property int refreshIntervalSec: Math.max(30, parseInt(String(saved("refreshIntervalSec", 60)), 10) || 60)
  property var defaultCollapsed: Logic.lowerList(saved("defaultCollapsed", ["closed", "research", "open"]))
  // Busy markers (settings.bots, keyed by project; none by default), from the board on screen.
  readonly property var botStates: Logic.botStates(Logic.botsConfig(saved("bots", null), project), columns)
  // Projects whose card moves ask first (settings.confirmMoves; none by default).
  readonly property bool confirmMoves: Logic.has(Logic.lowerList(saved("confirmMoves", [])), project)
  property var boardStates: saved("boardStates", ({})) || ({})

  // Board data from the last fetch.
  readonly property bool loading: fetchProcess.running
  readonly property Item tipArea: keyCatcher  // IconTips stay inside the card
  // A refresh of a board already on screen (button, r or the timer); a saved
  // copy says "updating…" itself.
  readonly property bool refreshing: loading && boardState === "ready" && !cached
  property string boardState: "loading"
  property string message: ""
  property string updatedAt: ""
  property var columns: []
  property var labelColors: ({})
  property string resolvedBoardId: ""
  property bool fallback: false
  property string firstBoardId: ""
  // The board on screen is the saved copy, until the fresh answer replaces it.
  property bool cached: false
  // A refresh failed while a board was on screen: it stays, with this reason
  // kept for the record; the header says "Couldn't refresh · showing HH:MM".
  property string refreshError: ""
  // Widths of boards shown this session, so the placeholder opens at about
  // the right size (Skeleton.qml): { stateKey: px }, and the last one.
  property var boardWidths: ({})
  property int lastBoardWidth: 0
  // First-run panel in place of the board: "no-glab", "logged-out", or
  // "pick" (no project yet); "" once there is a board to load.
  readonly property string setup: boardState === "no-glab" || boardState === "logged-out" ? boardState : project === "" ? "pick" : ""
  // The board could not load and nothing is on screen: SetupView's error step
  // (the reason and Try again) takes the board's place.
  readonly property bool failed: setup === "" && boardState !== "ready" && boardState !== "loading"
  readonly property bool onDefault: project === defaultProject && resolvedBoardId === (defaultBoardId || firstBoardId)
  readonly property string stateKey: project + "#" + (resolvedBoardId || "labels")
  readonly property var boardEntry: boardStates[stateKey] || null
  readonly property var availableColumns: columns.filter(function(c) { return c.name !== "Unlabeled" || (c.issues || []).length > 0 })
  readonly property var shownColumns: availableColumns.filter(function(c) { return !isHidden(c.name) })
  readonly property int boardWidth: shownColumns.reduce(function(sum, c) { return sum + (isCollapsed(c.name) ? stripWidth : columnWidth) + gap }, 0)

  // Keyboard cursor on the board, { col, row, iid } in shownColumns; null
  // (nothing drawn) until the first move after the popup opens.
  property var cursor: null
  readonly property var lanes: shownColumns.map(function(c) { return isCollapsed(c.name) ? null : (c.issues || []).map(function(i) { return i.iid }) })
  onLanesChanged: if (cursor) cursor = Logic.cursorFix(lanes, cursor)
  function moveCursor(dx, dy) { cursor = cursor ? Logic.cursorMove(lanes, cursor, dx, dy) : Logic.cursorFix(lanes, { col: 0, row: 0 }) }
  function cursorIssue() { return cursor ? shownColumns[cursor.col].issues[cursor.row] : null }

  // Views and their data.
  property string view: "board"
  property string pickerStep: "projects"
  property string pickerProject: ""
  property var projects: []
  property var pickerBoards: []
  property bool auxLoading: false
  property string auxError: ""
  property string auxKind: ""
  property var pendingAux: null

  // Drag-to-move: one move at a time, { iid, snapshot, key } while on its way.
  // The card moves at once (optimistic); the snapshot brings it back if GitLab
  // refuses. moveSeq/fetchSeq drop any board answer requested before the latest move.
  property var move: null
  property string moveError: ""
  property int moveSeq: 0
  property int fetchSeq: 0
  readonly property bool canMove: boardState === "ready" && !cached && !fallback && resolvedBoardId !== ""

  // New board data would replace the card being moved or held under the
  // pointer, so while held, board answers are dropped and refetched after.
  readonly property bool held: move !== null || pendingMove !== null || boardView.holding
  // A refresh asked for while busy waits here and runs once nothing is busy.
  readonly property bool busy: loading || held
  property bool refreshQueued: false
  // callLater: a drop starts its move (also callLater) before this runs.
  onBusyChanged: if (!busy && refreshQueued) Qt.callLater(runQueued)
  function runQueued() { if (refreshQueued) { refreshQueued = false; refresh() } }

  function columnAccent(column) {
    if (column.color) return Qt.color(column.color)
    return column.kind === "open" ? accent : column.kind === "closed" ? muted : dim
  }

  // Per board: stored lists win; a board never touched uses defaultCollapsed.
  function collapsedList() { return boardEntry && boardEntry.collapsed ? boardEntry.collapsed : defaultCollapsed }
  function hiddenList() { return boardEntry && boardEntry.hidden ? boardEntry.hidden : [] }
  function isCollapsed(name) { return Logic.has(collapsedList(), name) }
  function isHidden(name) { return Logic.has(hiddenList(), name) }
  function isDefaultCollapsed(name) { return Logic.has(defaultCollapsed, name) }

  function storeBoard(collapsed, hidden) {
    var next = {}
    for (var key in boardStates) next[key] = boardStates[key]
    next[stateKey] = { collapsed: collapsed, hidden: hidden }
    boardStates = next
    persist()
  }
  function toggleCollapsed(name) { storeBoard(Logic.toggled(collapsedList(), name), hiddenList()) }
  function toggleHidden(name) { storeBoard(collapsedList(), Logic.toggled(hiddenList(), name)) }
  function toggleDefaultCollapsed(name) {
    var on = !isDefaultCollapsed(name)
    defaultCollapsed = Logic.toggled(defaultCollapsed, name)
    // Apply to the board on screen too, so the change is visible at once.
    if (isCollapsed(name) !== on) toggleCollapsed(name)
    else persist()
  }
  // One-time update to settings revision 2 (v0.1.3): Open joins the collapsed
  // defaults and every saved board, without touching anything else. Runs again
  // only if it could not be saved.
  readonly property int settingsRevision: 2
  function migrateSettings() {
    if ((parseInt(String(saved("settingsRevision", 1)), 10) || 1) >= settingsRevision) return
    if (!bar || !bar.shell || typeof bar.shell.updateEntryInline !== "function") return
    if (saved("defaultCollapsed", null) === null && saved("boardStates", null) === null) return  // nothing saved yet
    // Read the saved values directly: the property bindings may not have caught up.
    var collapsed = Logic.lowerList(saved("defaultCollapsed", ["closed", "research"]))
    var states = saved("boardStates", ({})) || ({})
    var next = {}
    for (var key in states) {
      var entry = states[key] || {}
      next[key] = Array.isArray(entry.collapsed) && !Logic.has(entry.collapsed, "open")
        ? { collapsed: entry.collapsed.concat(["open"]), hidden: entry.hidden || [] } : entry
    }
    defaultCollapsed = Logic.has(collapsed, "open") ? collapsed : collapsed.concat(["open"])
    boardStates = next
    persist()
  }
  onSettingsChanged: Qt.callLater(migrateSettings)

  function setRefreshInterval(seconds) { refreshIntervalSec = seconds; persist() }

  // Same write path as built-in widgets: merge into the inline entry and hand
  // it to the shell facade. Without the facade the state stays in memory.
  // nextDefault ({ project, id, name }) replaces the saved default board.
  // nextBots replaces settings.bots (Settings > Bots); otherwise it is kept as saved.
  function persist(nextDefault, nextBots) {
    if (!bar || !bar.shell || typeof bar.shell.updateEntryInline !== "function") return
    var d = nextDefault || { project: defaultProject, id: defaultBoardId, name: defaultBoardName }
    var entry = { id: moduleName }
    var dropped = ["id", "collapsedColumns", "hiddenColumns", "project", "boardId", "boardName"]
    for (var key in savedSettings) if (dropped.indexOf(key) === -1) entry[key] = savedSettings[key]
    entry.defaultProject = d.project
    entry.defaultBoardId = d.id
    entry.defaultBoardName = d.name
    entry.refreshIntervalSec = refreshIntervalSec
    entry.defaultCollapsed = defaultCollapsed
    entry.boardStates = boardStates
    entry.settingsRevision = settingsRevision
    if (nextBots !== undefined) entry.bots = nextBots
    bar.shell.updateEntryInline(moduleName, entry)
  }
  function saveBots(next) { persist(undefined, next) }

  function helperPath() {
    return decodeURIComponent(Qt.resolvedUrl("board-fetch").toString().replace(/^file:\/\//, ""))
  }

  function refresh() {
    if (signingOut) return
    // No project yet: the project list doubles as the sign-in check, and
    // landing in the picker is the next step.
    if (project === "") { boardState = "loading"; runAux("projects", []); return }
    readCache()
    if (busy) { refreshQueued = true; return }
    fetchSeq = moveSeq
    fetchProcess.session = session
    fetchProcess.command = [helperPath(), "board", "--project", project, "--board", boardId]
    fetchProcess.running = true
  }

  function parse(raw) {
    try { return JSON.parse(String(raw || "")) } catch (error) { return { state: "error", message: "board-fetch returned no readable output." } }
  }

  // The saved copy, only while nothing is on screen: no GitLab call.
  function readCache() {
    if (project === "" || boardState !== "loading" || cacheProcess.running) return
    cacheProcess.key = project + "#" + boardId
    cacheProcess.session = session
    cacheProcess.command = [helperPath(), "cached", "--project", project, "--board", boardId]
    cacheProcess.running = true
  }
  function applyCache(raw, key) {
    if (boardState === "loading" && key === project + "#" + boardId && parse(raw).cached === true) apply(raw, true)
  }

  function apply(raw, fromCache) {
    var data = parse(raw)
    if (data.project && data.project !== project) return  // answer for a project we already left
    if (held || fetchSeq !== moveSeq) { refreshQueued = true; return }  // mid-drag or mid-move, or older than the latest move
    // A failed refresh keeps the board on screen (sign-in problems still show
    // the sign-in panel); only with nothing loaded does the error take its place.
    if (data.state === "error" && boardState === "ready" && columns.length > 0) { refreshError = String(data.message || "Could not load issues."); return }
    refreshError = ""
    cached = !!fromCache
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
    if (columns.length > 0) {
      var widths = Object.assign({}, boardWidths)
      widths[stateKey] = boardWidth
      boardWidths = widths
      lastBoardWidth = boardWidth
    }
  }

  // Columns a card can be dropped on: Open, Closed and label lists of a real
  // board (not the workflow-label fallback, not assignee/milestone lists).
  function canDrop(column) {
    return canMove && !!column && (column.kind === "open" || column.kind === "closed" || (column.kind === "label" && !!column.listId))
  }
  // A drop or Shift+H/L. With confirmMoves on for this project the move waits
  // in pendingMove for Move or Enter (MoveConfirm.qml); Cancel or Escape drops it.
  property var pendingMove: null
  function requestMove(row, from, to) {
    if (move || pendingMove || !row || !canDrop(from) || !canDrop(to) || Logic.columnKey(from) === Logic.columnKey(to)) return false
    if (!confirmMoves) return moveIssue(row, from, to)
    pendingMove = { row: row, from: from, to: to, key: stateKey }
    return true
  }
  function confirmMove() {
    var p = pendingMove
    pendingMove = null
    if (p && p.key === stateKey) moveIssue(p.row, p.from, p.to)
  }
  function cancelMove() { pendingMove = null }
  // Shift+H/L: the selected card to the nearest column it can go to on that side.
  function moveCursorCard(dx) {
    var row = cursorIssue()
    if (!row) return
    var from = shownColumns[cursor.col]
    for (var i = cursor.col + dx; i >= 0 && i < shownColumns.length; i += dx)
      if (canDrop(shownColumns[i])) { requestMove(row, from, shownColumns[i]); return }
  }
  function moveIssue(row, from, to) {
    // moveProcess can outlive move: the watchdog gives up on it, board-fetch's own timeouts end it.
    if (move || moveProcess.running || !row || !canDrop(from) || !canDrop(to) || Logic.columnKey(from) === Logic.columnKey(to)) return false
    move = { iid: row.iid, snapshot: columns, key: stateKey }
    moveError = ""
    moveSeq++
    columns = Logic.movedColumns(columns, row, from, to)
    moveProcess.command = [helperPath(), "move", "--project", project, "--board", resolvedBoardId,
      "--iid", String(row.iid), "--from", Logic.listSpec(from), "--to", Logic.listSpec(to)]
    moveProcess.running = true
    moveWatchdog.restart()
    return true
  }

  function moveDone(raw) {
    if (!move) return  // late answer after the watchdog gave up
    moveWatchdog.stop()
    var data = parse(raw)
    if (data.state !== "ready") {
      if (move.key === stateKey) columns = move.snapshot
      moveError = String(data.message || "Move failed.")
      moveErrorTimer.restart()
    }
    // Success, or a card that was out of date ("stale": board-fetch wrote
    // nothing): load the board as GitLab now has it. Other failures: only if a
    // refresh was due. It runs once the move is cleared (onBusyChanged).
    if (data.state === "ready" || data.state === "stale") refreshQueued = true
    move = null
  }

  function runAux(kind, args) {
    if (auxProcess.running) { pendingAux = { kind: kind, args: args }; return }
    auxKind = kind
    auxProcess.session = session
    auxError = ""
    auxLoading = true
    auxProcess.command = [helperPath(), kind].concat(args)
    auxProcess.running = true
  }

  function applyAux(raw) {
    var data = parse(raw)
    var error = data.state === "ready" ? "" : String(data.message || "Request failed.")
    var kind = data.projects ? "projects" : data.boards ? "boards" : auxKind
    auxLoading = false
    auxError = error
    if (kind === "whoami") { account = error ? "" : String(data.user || ""); accountError = data.state === "logged-out" ? "" : error }
    // Not set up: the first-run panel replaces the picker.
    if (data.state === "no-glab" || data.state === "logged-out") { boardState = data.state; message = String(data.message || ""); showView("board"); return }
    if (kind === "projects" && project === "") {
      boardState = error ? "error" : "ready"
      message = error
      if (!error && view === "board") pickProjectStep()
    }
    if (kind === "projects") projects = data.projects || []
    else if (kind === "boards") {
      var boards = data.boards || []
      pickerBoards = boards.length > 0 || error ? boards : [{ id: "", name: "Workflow labels (no boards)" }]
    }
  }

  function showView(name) {
    if (name === "settings" && view !== "settings") checkAccount()
    view = name
    Qt.callLater(function() {
      if (name === "picker" && picker.filterField.visible) picker.filterField.forceActiveFocus()
      else keyCatcher.forceActiveFocus()
    })
  }
  function back() { showView("board") }
  function toggleView(name) { showView(view === name ? "board" : name) }

  function openIssue(row) {
    issueView.issue = row  // the card at once; the view loads the rest
    showView("issue")
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
    showView("picker")  // the filter hides: keys back to the panel
    runAux("boards", ["--project", path])
  }
  function pickBoard(b) { switchTo(pickerProject, String(b.id || ""), b.id ? String(b.name) : "") }
  function openDefault() { switchTo(defaultProject, defaultBoardId, defaultBoardName) }
  function switchTo(path, id, name) {
    project = path
    boardId = id
    boardName = name
    columns = []
    cached = false
    resolvedBoardId = id
    firstBoardId = ""
    moveError = ""
    refreshError = ""
    pendingMove = null
    boardState = "loading"
    if (defaultProject === "") persist({ project: path, id: id, name: name })  // first board: the default
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

  // https only, so no file:, javascript: or --flag value reaches the browser.
  function openUrl(url) {
    if (!/^https:\/\//.test(String(url || ""))) return
    Quickshell.execDetached(["omarchy-launch-browser", String(url)])
    close()
  }

  // Account (settings only). The username stays in memory, never on disk.
  property string account: ""
  property string accountError: ""
  function checkAccount() { account = ""; accountError = ""; runAux("whoami", []) }
  // Sign out: board-fetch runs glab auth logout (no prompt; glab forgets the
  // token for every glab user on this machine) and deletes the saved boards.
  // Answers to requests made before it are dropped (session), and nothing
  // refreshes meanwhile; the popup then shows the sign-in panel.
  property bool signingOut: false
  property int session: 0
  function signOut() {
    if (signingOut) return
    signingOut = true
    accountError = ""
    logoutProcess.command = [helperPath(), "logout"]
    logoutProcess.running = true
  }
  function signedOut(raw) {
    var data = parse(raw)
    signingOut = false
    if (data.state !== "logged-out") { accountError = String(data.message || "Could not sign out."); return }
    session++
    columns = []; projects = []; pickerBoards = []; cached = false; account = ""; refreshError = ""; pendingMove = null
    message = String(data.message || ""); boardState = "logged-out"
    showView("board")
  }

  // First run. glab asks for the token in its own terminal: this plugin never
  // sees it. Same launcher as Omarchy's update widget (SystemUpdate.qml).
  readonly property string installCommand: "sudo pacman -S glab"
  readonly property string icon: "\uf296"  // Font Awesome gitlab (Nerd Font): the bar icon and the setup panel
  function signIn() {
    Quickshell.execDetached(["omarchy-launch-floating-terminal-with-presentation", "glab auth login"])
    close()
  }
  function copyInstall() { Quickshell.execDetached(["wl-copy", installCommand]) }

  function statusText() {
    if (moveError !== "") return moveError
    if (move) return "Moving #" + move.iid + "…"
    if (refreshing) return message !== "" ? message + "  Refreshing…" : "Refreshing…"
    if (boardState === "ready" && refreshError !== "")
      return "Couldn't refresh · showing " + (updatedAt !== "" ? new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : "the last board")
    if (boardState === "ready" && cached) return Logic.savedNote(updatedAt)
    if (boardState === "ready") {
      var time = updatedAt !== "" ? "Updated " + new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : ""
      return message !== "" ? message + "  " + time : time
    }
    if (view === "board" && (setup !== "" || failed || boardState === "loading")) return ""  // the board body says it
    if (project === "") return ""
    if (boardState === "loading") return "Loading GitLab issues…"
    if (boardState === "logged-out") return message || "Not signed in. Run: glab auth login"
    return message || "Could not load issues."
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component.onCompleted: Qt.callLater(readCache)
  onOpenedChanged: if (opened) { view = "board"; cursor = null; refresh() } else { boardView.endDrag(); pendingMove = null }

  // Only while the popup is open; opening it refreshes (onOpenedChanged).
  Timer {
    id: refreshTimer
    interval: root.refreshIntervalSec * 1000
    repeat: true; running: root.opened && root.setup === ""
    onTriggered: root.refresh()
  }

  Process {
    id: fetchProcess
    property int session: 0  // root.session it was started in
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: if (fetchProcess.session === root.session) root.apply(text) }
  }

  Process {
    id: cacheProcess
    property string key: ""  // project#boardId it was asked for
    property int session: 0
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: if (cacheProcess.session === root.session) root.applyCache(text, cacheProcess.key) }
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
    property int session: 0
    onExited: if (root.pendingAux) { var next = root.pendingAux; root.pendingAux = null; Qt.callLater(function() { root.runAux(next.kind, next.args) }) }
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: if (auxProcess.session === root.session) root.applyAux(text); else root.auxLoading = false }
  }

  Process {
    id: logoutProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: root.signedOut(text) }
  }

  BarIconButton {
    id: button
    anchors.fill: parent; bar: root.bar
    text: root.icon
    tooltipText: "GitLab board" + (root.project !== "" ? " · " + root.project : "")
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
    contentWidth: panel.fittedContentWidth(Math.max(Style.space(520), root.view === "keys" ? Style.space(760) : root.view !== "board" ? 0
      : (root.setup !== "" || root.failed || root.boardState === "loading" ? skeleton.implicitWidth : root.boardWidth) + panel.padding * 2 + Style.space(4)))
    contentHeight: panel.fittedContentHeight(keyCatcher.implicitHeight, Style.space(640))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      blocked: issueView.typing || picker.typing || settingsView.typing  // text fields get every key (Omarchy PanelKeyCatcher.qml:26-29)
      implicitHeight: header.implicitHeight + root.gap + (botsRow.visible ? botsRow.height + root.gap : 0) + (moveConfirm.visible ? moveConfirm.height + root.gap : 0) + (root.view === "board" ? (root.setup !== "" || root.failed ? Math.max(setupView.implicitHeight, skeleton.implicitHeight) : root.boardState === "loading" ? skeleton.implicitHeight : boardView.implicitHeight)
        : root.view === "issue" ? issueView.implicitHeight : root.view === "picker" ? picker.implicitHeight
        : root.view === "keys" ? keysView.implicitHeight : settingsView.implicitHeight)
      onCloseRequested: {
        if (root.pendingMove) root.cancelMove()
        else if (root.view === "issue" && issueView.confirming) issueView.confirming = false
        else if (root.view === "issue" && issueView.editing) issueView.doneEditing()  // labels still loading: the filter is off
        else if (root.view === "settings" && settingsView.adding) settingsView.cancelAdd()
        else if (root.view !== "board") root.back()
        else root.close()
      }
      onDeleteRequested: if (root.view === "issue" && !issueView.editing) issueView.toggleState()  // x; not while labels load
      onTabRequested: function(direction) { root.switchPanel(direction) }
      onMoveRequested: function(dx, dy) {
        if (root.view === "board") root.moveCursor(dx, dy)
        else if (root.view === "picker" && dy !== 0) picker.moveCursor(dy)
      }
      onActivateRequested: {
        if (root.pendingMove) root.confirmMove()
        else if (root.view === "issue" && issueView.confirming) issueView.setState("close")
        else if (root.view === "board" && root.cursorIssue()) root.openIssue(root.cursorIssue())
        else if (root.view === "picker") picker.activate()
        else if (root.view === "board" && (root.setup !== "" || root.failed)) setupView.primary()
      }
      onTextKey: function(text) {
        if (root.pendingMove) return  // Enter or Escape first
        if (root.view === "issue" && issueView.editing) return  // typed for the filter while labels load
        if ((text === "H" || text === "L") && root.view === "board") { root.moveCursorCard(text === "H" ? -1 : 1); return }
        var key = text.toLowerCase()
        if (key === "r" && root.view === "board") root.refresh()
        else if (key === "o") {
          var row = root.view === "issue" ? issueView.issue : root.view === "board" ? root.cursorIssue() : null
          if (row) root.openUrl(row.url)
        }
        else if (key === "c" && root.view === "issue") issueView.focusBox()
        else if (key === "e" && root.view === "issue") issueView.editLabels()
        else if (key === "p") root.openPicker()
        else if (key === "s") root.toggleView("settings")
        else if (key === "?") root.toggleView("keys")
      }

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
        // The title gets all the room the rest of the row doesn't need; the
        // status gets at most 40% of it, and elides from the left.
        readonly property real titleRoom: width - chevron.implicitWidth - defaultMark.implicitWidth - refreshButton.implicitWidth - keysButton.implicitWidth - gear.implicitWidth
          - Style.space(8 + 12 + 8 + 10 + 10) - Math.min(status.implicitWidth, width * 0.4)

        // Elides at the end, so the board name goes before the project.
        BoardText {
          id: title
          anchors.verticalCenter: parent.verticalCenter
          width: Math.max(0, Math.min(implicitWidth, header.titleRoom))
          elide: Text.ElideRight
          text: root.project === "" ? "GitLab board" : root.project + (root.boardName !== "" ? " · " + root.boardName : "")
          color: titleMouse.containsMouse ? root.accent : root.foreground
          font { pixelSize: Style.font.title; bold: true }
        }
        BoardText {
          id: chevron
          anchors { left: title.right; verticalCenter: parent.verticalCenter }
          text: " ▾"
          color: title.color
          font: title.font
        }
        MouseArea {
          id: titleMouse
          x: title.x; width: chevron.x + chevron.width - title.x; height: parent.height
          hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.openPicker()
          IconTip { host: root; shown: titleMouse.containsMouse; text: "Switch project or board (p)" }
        }
        BoardText {
          id: defaultMark
          anchors { left: chevron.right; leftMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          text: root.project === "" ? "" : root.onDefault ? "\uf005" : "\uf006 Default"
          color: root.onDefault || defaultMouse.containsMouse ? root.accent : root.dim
          font.pixelSize: Style.font.bodySmall
          MouseArea {
            id: defaultMouse; anchors.fill: parent; anchors.margins: -Style.space(4)
            enabled: root.project !== ""; hoverEnabled: true; cursorShape: root.onDefault ? Qt.ArrowCursor : Qt.PointingHandCursor
            onClicked: if (!root.onDefault) root.openDefault()
          }
          IconTip { host: root; shown: defaultMouse.containsMouse; text: root.onDefault ? "Your default board" : "Go to your default board" }
        }
        BoardText {
          id: status
          anchors { left: defaultMark.right; leftMargin: Style.space(12); right: refreshButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
          horizontalAlignment: Text.AlignRight
          elide: Text.ElideLeft
          text: root.statusText()
          color: root.moveError !== "" || (root.refreshError !== "" && root.boardState === "ready" && !root.refreshing) ? root.urgent : root.boardState === "ready" && root.message === "" && !root.move && !root.cached ? root.dim : root.accent
          font.pixelSize: Style.font.bodySmall
        }
        BoardText {
          id: refreshButton
          anchors { right: keysButton.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
          text: "\uf021"
          color: refreshMouse.containsMouse ? root.accent : root.dim
          font.pixelSize: Style.font.body
          // Spins while the board loads (as Omarchy's Ui/Button.qml spins its
          // icon) and finishes the turn it is on, so it always stops upright.
          RotationAnimation on rotation { running: root.loading; alwaysRunToEnd: true; loops: Animation.Infinite; from: 0; to: 360; duration: 900 }
          MouseArea { id: refreshMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.refresh() }
          IconTip { host: root; shown: refreshMouse.containsMouse; text: "Refresh (r)" }
        }
        // The keyboard shortcuts (KeysView), like ? does.
        BoardText {
          id: keysButton
          anchors { right: gear.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
          text: "\uf11c"
          color: keysMouse.containsMouse || root.view === "keys" ? root.accent : root.dim
          font.pixelSize: Style.font.body
          MouseArea { id: keysMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleView("keys") }
          IconTip { host: root; shown: keysMouse.containsMouse; text: "Keyboard shortcuts (?)" }
        }
        BoardText {
          id: gear
          anchors { right: parent.right; verticalCenter: parent.verticalCenter }
          text: "\uf013"
          color: gearMouse.containsMouse || root.view === "settings" ? root.accent : root.dim
          font.pixelSize: Style.font.body
          MouseArea { id: gearMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.toggleView("settings") }
          IconTip { host: root; shown: gearMouse.containsMouse; text: "Settings (s)" }
        }
      }

      BotsRow {
        id: botsRow
        host: root
        states: root.botStates
        visible: root.view === "board" && root.setup === "" && root.boardState === "ready" && root.botStates.length > 0
        anchors { top: header.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      MoveConfirm {
        id: moveConfirm
        host: root
        pending: root.pendingMove
        visible: root.view === "board" && root.pendingMove !== null
        anchors { top: botsRow.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      Item {
        anchors { top: moveConfirm.bottom; topMargin: root.gap; left: parent.left; right: parent.right; bottom: parent.bottom }
        SetupView { id: setupView; host: root; anchors.fill: parent; visible: root.view === "board" && (root.setup !== "" || root.failed) }
        Skeleton { id: skeleton; host: root; anchors.fill: parent; visible: root.view === "board" && root.setup === "" && root.boardState === "loading" }
        BoardView { id: boardView; host: root; anchors.fill: parent; visible: root.view === "board" && root.setup === "" && root.boardState === "ready" }
        IssueView { id: issueView; host: root; anchors.fill: parent; visible: root.view === "issue" }
        Picker { id: picker; host: root; anchors.fill: parent; visible: root.view === "picker" }
        SettingsView { id: settingsView; host: root; anchors.fill: parent; visible: root.view === "settings" }
        KeysView { id: keysView; host: root; anchors.fill: parent; visible: root.view === "keys" }
      }
    }
  }
}
