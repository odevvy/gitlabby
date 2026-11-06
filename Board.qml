import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "Logic.js" as Logic
import "components"

// GitLab issue board in the Omarchy bar. Left click opens the popup, right or
// middle click refreshes. The board comes from BoardService.qml, shared by the
// copies of this widget on every screen (one fetch for all of them); the rest
// from ./board-fetch through glab directly: reads are
// GET only; the writes are `board-fetch move` (a card dropped on another column,
// or Shift+H/L; asks first for projects in settings.confirmMoves), and from the
// issue view `comment`, `relabel`, `close` and `reopen`; Sign out runs `logout`.
// Picked cards (v, Ctrl+click) take the same writes in bulk (BulkBar.qml).
// Views: the board, one issue, the board picker, settings and the key list.
// Until the first answer, the board shows its saved copy (`board-fetch
// cached`, read at shell start and on switching boards), else a placeholder.
// Selection, per-board collapsed/hidden columns and defaults are saved inline
// in shell.json.
Panel {
  id: root
  moduleName: "odevvy.gitlabby"
  ipcTarget: "odevvy.gitlabby"

  readonly property color foreground: Commons.Color.popups.text
  readonly property color accent: Commons.Color.accent
  readonly property color background: Commons.Color.popups.background
  readonly property color muted: Commons.Color.muted
  readonly property color urgent: Commons.Color.urgent
  // Solid blends so they also work inside StyledText markup.
  readonly property color dim: Qt.tint(foreground, Qt.rgba(background.r, background.g, background.b, 0.35))
  readonly property color faint: Qt.tint(background, Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12))
  // Third text level (counts, hints, empty states, "Updated"): quieter than dim.
  readonly property color quiet: Qt.tint(foreground, Qt.rgba(background.r, background.g, background.b, 0.55))
  // The show/hide-columns row under the bots, opened from the header (BoardView.qml).
  property bool columnChips: false
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

  // The GitLab server (settings.gitlabHost; gitlab.com by default), as a bare
  // name (Logic.serverHost); every board-fetch call gets it as --hostname
  // (helperCommand). One that isn't a bare name (http, a port, a path) counts
  // as gitlab.com. Another server keeps its own default board, bots, alerts,
  // confirm moves and column state (projectKey); gitlab.com's stay as before.
  readonly property string gitlabHost: Logic.serverHost(saved("gitlabHost", "gitlab.com")) || "gitlab.com"
  readonly property bool onGitlabCom: gitlabHost === "gitlab.com"
  readonly property string projectKey: Logic.serverKey(gitlabHost, project)
  readonly property string loginCommand: Logic.signInCommand(gitlabHost)  // runs in a shell: see Logic.signInCommand
  // The setting as saved: Settings shows it, with the error, when it isn't a
  // bare name (the board then uses gitlab.com until it is fixed there).
  readonly property string savedHost: String(saved("gitlabHost", "gitlab.com"))
  readonly property bool hostInvalid: savedHost.trim() !== "" && Logic.serverHost(savedHost) === ""
  // Settings > GitLab server's Use: saves a bare name (switchServer follows).
  function useServer(raw) {
    var h = Logic.serverHost(raw)
    if (h === "") return false
    if (h !== gitlabHost || hostInvalid) persist({ gitlabHost: h })
    return true
  }
  // The setup panel's Change server: Settings, with the server field focused.
  function changeServer() { showView("settings"); Qt.callLater(settingsView.focusServer) }
  // Saved default board (empty id = the project's first board). The only
  // place the default project is set: none, so a new install starts in the
  // picker, and the first board opened there becomes the default. gitlab.com's
  // is defaultProject/Id/Name; another server's is settings.serverDefaults[host].
  readonly property var hostDefault: onGitlabCom
    ? { project: saved("defaultProject", ""), id: saved("defaultBoardId", ""), name: saved("defaultBoardName", "") }
    : Object(saved("serverDefaults", ({})))[gitlabHost] || ({})
  readonly property string defaultProject: String(hostDefault.project || "").trim()
  readonly property string defaultBoardId: String(hostDefault.id || "")
  readonly property string defaultBoardName: String(hostDefault.name || "")
  // Favorited boards for this host (header jump list). gitlab.com: settings.favorites;
  // another server: settings.serverFavorites[host]. The default is merged into the
  // list even when it is not stored here (Logic.jumpBoards).
  readonly property var hostFavorites: Logic.hostFavorites(saved("favorites", []), saved("serverFavorites", ({})), gitlabHost, onGitlabCom)
  readonly property var jumpBoards: Logic.jumpBoards(hostFavorites, defaultProject, defaultBoardId, defaultBoardName)
  // Header menus: "" | "default" | "jump". Esc and choosing a row clear it.
  property string headerMenu: ""
  onViewChanged: headerMenu = ""
  // Board on screen: starts as the default on every shell start; browsing
  // assigns these (breaking the binding) and is never saved.
  property string project: defaultProject
  property string boardId: defaultBoardId
  property string boardName: defaultBoardName
  // Saved preferences.
  property int refreshIntervalSec: Math.max(30, parseInt(String(saved("refreshIntervalSec", 60)), 10) || 60)
  // Settings > Open links in: "browser" (a tab, omarchy-launch-browser, the
  // default) or "app" (its own window, omarchy-launch-webapp). See openUrl.
  // The bar icon's dot after an alert (alertDot), unless Settings keeps it unlit.
  readonly property bool iconUnlit: saved("iconUnlit", false) === true
  readonly property bool iconLit: !iconUnlit && !!feed && feed.unseenAlerts > 0
  function setIconUnlit(on) { persist({ iconUnlit: on === true }) }
  // Avatar pictures come from outside sites (Gravatar and the like), which see
  // the shell's IP; off, every avatar is its initials circle (Avatar.qml).
  readonly property bool showAvatars: saved("showAvatars", true) !== false
  function setShowAvatars(on) { persist({ showAvatars: on === true }) }
  readonly property string linkMode: String(saved("openLinks", "browser")) === "app" ? "app" : "browser"
  function setLinkMode(mode) { persist({ openLinks: mode === "app" ? "app" : "browser" }) }
  // The interval actually used: the setting, faster while cards move, slower
  // while nothing changes (Logic.adaptiveInterval), from the shared pace.
  readonly property var cadence: Logic.adaptiveInterval(refreshIntervalSec, feed.paces[fetchKey])
  property var defaultCollapsed: Logic.lowerList(saved("defaultCollapsed", ["closed", "research", "open"]))
  // Busy markers (settings.bots, keyed by projectKey; none by default), from the board on screen.
  readonly property var botStates: Logic.botStates(Logic.botsConfig(saved("bots", null), projectKey), columns)
  // Desktop alerts for the project on screen (settings.alerts; off by default).
  // While one is on, the shared service watches this board and notifies
  // (BoardService.qml watch); one per event. A card or bot alert refreshes the
  // board with the popup closed; the pipeline one (v0.1.76) asks only for your
  // open MRs there (board-fetch pipes).
  // A click on one opens its link as Settings > Open links in says (links).
  readonly property var alerts: Logic.alertsFor(saved("alerts", null), projectKey)
  readonly property string watchOwner: "w" + Math.floor(Math.random() * 1e9)
  readonly property var watchCfg: project !== "" && setup === "" && (alerts.review || alerts.idle || alerts.pipeline)
    ? { key: fetchKey, project: project, boardId: boardId, review: alerts.review, idle: alerts.idle, pipeline: alerts.pipeline, bots: saved("bots", null), base: refreshIntervalSec, host: gitlabHost, links: linkMode } : null
  onWatchCfgChanged: feed.watch(watchOwner, watchCfg)
  Component.onDestruction: { saveFolds(); feed.watch(watchOwner, null) }
  function setAlert(kind, on) { persist({ alerts: Logic.withAlert(saved("alerts", null), projectKey, kind, on) }) }
  // Projects whose card moves ask first (settings.confirmMoves; none by default).
  readonly property bool confirmMoves: Logic.has(Logic.lowerList(saved("confirmMoves", [])), projectKey)
  property var boardStates: saved("boardStates", ({})) || ({})
  readonly property Item avatarMask: sharedAvatarMask

  // The shared board fetch (BoardService.qml): the shell's one service when the
  // built-in bar hosts this widget (PluginShellApi.serviceFor), else a private one.
  readonly property var sharedFeed: bar && bar.shell && typeof bar.shell.serviceFor === "function" ? bar.shell.serviceFor(moduleName) : null
  readonly property var feed: sharedFeed || localFeed
  readonly property string fetchKey: feed.keyOf(project, boardId)
  // Board data from the last fetch. loading: this board is being fetched,
  // whichever screen asked.
  readonly property bool loading: project !== "" && (feed.runningKey === fetchKey || feed.queuedKeys.indexOf(fetchKey) !== -1)
  readonly property Item tipArea: keyCatcher  // IconTips stay inside the card
  // A refresh of a board already on screen (button, r or the timer); a saved
  // copy says "updating…" itself.
  readonly property bool refreshing: loading && boardState === "ready" && !cached
  // Any refresh on its way while the popup is open, manual or automatic: the
  // board, or the merge-request list on screen, or the to-dos already shown
  // (their first load is TodoView's own spinner row). The header bar slides
  // and the refresh icon spins on it; the cards stay.
  // The list views (ScopedList), by view name: showView opens one, and the
  // header's Updated and refresh follow the one on screen (shownList).
  readonly property var lists: ({ mrs: mrsView, todos: todoView })
  readonly property Item shownList: lists[view] || null
  readonly property bool listBusy: shownList !== null && shownList.busy
  readonly property bool refreshActive: opened && (loading || listBusy || updating)
  // A refresh you asked for (Refresh, r, a click on the icon), not the timer's
  // or the one opening the popup runs: set by each refresh(). It, the first
  // load and the merge-request list loading are "loud": the icon spins and
  // the status dot is accent. A background refresh only breathes the dot, grey.
  property bool manualRefresh: false
  readonly property bool loudNow: opened && ((loading && (manualRefresh || boardState !== "ready")) || listBusy)
  // A refresh you asked for on a loaded board says "Updating…" for at least
  // half a second (with the dot and the icon), so a quick answer reads as
  // Updating… then Updated, not a flicker. Not the first load, not closed.
  readonly property bool updatingNow: loudNow && boardState === "ready"
  property bool refreshHeld: false
  Timer { id: refreshHold; interval: 500; onTriggered: root.refreshHeld = false }
  readonly property bool updating: updatingNow || (refreshHeld && opened && boardState === "ready")
  readonly property bool loudRefresh: loudNow || updating
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
  readonly property string stateKey: projectKey + "#" + (resolvedBoardId || "labels")
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
  // refuses. moveFloor: board answers from fetches started before the latest
  // move (feed tickets below it) are dropped, and the board is fetched again.
  property var move: null
  property string moveError: ""
  // A write the watchdog gave up on that board-fetch hasn't ended yet.
  readonly property string stillFinishing: "The last change is still finishing on GitLab. Try again in a moment."
  readonly property bool moveStillRunning: move === null && moveProcess.running
  function noteStillFinishing() { moveError = stillFinishing; moveErrorTimer.restart(); return false }
  property int moveFloor: 0
  readonly property bool canMove: boardState === "ready" && !cached && !fallback && resolvedBoardId !== "" && writable
  // Write access on this project (BoardService access, asked once per project
  // when its board loads): accessNote "" (writes on), "view-only" or
  // "read-token" turns moves, bulk actions, labels and close off, and
  // AccessHint.qml says why until Not now (saved per project).
  readonly property var accessEntry: project !== "" ? feed.access[project] || null : null
  readonly property string accessNote: Logic.accessNote(accessEntry)
  readonly property bool writable: accessNote === ""
  readonly property bool hintDismissed: Logic.has(Logic.lowerList(saved("accessHintDismissed", [])), projectKey)
  function dismissHint() { if (!hintDismissed) persist({ accessHintDismissed: Logic.lowerList(saved("accessHintDismissed", [])).concat([projectKey.toLowerCase()]) }) }

  // New board data would replace the card being moved or held under the
  // pointer, so while held, board answers are dropped and refetched after.
  // A fold or hide in progress (folding) holds answers too, so a refresh never
  // rebuilds the board under the animation; it lands right after.
  readonly property bool held: move !== null || pendingMove !== null || boardView.holding || bulkBar.busy || bulkBar.armed || folding
  // A refresh asked for while busy waits here and runs once nothing is busy.
  readonly property bool busy: loading || held
  property bool refreshQueued: false
  // callLater: a drop starts its move (also callLater) before this runs.
  onBusyChanged: if (!busy && refreshQueued) Qt.callLater(runQueued)
  function runQueued() { if (refreshQueued) { refreshQueued = false; refresh(true) } }

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

  // Folds and hides change boardStates in memory at once and are saved later:
  // when the popup closes, or 2 s after the last one (foldSave). Each save
  // rewrites shell.json, and Omarchy reloads its shell-wide state on that, which
  // froze the fold animation when it happened on every click.
  property bool foldsUnsaved: false
  function storeBoard(collapsed, hidden) {
    var next = {}
    for (var key in boardStates) next[key] = boardStates[key]
    next[stateKey] = { collapsed: collapsed, hidden: hidden }
    boardStates = next
    foldsUnsaved = true
    foldSave.restart()
  }
  function saveFolds() { if (foldsUnsaved) persist() }
  // folding: true for a moment after a fold or hide. Only then do the column
  // and the popup's width animate (board and view switches stay
  // instant), and answers wait (held).
  property bool folding: false
  function startFold() { folding = true; foldClock.restart() }
  function toggleCollapsed(name) { startFold(); storeBoard(Logic.toggled(collapsedList(), name), hiddenList()) }
  function toggleHidden(name) { startFold(); storeBoard(collapsedList(), Logic.toggled(hiddenList(), name)) }
  function toggleDefaultCollapsed(name) {
    var on = !isDefaultCollapsed(name)
    defaultCollapsed = Logic.toggled(defaultCollapsed, name)
    // Apply to the board on screen too, so the change is visible at once.
    if (isCollapsed(name) !== on) toggleCollapsed(name)
    persist()  // a Settings change: saved now
  }
  Timer { id: foldSave; interval: 2000; onTriggered: root.saveFolds() }
  Timer { id: foldClock; interval: 200; onTriggered: root.folding = false }
  // The popup edge follows the columns while they fold.
  property real shownBoardWidth: boardWidth
  Behavior on shownBoardWidth { enabled: root.folding; NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
  // One-time update to settings revision 2 (v0.1.3): Open joins the collapsed
  // defaults and every saved board, without touching anything else. Runs again
  // only if it could not be saved.
  readonly property int settingsRevision: 2
  onSettingsChanged: Qt.callLater(migrateSettings)

  function setRefreshInterval(seconds) { refreshIntervalSec = seconds; persist() }

  // Same write path as built-in widgets: merge into the inline entry and hand
  // it to the shell facade. Without the facade the state stays in memory.
  // patch: settings keys to set (bots, alerts, openLinks, …); the rest are kept
  // as saved. patch.board ({ project, id, name }) replaces the saved default
  // board (this server's: on another one, settings.serverDefaults[host];
  // gitlab.com's stays).

  // ifDue (the timer, opening the popup): skipped when this board was fetched
  // less than an interval ago, on any screen; that answer is shown instead.
  // Otherwise (Refresh, r, a click on the icon) it is fetched, unless a fetch
  // is already on its way, which every screen then shows.
  function refresh(ifDue) {
    if (signingOut) return
    // No project yet: the project list doubles as the sign-in check, and
    // landing in the picker is the next step.
    if (project === "") { boardState = "loading"; runAux("projects", []); return }
    readCache()
    if (held) { refreshQueued = true; return }
    // A refresh you asked for stays loud until its answer, even if the
    // popup opening (or the timer) joins it meanwhile.
    manualRefresh = ifDue !== true || (manualRefresh && loading)
    if (ifDue !== true && boardState === "ready" && opened) { refreshHeld = true; refreshHold.restart() }  // "Updating…" at least 500 ms
    var last = feed.request(project, boardId, ifDue === true, cadence.sec * 1000 - 2000, moveFloor)
    if (last) apply(last.raw, false, last.ticket)
  }

  function parse(raw) {
    try { return JSON.parse(String(raw || "")) } catch (error) { return { state: "error", message: "board-fetch returned no readable output." } }
  }

  // The saved copy, only while nothing is on screen: no GitLab call.
  function readCache() {
    if (project === "" || boardState !== "loading" || cacheProcess.running) return
    cacheProcess.key = project + "#" + boardId
    cacheProcess.session = session
    cacheProcess.command = helperCommand(["cached", "--project", project, "--board", boardId])
    cacheProcess.running = true
  }
  function applyCache(raw, key) {
    if (boardState === "loading" && key === project + "#" + boardId && parse(raw).cached === true) apply(raw, true)
  }

  function apply(raw, fromCache, ticket) {
    var data = parse(raw)
    if (data.project && data.project !== project) return  // answer for a project we already left
    if (held || (!fromCache && ticket < moveFloor)) { refreshQueued = true; return }  // mid-drag or mid-move, or older than the latest move
    // A failed refresh keeps the board on screen (sign-in problems still show
    // the sign-in panel); only with nothing loaded does the error take its place.
    if (data.state === "error" && boardState === "ready" && columns.length > 0) { refreshError = String(data.message || "Could not load issues."); return }
    refreshError = ""
    cached = !!fromCache
    boardState = String(data.state || "error")
    message = String(data.message || "")
    updatedAt = String(data.updatedAt || "")
    // Columns and cards on screen are keyed (BoardView.qml), so a new array
    // only redraws the cards whose data changed.
    var nextColumns = Array.isArray(data.columns) ? data.columns : []
    if (JSON.stringify(nextColumns) !== JSON.stringify(columns)) columns = nextColumns
    var nextColors = data.labelColors || {}
    if (JSON.stringify(nextColors) !== JSON.stringify(labelColors)) labelColors = nextColors
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
    if (boardState === "ready" && !cached) feed.requestAccess(project)  // once per project (the service keeps it)
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
    if (moveStillRunning || (!bulkBar.running && bulkBar.busy)) return noteStillFinishing()
    if (move || pendingMove || bulkBar.busy || !row || !canDrop(from) || !canDrop(to) || Logic.columnKey(from) === Logic.columnKey(to)) return false
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

  // Picked cards for bulk actions: Logic.pickKey per card, at most
  // Logic.bulkCap; cards that leave the board drop out. Fixed while armed or
  // running, and until the results are closed.
  property var picked: []
  // Picking stays open when only a card the watchdog gave up on still runs;
  // arming then says it is still finishing.
  onColumnsChanged: if (!bulkBar.running && !bulkBar.armed) picked = Logic.livePicks(columns, picked)
  function togglePick(column, iid) {
    if (bulkBar.running || bulkBar.armed || bulkBar.mode === "results" || !column || !writable) return
    var t = Logic.togglePick(picked, Logic.pickKey(column, iid))
    picked = t.picked
    bulkBar.pickNote(t.full)
  }
  function pickAtCursor() { var row = cursorIssue(); if (row) togglePick(shownColumns[cursor.col], row.iid) }
  function dropPicks() { if (bulkBar.busy) bulkBar.stopping = true; else bulkBar.reset(); picked = [] }
  // A run ended: load the board as GitLab now has it, after every write.
  function bulkFinished() { refreshQueued = true; moveFloor = feed.tickets + 1 }
  function focusBoard() { Qt.callLater(function() { keyCatcher.forceActiveFocus() }) }
  // Shift+H/L: the selected card to the nearest column it can go to on that side.
  function moveCursorCard(dx) {
    var row = cursorIssue()
    if (!row) return
    var from = shownColumns[cursor.col]
    for (var i = cursor.col + dx; i >= 0 && i < shownColumns.length; i += dx)
      if (canDrop(shownColumns[i])) { requestMove(row, from, shownColumns[i]); return }
  }
  function moveIssue(row, from, to) {
    // moveProcess can outlive move: the watchdog gave up on it, board-fetch's deadline ends it.
    if (moveStillRunning) return noteStillFinishing()
    if (move || moveProcess.running || !row || !canDrop(from) || !canDrop(to) || Logic.columnKey(from) === Logic.columnKey(to)) return false
    move = { iid: row.iid, snapshot: columns, key: stateKey }
    moveError = ""
    columns = Logic.movedColumns(columns, row, from, to)
    moveProcess.command = helperCommand(["move", "--project", project, "--board", resolvedBoardId,
      "--iid", String(row.iid), "--from", Logic.listSpec(from), "--to", Logic.listSpec(to)])
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
      feed.noteRefused(project, data.message)  // a 403: view-only here
      moveErrorTimer.restart()
    }
    // Success, or a card that was out of date ("stale": board-fetch wrote
    // nothing): load the board as GitLab now has it. Other failures: only if a
    // refresh was due. It runs once the move is cleared (onBusyChanged).
    // Answers from fetches started before now may predate the write: the next
    // one must start after it (moveFloor), on every screen's behalf.
    if (data.state === "ready" || data.state === "stale") { refreshQueued = true; moveFloor = feed.tickets + 1 }
    if (data.state === "ready") feed.noteOwnMove(fetchKey, move.iid)  // no alert for his own move
    move = null
  }

  function runAux(kind, args) {
    if (auxProcess.running) { pendingAux = { kind: kind, args: args }; return }
    auxKind = kind
    auxProcess.session = session
    auxError = ""
    auxLoading = true
    auxProcess.command = helperCommand([kind].concat(args))
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
    if (lists[name] && view !== name) lists[name].open()
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
    headerMenu = ""
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
    dropPicks()
    boardState = "loading"
    if (defaultProject === "") persist({ board: { project: path, id: id, name: name } })  // first board: the default
    back()
    refresh()
  }
  // Star in the picker: favorite toggle (jump list). The default is set from
  // the header Default menu (setDefaultCurrent), not from this star.
  function isDefaultBoard(b) {
    var first = pickerBoards.length > 0 ? String(pickerBoards[0].id || "") : ""
    return pickerProject === defaultProject && String(b.id || "") === (defaultBoardId || first)
  }
  function isFavoriteBoard(b) {
    return Logic.isFavorite(hostFavorites, pickerProject, String(b.id || ""))
  }
  function favoriteEntry(projectPath, b) {
    var id = String(b.id || "")
    return { project: projectPath, id: id, name: id !== "" ? String(b.name || "") : Logic.boardLabel(b.name, "") }
  }
  function persistFavorites(list) {
    if (onGitlabCom) persist({ favorites: list })
    else {
      var next = {}, old = Object(saved("serverFavorites", ({})))
      for (var hostKey in old) next[hostKey] = old[hostKey]
      next[gitlabHost] = list
      persist({ serverFavorites: next })
    }
  }
  function toggleFavorite(b) {
    persistFavorites(Logic.toggledFavorite(hostFavorites, favoriteEntry(pickerProject, b)))
  }
  // Make the board on screen the default (header menu). Freezes browsing
  // bindings the same way the old picker setDefault did.
  function setDefaultCurrent() {
    project = project; boardId = boardId; boardName = boardName
    persist({ board: { project: project, id: boardId || resolvedBoardId, name: boardName } })
    headerMenu = ""
  }
  function openDefault() { headerMenu = ""; switchTo(defaultProject, defaultBoardId, defaultBoardName) }
  // Title click: jump list when there is a default or a favorite; else the picker.
  function openJumpMenu() {
    if (jumpBoards.length === 0) openPicker()
    else headerMenu = headerMenu === "jump" ? "" : "jump"
  }
  function openDefaultMenu() {
    if (onDefault || project === "") return
    headerMenu = headerMenu === "default" ? "" : "default"
  }
  function jumpTo(entry) {
    headerMenu = ""
    switchTo(entry.project, String(entry.id || ""), String(entry.name || ""))
  }
  function openBrowse() { headerMenu = ""; openPicker() }

  // https only (Logic.httpsUrl), so no file:, javascript: or --flag value reaches the browser.
  // A browser tab or an app window, as Settings says (linkMode).
  function openUrl(url) {
    var link = Logic.httpsUrl(url)
    if (link === "") return
    Quickshell.execDetached([linkMode === "app" ? "omarchy-launch-webapp" : "omarchy-launch-browser", link])
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
    logoutProcess.command = helperCommand(["logout"])
    logoutProcess.running = true
  }
  function signedOut(raw) {
    var data = parse(raw)
    signingOut = false
    if (data.state !== "logged-out") { accountError = String(data.message || "Could not sign out."); return }
    session++
    feed.forget()
    columns = []; projects = []; pickerBoards = []; cached = false; account = ""; refreshError = ""; pendingMove = null; dropPicks()
    message = String(data.message || ""); boardState = "logged-out"
    showView("board")
  }

  // First run. glab asks for the token in its own terminal: this plugin never
  // sees it. Same launcher as Omarchy's update widget (SystemUpdate.qml).
  readonly property string installCommand: "sudo pacman -S glab"
  readonly property string icon: "\uf296"  // Font Awesome gitlab (Nerd Font): the bar icon and the setup panel
  function signIn() {
    Quickshell.execDetached(["omarchy-launch-floating-terminal-with-presentation", loginCommand])
    close()
  }
  function copyInstall() { Quickshell.execDetached(["wl-copy", installCommand]) }
  // j/k or ↓/↑ in Settings, the shortcuts and an issue (BoardKeys.qml): about
  // three lines down or up, eased, never past either end. The view's
  // ScrollHint knows its Flickable. Not while typing: fields get every key.
  function scrollView(dy) {
    var v = view === "settings" ? settingsView : view === "keys" ? keysView : view === "issue" ? issueView : null
    var hint = null
    if (v) for (var i = 0; i < v.children.length; i++) if (v.children[i].objectName === "scrollHint") hint = v.children[i]
    if (!hint) return false
    var f = hint.flick
    var from = scrollAnim.running && scrollAnim.target === f ? scrollAnim.to : f.contentY
    var to = Math.max(0, Math.min(f.contentHeight - f.height, from + dy * Style.space(56)))
    scrollAnim.stop(); scrollAnim.target = f; scrollAnim.to = to; scrollAnim.start()
    return true
  }
  NumberAnimation { id: scrollAnim; property: "contentY"; duration: 120; easing.type: Easing.OutCubic }
  function copyLogin() { Quickshell.execDetached(["wl-copy", loginCommand]) }

  // y, or a right-click on a card or a merge request (BoardKeys, BoardView,
  // MrsView): its link to the clipboard with wl-copy, as the setup panel does.
  // https only (Logic.httpsUrl), the same as openUrl. The status then reads
  // "Copied #N" (an issue) or "Copied !N" (a merge request) for a moment.
  property string copiedNote: ""
  Timer { id: copiedTimer; interval: 1500; onTriggered: root.copiedNote = "" }
  function copyLink(row, sign) {
    var link = row ? Logic.httpsUrl(row.url) : ""
    if (link === "") return false
    Quickshell.execDetached(["wl-copy", link])
    copiedNote = "Copied " + sign + row.iid
    copiedTimer.restart()
    return true
  }

  // The tip on "Updated": the setting, then the pace and why; with a card or
  // bot alert on it also refreshes while closed (watchCfg, BoardService.background).
  function cadenceText() { return Logic.cadenceText(refreshIntervalSec, cadence, watchCfg !== null && (alerts.review || alerts.idle)) }
  function statusText() {
    if (moveError !== "") return moveError
    if (move) return "Moving #" + move.iid + "…"
    // While the timer's refresh runs the status keeps its time (the dot before
    // it says a refresh is on), and a last failure gives way to it.
    if (boardState === "ready" && refreshError !== "" && !refreshing)
      return "Couldn't refresh · showing " + (updatedAt !== "" ? new Date(updatedAt).toLocaleTimeString(Qt.locale(), "HH:mm") : "the last board")
    if (boardState === "ready" && cached) return Logic.savedNote(updatedAt)
    if (boardState === "ready") {
      // A refresh you asked for says so; the timer's keeps the time.
      // On Merge requests or To-do, when the lists were read (their entry), not the board.
      var listed = shownList ? shownList.entry : null
      var at = !shownList ? updatedAt : listed && listed.startedAt > 0 ? new Date(listed.startedAt).toISOString() : ""
      var time = copiedNote !== "" ? copiedNote : updating ? "Updating…" : at !== "" ? "Updated " + new Date(at).toLocaleTimeString(Qt.locale(), "HH:mm") : ""
      if (!writable) time = "View-only  " + time
      return message !== "" ? message + "  " + time : time
    }
    if (view === "board" && (setup !== "" || failed || boardState === "loading")) return ""  // the board body says it
    if (project === "") return ""
    if (boardState === "loading") return "Loading GitLab issues…"
    if (boardState === "logged-out") return message || "Not signed in. Run: " + loginCommand
    return message || "Could not load issues."
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component.onCompleted: { feed.setHost(gitlabHost); Qt.callLater(readCache); feed.watch(watchOwner, watchCfg) }
  // Another server: nothing from the last one stays (its board, saved copy,
  // projects, account, merge requests: feed.setHost forgets them), and its own
  // default board loads, or the picker. Answers on their way are dropped (session).
  property string shownHost: "gitlab.com"  // the server this copy shows
  onGitlabHostChanged: switchServer()
  function switchServer() {
    if (gitlabHost === shownHost) return
    shownHost = gitlabHost
    feed.setHost(gitlabHost)
    session++
    // Back to following the saved default, as on a shell start.
    project = Qt.binding(function() { return root.defaultProject })
    boardId = Qt.binding(function() { return root.defaultBoardId })
    boardName = Qt.binding(function() { return root.defaultBoardName })
    columns = []; projects = []; pickerBoards = []; cached = false; account = ""; accountError = ""
    resolvedBoardId = boardId; firstBoardId = ""; refreshError = ""; moveError = ""; message = ""; updatedAt = ""
    pendingMove = null; dropPicks()
    boardState = "loading"
    if (view !== "board" && view !== "settings") showView("board")
    // Once the settings-bound properties (the default board) have caught up.
    Qt.callLater(function() {
      if (view === "settings") checkAccount()
      if (opened) refresh()
      else readCache()
    })
  }
  onOpenedChanged: if (opened) { feed.seenAlerts(); view = "board"; cursor = null; refresh(true) } else { boardView.endDrag(); pendingMove = null; if (!bulkBar.busy && bulkBar.mode !== "results") dropPicks(); saveFolds() }

  // Only while the popup is open; opening it refreshes if due (onOpenedChanged).
  // A copy on another screen that fetched meanwhile makes the tick a no-op.
  // A new cadence restarts it (QML Timer), so the next tick counts from then.
  Timer {
    id: refreshTimer
    interval: root.cadence.sec * 1000
    repeat: true; running: root.opened && root.setup === ""
    onTriggered: root.refresh(true)
  }

  BoardPersist { id: boardPersist; host: root }
  function migrateSettings() { boardPersist.migrateSettings() }
  function persist(patch) { foldsUnsaved = false; foldSave.stop(); boardPersist.persist(patch) }
  function saveBots(next) { boardPersist.saveBots(next) }
  function helperPath() { return boardPersist.helperPath() }
  function helperCommand(args) { return boardPersist.helperCommand(args) }

  BoardService { id: localFeed }
  // Every answer for the board on screen, whichever screen asked for it.
  Connections {
    target: root.feed
    function onAnswered(key, raw, ticket) { if (key === root.fetchKey) root.apply(raw, false, ticket) }
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
  // No answer in 50 s, past board-fetch's 40 s deadline (glab hung or never
  // started): put the card back and reload, since the move may or may not have
  // reached GitLab.
  Timer {
    id: moveWatchdog; interval: 50000
    onTriggered: { root.refreshQueued = true; root.moveFloor = root.feed.tickets + 1; root.moveDone(JSON.stringify({ state: "error", message: "No answer from glab; reloading the board." })) }
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
    tooltipText: "GitLabby" + (root.project !== "" ? " · " + root.project : "") + (root.iconLit ? " · an alert came" : "")
    onPressed: function(buttonCode) {
      if (buttonCode === Qt.RightButton || buttonCode === Qt.MiddleButton) root.refresh()
      else root.toggle()
    }
  }

  // A small accent dot at the icon's top right while an alert waits unseen
  // (BoardService.unseenAlerts), on every screen; gone when a popup opens.
  Rectangle {
    id: alertDot
    objectName: "alertDot"
    visible: root.iconLit
    width: Style.space(5); height: width; radius: width / 2
    x: Math.round(button.width / 2 + Style.space(4)); y: Math.round(button.height / 2 - Style.space(9))
    color: root.accent
  }
  Connections {
    target: root.feed
    function onUnseenAlertsChanged() { if (root.opened && root.feed.unseenAlerts > 0) root.feed.seenAlerts() }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button; owner: root; bar: root.bar
    open: root.opened; focusTarget: keyCatcher
    // One frame for every view: the board's width (760 at least) and a fixed
    // 640 height. Views fit or scroll inside it, so switching views never
    // resizes the popup; only folding columns changes the width.
    // fittedContentWidth caps at availableCardWidth (screen minus margins) and
    // fittedContentHeight at the free screen height (availableCardHeight):
    // anything bigger scrolls inside.
    contentWidth: panel.fittedContentWidth(Math.max(Style.space(760),
      (root.setup !== "" || root.failed || root.boardState === "loading" ? skeleton.implicitWidth : root.shownBoardWidth) + panel.padding * 2 + Style.space(4)))
    contentHeight: panel.fittedContentHeight(Style.space(640), Style.space(640))

    BoardKeys {  // the key routing (BoardKeys.qml)
      id: keyCatcher
      host: root
      views: ({ issue: issueView, picker: picker, settings: settingsView, bulk: bulkBar, mrs: mrsView, todos: todoView, setup: setupView })
      anchors.fill: parent
      blocked: issueView.typing || picker.typing || settingsView.typing || bulkBar.typing  // text fields get every key (Omarchy PanelKeyCatcher.qml:26-29)
      implicitHeight: header.implicitHeight + root.gap + (botsRow.visible ? botsRow.height + root.gap : 0) + (accessHint.visible ? accessHint.height + root.gap : 0) + (moveConfirm.visible ? moveConfirm.height + root.gap : 0) + (bulkBar.visible ? bulkBar.height + root.gap : 0) + (root.view === "board" ? (root.setup !== "" || root.failed ? Math.max(setupView.implicitHeight, skeleton.implicitHeight) : root.boardState === "loading" ? skeleton.implicitHeight : boardView.implicitHeight)
        : root.view === "issue" ? issueView.implicitHeight : root.view === "picker" ? picker.implicitHeight
        : root.view === "keys" ? keysView.implicitHeight : root.shownList ? root.shownList.implicitHeight : settingsView.implicitHeight)
      // One round mask for every avatar (Avatar.qml's maskSource): one
      // offscreen layer for the popup instead of one per avatar.
      Item {
        id: sharedAvatarMask
        objectName: "sharedAvatarMask"
        width: 64; height: 64
        visible: false
        layer.enabled: true
        Rectangle { anchors.fill: parent; radius: width / 2; color: "black" }
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

      BoardHeader {
        id: header
        host: root
        mrsScope: mrsView.scope
        todoScope: todoView.scope
        width: parent.width
      }

      BotsRow {
        id: botsRow
        host: root
        states: root.botStates
        visible: root.view === "board" && root.setup === "" && root.boardState === "ready" && root.botStates.length > 0
        anchors { top: header.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      AccessHint {
        id: accessHint
        host: root
        anchors { top: botsRow.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      MoveConfirm {
        id: moveConfirm
        host: root
        pending: root.pendingMove
        visible: root.view === "board" && root.pendingMove !== null
        anchors { top: accessHint.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      BulkBar {
        id: bulkBar
        host: root
        anchors { top: moveConfirm.bottom; topMargin: visible ? root.gap : 0; left: parent.left; right: parent.right }
        height: visible ? implicitHeight : 0
      }

      Item {
        anchors { top: bulkBar.bottom; topMargin: root.gap; left: parent.left; right: parent.right; bottom: parent.bottom }
        SetupView { id: setupView; host: root; anchors.fill: parent; visible: root.view === "board" && (root.setup !== "" || root.failed) }
        Skeleton { id: skeleton; host: root; anchors.fill: parent; visible: root.view === "board" && root.setup === "" && root.boardState === "loading" }
        BoardView { id: boardView; host: root; anchors.fill: parent; visible: root.view === "board" && root.setup === "" && root.boardState === "ready" }
        IssueView { id: issueView; host: root; anchors.fill: parent; visible: root.view === "issue" }
        Picker { id: picker; host: root; anchors.fill: parent; visible: root.view === "picker" }
        SettingsView { id: settingsView; host: root; anchors.fill: parent; visible: root.view === "settings" }
        KeysView { id: keysView; host: root; anchors.fill: parent; visible: root.view === "keys" }
        MrsView { id: mrsView; host: root; anchors.fill: parent; visible: root.view === "mrs" }
        TodoView { id: todoView; host: root; anchors.fill: parent; visible: root.view === "todos" }
      }
    }
  }
}
