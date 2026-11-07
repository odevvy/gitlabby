import QtQuick
import qs.Ui

// The board popup's keys (Omarchy's PanelKeyCatcher): which view or bar each
// key goes to. Board.qml places it as keyCatcher, with the views as its
// children and passed in views, so their ids stay Board.qml's.
PanelKeyCatcher {
  property Item host
  // { issue, picker, settings, bulk, mrs, todos, setup }: the views keys go to.
  property var views: ({})
  readonly property Item issueView: views.issue || null
  readonly property Item picker: views.picker || null
  readonly property Item settingsView: views.settings || null
  readonly property Item bulkBar: views.bulk || null
  readonly property Item mrsView: views.mrs || null
  readonly property Item todoView: views.todos || null
  readonly property Item setupView: views.setup || null

  // Ctrl+Tab / Ctrl+Shift+Tab: next or previous bar panel. A shortcut runs
  // before the key reaches the catcher, which would read it as plain Tab.
  Shortcut { sequences: ["Ctrl+Tab"]; onActivated: host.switchPanel(1) }
  Shortcut { sequences: ["Ctrl+Shift+Tab", "Ctrl+Backtab", "Ctrl+Shift+Backtab"]; onActivated: host.switchPanel(-1) }

  onCloseRequested: {
    if (host.headerMenu !== "") host.headerMenu = ""
    else if (host.kbFocus) host.kbFocus = null
    else if (host.pendingMove) host.cancelMove()
    else if (host.view === "board" && bulkBar.stepBack()) {}
    else if (host.view === "issue" && issueView.confirming) issueView.confirming = false
    else if (host.view === "issue" && issueView.editing) issueView.doneEditing()  // labels still loading: the filter is off
    else if (host.view === "settings" && settingsView.adding) settingsView.cancelAdd()
    else if (host.view !== "board") host.back()
    else host.close()
  }
  onDeleteRequested: {  // x
    if (host.view === "issue" && !issueView.editing) issueView.toggleState()  // not while labels load
    else if (host.view === "board" && !host.pendingMove && bulkBar.armed && bulkBar.armKey === "x") bulkBar.confirm()
    else if (host.view === "board" && !host.pendingMove && bulkBar.mode === "" && host.picked.length > 0) bulkBar.armClose("x")
  }
  onTabRequested: function(direction) { host.focusNext(direction) }  // the popup's controls
  onMoveRequested: function(dx, dy) {
    if (host.headerMenu !== "") { if (dy !== 0) host.moveMenu(dy); return }
    // A focused segmented control takes Left / Right (Settings, v0.1.104).
    if (host.kbFocus && dx !== 0 && typeof host.kbFocus.kbMove === "function") { host.kbFocus.kbMove(dx); return }
    host.kbFocus = null  // one focus at a time: the board cursor or a control
    if (host.view === "board") host.moveCursor(dx, dy)
    else if (host.view === "picker" && dy !== 0) picker.moveCursor(dy)
    else if (host.view === "mrs" && dy !== 0) mrsView.moveCursor(dy)
    else if (host.view === "todos" && dy !== 0) todoView.moveCursor(dy)
    else if (dy !== 0) host.scrollView(dy)  // j/k, ↓/↑: Settings, the shortcuts, an issue
  }
  onActivateRequested: {
    if (host.headerMenu !== "") { host.activateMenu(); return }
    if (host.kbFocus) { host.activateFocus(); return }
    if (host.pendingMove) host.confirmMove()
    else if (host.view === "board" && bulkBar.armed) bulkBar.confirm()
    else if (host.view === "board" && bulkBar.mode === "results") bulkBar.done()
    else if (host.view === "issue" && issueView.confirming) issueView.setState("close")
    else if (host.view === "board" && host.cursorIssue()) host.openIssue(host.cursorIssue())
    else if (host.view === "picker") picker.activate()
    else if (host.view === "mrs") mrsView.activate()
    else if (host.view === "todos") todoView.activate()
    else if (host.view === "board" && (host.setup !== "" || host.failed)) setupView.primary()
  }
  onTextKey: function(text) {
    if (host.headerMenu !== "") return  // an open header menu keeps letters from the board
    if (host.pendingMove) return  // Enter or Escape first
    if (host.view === "issue" && issueView.editing) return  // typed for the filter while labels load
    if (host.view === "board" && bulkBar.visible && bulkBar.mode !== "") {
      if (bulkBar.armed && text === bulkBar.armKey) bulkBar.confirm()  // the arming key again
      return  // choosing, armed, running or results: Enter, Esc or the bar's buttons
    }
    if (host.view === "board" && host.picked.length > 0 && (text === "H" || text === "L")) { bulkBar.armSide(text === "H" ? -1 : 1, text); return }
    if (host.view === "board" && host.picked.length > 0 && text.toLowerCase() === "e") { bulkBar.chooseLabel("add"); return }
    if (text.toLowerCase() === "v" && host.view === "board") { host.pickAtCursor(); return }
    if ((text === "H" || text === "L") && host.view === "board") { host.moveCursorCard(text === "H" ? -1 : 1); return }
    var key = text.toLowerCase()
    if (key === "r" && host.view === "board") host.refresh()
    else if (key === "r" && host.view === "mrs") mrsView.refresh()
    else if (key === "o" && host.view === "mrs") mrsView.activate()
    else if (key === "r" && host.view === "todos") todoView.refresh()
    else if (key === "o" && host.view === "todos") todoView.activate()
    else if (key === "y" && host.view === "todos") todoView.copyCurrent()
    else if (key === "o") {
      var row = host.view === "issue" ? issueView.issue : host.view === "board" ? host.cursorIssue() : null
      if (row) host.openUrl(row.url)
    }
    else if (key === "y" && host.view === "mrs") host.copyLink(mrsView.rows[mrsView.cursor], "!")
    else if (key === "y") host.copyLink(host.view === "issue" ? issueView.issue : host.view === "board" ? host.cursorIssue() : null, "#")
    else if (key === "c" && host.view === "issue") issueView.focusBox()
    else if (key === "e" && host.view === "issue") issueView.editLabels()
    else if (key === "b" && host.view === "board") host.toggleBots()
    else if (key === "p") host.openPicker()
    else if (key === "s") host.toggleView("settings")
    else if (key === "?") host.toggleView("keys")
    else if (key === "m") host.toggleView("mrs")
    else if (key === "t") host.toggleView("todos")
  }
}
