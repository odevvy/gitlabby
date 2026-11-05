import QtQuick
import "Logic.js" as Logic

// Settings persistence for Board.qml (not a view). Board keeps one-line
// wrappers so host.persist / host.saveBots / host.migrateSettings stay the same.
QtObject {
  id: data
  required property var host

  // One-time update to settings revision 2 (v0.1.3): Open joins the collapsed
  // defaults, and every saved board that had no Open entry gets it.
  function migrateSettings() {
    var h = data.host
    if ((parseInt(String(h.saved("settingsRevision", 1)), 10) || 1) >= h.settingsRevision) return
    if (h.saved("defaultCollapsed", null) === null && h.saved("boardStates", null) === null) return
    var collapsed = Logic.lowerList(h.saved("defaultCollapsed", ["closed", "research"]))
    if (collapsed.indexOf("open") === -1) h.persist({ defaultCollapsed: ["open"].concat(collapsed) })
    var states = h.saved("boardStates", ({})) || ({})
    var next = {}, changed = false
    for (var key in states) {
      var e = Object(states[key]), c = Logic.lowerList(e.collapsed)
      if (c.indexOf("open") === -1) { c = ["open"].concat(c); changed = true }
      next[key] = { collapsed: c, hidden: Logic.lowerList(e.hidden) }
    }
    if (changed) { h.boardStates = next; h.persist({}) }
  }

  // Same write path as built-in widgets: merge into the inline entry and hand
  // it to the shell facade. Without the facade the state stays in memory.
  // patch: settings keys to set (bots, alerts, openLinks, …); the rest are kept
  // as saved. patch.board ({ project, id, name }) replaces the saved default
  // board (this server's: on another one, settings.serverDefaults[host];
  // gitlab.com's stays).
  function persist(patch) {
    var h = data.host
    var p = patch || {}
    if (!h.bar || !h.bar.shell || typeof h.bar.shell.updateEntryInline !== "function") return
    var d = p.board || { project: h.defaultProject, id: h.defaultBoardId, name: h.defaultBoardName }
    var entry = { id: h.moduleName }
    var dropped = ["id", "collapsedColumns", "hiddenColumns", "project", "boardId", "boardName"]
    for (var key in h.savedSettings) if (dropped.indexOf(key) === -1) entry[key] = h.savedSettings[key]
    if (h.onGitlabCom) {
      entry.defaultProject = d.project
      entry.defaultBoardId = d.id
      entry.defaultBoardName = d.name
    } else if (p.board) {
      var defaults = {}, old = Object(h.saved("serverDefaults", ({})))
      for (var hostKey in old) defaults[hostKey] = old[hostKey]
      defaults[h.gitlabHost] = { project: d.project, id: d.id, name: d.name }
      entry.serverDefaults = defaults
    }
    entry.refreshIntervalSec = h.refreshIntervalSec
    entry.defaultCollapsed = h.defaultCollapsed
    entry.boardStates = h.boardStates
    entry.settingsRevision = h.settingsRevision
    for (var k in p) if (k !== "board") entry[k] = p[k]
    h.bar.shell.updateEntryInline(h.moduleName, entry)
  }

  function saveBots(next) { data.persist({ bots: next }) }

  function helperPath() {
    return decodeURIComponent(Qt.resolvedUrl("board-fetch").toString().replace(/^file:\/\//, ""))
  }
  function helperCommand(args) {
    return [data.helperPath()].concat(args, ["--hostname", data.host.gitlabHost])
  }
}
