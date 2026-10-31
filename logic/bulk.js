// Bulk actions: picks, the plan, the bar text and each card's outcome. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From board.js, core.js: required under node; in QML, Logic.js hands them over through use().
var BoardLogic = typeof module !== "undefined" ? require("./board.js") : null
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { BoardLogic = m.BoardLogic; Core = m.Core; }
function columnKey(column) { return BoardLogic.columnKey(column) }
function listSpec(column) { return BoardLogic.listSpec(column) }
function has(list, name) { return Core.has(list, name) }

// Bulk actions (BulkBar.qml): several cards, one action, armed then confirmed,
// written one card at a time with the same board-fetch writes as one card.
// A picked card is "<columnKey>|<iid>": a card shown in two lists is picked
// in the one it was picked in, and that list is the move's --from.
var bulkCap = 20
function pickKey(column, iid) { return columnKey(column) + "|" + iid }
// { picked, full }: full when adding would pass the cap (nothing added).
function togglePick(picked, key) {
  var list = picked || []
  if (list.indexOf(key) !== -1) return { picked: list.filter(function(k) { return k !== key }), full: false }
  if (list.length >= bulkCap) return { picked: list, full: true }
  return { picked: list.concat([key]), full: false }
}
// The picked cards still on the board, as { key, row, column }, in pick order.
function pickedCards(columns, picked) {
  var at = {}
  ;(columns || []).forEach(function(c) { (c.issues || []).forEach(function(i) { at[pickKey(c, i.iid)] = { row: i, column: c } }) })
  return (picked || []).filter(function(k) { return !!at[k] }).map(function(k) { return { key: k, row: at[k].row, column: at[k].column } })
}
function livePicks(columns, picked) { return pickedCards(columns, picked).map(function(p) { return p.key }) }
// A column a card can leave or enter by a move (Board.canDrop without the board checks).
function movable(column) { return !!column && (column.kind === "open" || column.kind === "closed" || (column.kind === "label" && !!column.listId)) }
// x on a selection: close, unless every picked card is already closed.
function closeOrReopen(cards) { return (cards || []).some(function(p) { return p.column.kind !== "closed" }) ? "close" : "reopen" }
// One step per picked card: board-fetch arguments, or why it is skipped.
// action: { kind: "move", to } | { kind: "add" | "remove", label } | { kind: "close" | "reopen" }
function bulkPlan(cards, action, project, boardId) {
  return (cards || []).map(function(p) {
    var row = p.row, from = p.column, skip = "", args = null, labels = row.labels || []
    var base = ["--project", project, "--iid", String(row.iid)]
    if (action.kind === "move") {
      if (!movable(from)) skip = "Can't move cards out of " + from.name
      else if (columnKey(from) === columnKey(action.to)) skip = "Already in " + action.to.name
      else args = ["move", "--project", project, "--board", String(boardId), "--iid", String(row.iid), "--from", listSpec(from), "--to", listSpec(action.to)]
    } else if (action.kind === "add") {
      if (labels.indexOf(action.label) !== -1) skip = "Already has " + action.label
      else args = ["relabel"].concat(base, ["--add", action.label])
    } else if (action.kind === "remove") {
      if (labels.indexOf(action.label) === -1) skip = "Doesn't have " + action.label
      else args = ["relabel"].concat(base, ["--remove", action.label])
    } else {
      var closed = from.kind === "closed"
      if (action.kind === "close" && closed) skip = "Already closed"
      else if (action.kind === "reopen" && !closed) skip = "Already open"
      else args = [action.kind].concat(base)
    }
    return { key: p.key, iid: row.iid, title: String(row.title || ""), from: from, args: args, skip: skip }
  })
}
function cardsText(n) { return n === 1 ? "1 card" : n + " cards" }
function iidsText(steps) { return steps.map(function(s) { return "#" + s.iid }).join(" ") }
// The armed bar's question, its button and the note on what changes.
function bulkQuestion(action, n) {
  var c = cardsText(n)
  return action.kind === "move" ? "Move " + c + " to " + action.to.name + "?"
    : action.kind === "add" ? "Add " + action.label + " to " + c + "?"
    : action.kind === "remove" ? "Remove " + action.label + " from " + c + "?"
    : (action.kind === "close" ? "Close " : "Reopen ") + c + "?"
}
function bulkButton(action, n) {
  var c = cardsText(n)
  return action.kind === "move" ? "Move " + c : action.kind === "add" ? "Add to " + c : action.kind === "remove" ? "Remove from " + c
    : (action.kind === "close" ? "Close " : "Reopen ") + c
}
function bulkNote(action) {
  var tail = " One card at a time; nothing else changes."
  if (action.kind === "move") return (action.to.kind === "closed" ? "Each card closes on GitLab and keeps its labels."
    : action.to.kind === "open" ? "Each card loses its status label (closed ones reopen)."
    : "Each card's status label becomes " + action.to.name + " (closed ones reopen).") + tail
  if (action.kind === "add" || action.kind === "remove") return "Only the label " + action.label + " changes." + tail
  return (action.kind === "close" ? "Closing keeps each card's labels." : "Reopening keeps each card's labels.") + tail
}
// The armed bar's lines: what happens to which cards, grouped by where they are.
function bulkLines(plan, action) {
  var lines = [], groups = {}, order = []
  plan.forEach(function(s) {
    var text = s.skip ? "Skipped, " + s.skip.charAt(0).toLowerCase() + s.skip.slice(1)
      : action.kind === "move" ? s.from.name + " \u2192 " + action.to.name
      : action.kind === "add" ? "+ " + action.label : action.kind === "remove" ? "\u2212 " + action.label
      : action.kind === "close" ? "open \u2192 closed" : "closed \u2192 open"
    var g = (s.skip ? "1" : "0") + text
    if (!groups[g]) { groups[g] = { text: text, skip: !!s.skip, steps: [] }; order.push(g) }
    groups[g].steps.push(s)
  })
  order.sort(function(a, b) { return a.charAt(0) === b.charAt(0) ? 0 : a < b ? -1 : 1 })
  order.forEach(function(g) { lines.push({ text: groups[g].text, skip: groups[g].skip, iids: iidsText(groups[g].steps) }) })
  return lines
}
// One card's board-fetch answer. stop: nothing more should run (signed out,
// no glab, or no answer in time, which may have gone through).
function bulkOutcome(data, action) {
  var state = data && data.state ? String(data.state) : "error"
  var message = String((data && data.message) || "")
  if (state === "ready") return { ok: true, stop: false, text: action.kind === "move" ? "Moved to " + action.to.name
    : action.kind === "add" ? "Added " + action.label : action.kind === "remove" ? "Removed " + action.label
    : action.kind === "close" ? "Closed" : "Reopened" }
  if (state === "stale") return { ok: false, stop: false, text: "Not moved: it changed on GitLab after the board loaded. Nothing was written." }
  if (state === "logged-out" || state === "no-glab") return { ok: false, stop: true, text: message || "Not signed in." }
  if (state === "timeout" || /within 30 seconds/.test(message)) return { ok: false, stop: true,
    text: /may have/.test(message) ? message : (message || "No answer from glab.") + " It may have gone through." }
  return { ok: false, stop: false, text: message || "Failed." }
}
// The results line: "Moved 2 of 3 cards to review. 1 failed."
function bulkSummary(action, results) {
  var count = function(st) { return results.filter(function(r) { return r.status === st }).length }
  var done = count("done"), failed = count("failed"), untried = count("untried"), todo = results.length - count("skipped")
  var verb = action.kind === "move" ? "Moved" : action.kind === "add" ? "Added " + action.label + " to"
    : action.kind === "remove" ? "Removed " + action.label + " from" : action.kind === "close" ? "Closed" : "Reopened"
  var text = verb + " " + done + " of " + cardsText(todo) + (action.kind === "move" ? " to " + action.to.name : "") + "."
  var tail = []
  if (failed) tail.push(failed + " failed")
  if (untried) tail.push(untried + " not tried")
  return text + (tail.length ? " " + tail.join(", ") + "." : "")
}

if (typeof module !== "undefined") module.exports = { bulkCap: bulkCap, pickKey: pickKey, togglePick: togglePick, pickedCards: pickedCards, livePicks: livePicks, movable: movable, closeOrReopen: closeOrReopen, bulkPlan: bulkPlan, cardsText: cardsText, iidsText: iidsText, bulkQuestion: bulkQuestion, bulkButton: bulkButton, bulkNote: bulkNote, bulkLines: bulkLines, bulkOutcome: bulkOutcome, bulkSummary: bulkSummary }
