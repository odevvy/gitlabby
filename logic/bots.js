// Who's busy: the bots setting, per-column bot states, editing the setting. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { Core = m.Core; }
function lowerList(value) { return Core.lowerList(value) }
function plain(v) { return Core.plain(v) }
function copied(raw) { return Core.copied(raw) }

// Busy markers for a team of bots, read from the board on screen (no extra
// calls). config is settings.bots[project]:
//   { busyLists: ["approved", "in progress", "review"], workingLists: ["in progress"],
//     bots: [{ name, label }, { name, label: "" }, { name, list }] }
// A label bot owns open issues with its label in a busy list; label "" owns
// those with none of the bots' labels; a list bot owns every issue in its list.
// An issue with two owner labels counts for both. Closed and Open never count.
// working: an owned issue in a working list (default "in progress"), or any
// for a list bot; waiting: only other busy lists; idle: none. Names match in
// any case. Returns null (no row) unless the config has at least one bot.
// Each state also names the column its dot takes its color from: the furthest
// along (rightmost on the board) of the issues that set the state, so the
// working ones when any are working (a filled dot never wears a column the bot
// only waits in). oneList is that column's name when every issue is in it.
// The board's bots for project, read with the same rules as Settings > Bots
// (botsEntry, botUsable), so the row and the editor never disagree.
function botsConfig(all, project) {
  var c = botsEntry(all, project).entry
  if (!c) return null
  var bots = c.bots.filter(botUsable).map(function(b) {
    return typeof b.list === "string" && b.list.trim() !== "" ? { name: b.name.trim(), list: b.list.trim().toLowerCase() } : { name: b.name.trim(), label: b.label.trim().toLowerCase() }
  })
  if (bots.length === 0) return null
  return { bots: bots, busyLists: lowerList(c.busyLists || []), workingLists: lowerList(c.workingLists || ["in progress"]) }
}
function botStates(config, columns) {
  if (!config) return []
  var owners = config.bots.filter(function(b) { return b.label }).map(function(b) { return b.label })
  return config.bots.map(function(bot) {
    var found = {}, order = []
    ;(columns || []).forEach(function(c, at) {
      if (c.kind !== "label") return
      var list = String(c.name).toLowerCase()
      if (bot.list !== undefined ? list !== bot.list : config.busyLists.indexOf(list) === -1) return
      ;(c.issues || []).forEach(function(row) {
        var labels = lowerList(row.labels || [])
        var mine = bot.list !== undefined || (bot.label ? labels.indexOf(bot.label) !== -1
          : !labels.some(function(l) { return owners.indexOf(l) !== -1 }))
        if (!mine) return
        var working = bot.list !== undefined || config.workingLists.indexOf(list) !== -1
        if (!found[row.iid]) { found[row.iid] = { iid: row.iid, list: c.name, color: c.color || "", at: at, working: working, row: row }; order.push(row.iid) }
        else if (working && !found[row.iid].working) Object.assign(found[row.iid], { list: c.name, color: c.color || "", at: at, working: true })
      })
    })
    var issues = order.map(function(iid) { return found[iid] })
    var working = issues.filter(function(i) { return i.working })
    var lead = (working.length > 0 ? working : issues).reduce(function(best, i) { return !best || i.at > best.at ? i : best }, null)
    var oneList = issues.length > 0 && issues.every(function(i) { return i.list === issues[0].list }) ? issues[0].list : ""
    return { name: bot.name, byList: bot.list !== undefined, issues: issues,
             state: working.length > 0 ? "working" : issues.length > 0 ? "waiting" : "idle",
             column: lead ? lead.list : "", color: lead ? lead.color : "", oneList: oneList }
  })
}
// "in research", but "in progress" as it is (no "in in progress").
function inColumn(name) { var n = String(name || ""); return /^in\s/i.test(n) ? n : "in " + n }
// { problem, entry }: problem "setting" (bots isn't an object, e.g. set
// without --json) or "entry" (this project's entry or its bots list is
// malformed); entry is the project's saved entry, or null.
function botsEntry(raw, project) {
  if (raw === undefined || raw === null) return { problem: "", entry: null }
  if (!plain(raw)) return { problem: "setting", entry: null }
  var e = raw[project]
  if (e === undefined) return { problem: "", entry: null }
  if (!plain(e) || !Array.isArray(e.bots)) return { problem: "entry", entry: null }
  return { problem: "", entry: e }
}
// A bot botsConfig would show: a name, and a label (may be "") or a list.
function botUsable(b) {
  return plain(b) && typeof b.name === "string" && b.name.trim() !== ""
    && (typeof b.label === "string" || (typeof b.list === "string" && b.list.trim() !== ""))
}
function botNameTaken(entry, name) {
  var key = String(name).trim().toLowerCase()
  return !!entry && (entry.bots || []).some(function(b) { return plain(b) && String(b.name || "").trim().toLowerCase() === key })
}
// Adds bot ({ name, label } or { name, list }). A new (or replaced, malformed)
// entry starts with every label column busy.
function withBot(raw, project, bot, labelColumns) {
  var next = copied(raw), found = botsEntry(next, project)
  if (!found.entry) next[project] = { busyLists: (labelColumns || []).slice(), bots: [] }
  next[project].bots.push(bot)
  return next
}
// Removes the bot at index; the last one takes the project's entry with it.
function withoutBot(raw, project, index) {
  var next = copied(raw), found = botsEntry(next, project)
  if (!found.entry) return next
  found.entry.bots.splice(index, 1)
  if (found.entry.bots.length === 0) delete next[project]
  return next
}
// Turns a busy column on or off (any case); other names stay as saved.
function withBusy(raw, project, column, on) {
  var next = copied(raw), found = botsEntry(next, project)
  if (!found.entry) return next
  var key = String(column).toLowerCase()
  var lists = (Array.isArray(found.entry.busyLists) ? found.entry.busyLists : []).filter(function(n) { return String(n).toLowerCase() !== key })
  if (on) lists.push(column)
  found.entry.busyLists = lists
  return next
}

if (typeof module !== "undefined") module.exports = { botsConfig: botsConfig, botStates: botStates, inColumn: inColumn, botsEntry: botsEntry, botUsable: botUsable, botNameTaken: botNameTaken, withBot: withBot, withoutBot: withoutBot, withBusy: withBusy }
