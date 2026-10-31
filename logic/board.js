// The board: columns, moves, keyboard cursor, keys list, refresh pace, popup height. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// A Review card's pipeline (board-fetch: {status, url, mr}) as its mark:
// a glyph per status in GitLab's own status colors (dark theme), and the tooltip.
// Anything else, or no pipeline, is null: nothing is drawn.
var pipelineMarks = {
  passed: { glyph: "\uf058", color: "#2da160" },
  failed: { glyph: "\uf057", color: "#ec5941" },
  running: { glyph: "\uf192", color: "#428fdc" },
  pending: { glyph: "\uf017", color: "#c17d10" },
  canceled: { glyph: "\uf05e", color: "#89888d" }
}
function pipelineMark(p) {
  var status = p && typeof p === "object" ? String(p.status || "") : ""
  if (!Object.prototype.hasOwnProperty.call(pipelineMarks, status)) return null
  var url = /^https:\/\//.test(String(p.url || "")) ? String(p.url) : ""
  var on = /^[!#A-Za-z0-9_.\/-]+$/.test(String(p.mr || "")) ? " on " + p.mr : ""
  return { glyph: pipelineMarks[status].glyph, color: pipelineMarks[status].color, url: url,
    tip: "Pipeline " + status + on + (url ? ": open it on GitLab" : "") }
}
function columnKey(column) { return column.kind + ":" + (column.listId || column.name) }
// The list argument board-fetch move takes: open, closed, or a label list id.
function listSpec(column) { return column.kind === "label" ? String(column.listId) : column.kind }
// Board columns after moving row from one column to another, as GitLab would
// show them: label swapped (kept when closing), card on top of the target.
function movedColumns(columns, row, from, to) {
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
// The board's keyboard cursor, { col, row, iid }, over lanes: one array of
// issue iids per shown column, null for a collapsed one. Moves skip collapsed
// and empty columns and stop at the edges.
function cursorMove(lanes, at, dx, dy) {
  var c = cursorFix(lanes, at)
  if (!c || dx === 0) return c && cursorAt(lanes, c.col, c.row + dy)
  for (var i = c.col + dx; i >= 0 && i < lanes.length; i += dx)
    if (lanes[i] && lanes[i].length) return cursorAt(lanes, i, c.row)
  return c
}
// After the board changes: the same issue if it is still shown (its old
// column first), else the nearest card to the old place; null if none.
function cursorFix(lanes, at) {
  var order = lanes.map(function(lane, i) { return i })
    .sort(function(a, b) { return Math.abs(a - at.col) - Math.abs(b - at.col) || a - b })
  var usable = order.filter(function(i) { return lanes[i] && lanes[i].length })
  for (var k = 0; k < usable.length; k++) {
    var row = lanes[usable[k]].indexOf(at.iid)
    if (row !== -1) return cursorAt(lanes, usable[k], row)
  }
  return usable.length ? cursorAt(lanes, usable[0], at.row) : null
}
function cursorAt(lanes, col, row) {
  var r = Math.max(0, Math.min(row, lanes[col].length - 1))
  return { col: col, row: r, iid: lanes[col][r] }
}
// The popup's keys, shown by ? and listed in the README's Keyboard section.
// The popup's keys, by where they work (KeysView, and the README's Keyboard
// section, which tests/logic.test.js holds to this list). In a key, spaces
// separate keys, "or" separates choices, and + joins a chord.
var keyGroups = [
  { title: "Board", keys: [
    ["h j k l or ← ↓ ↑ →", "Move between cards"],
    ["Enter or Space", "Open the selected issue"],
    ["o", "Open the selected issue in the browser"],
    ["Shift+H or Shift+L", "Move the selected card to the column on the left or right, after a confirm"],
    ["v", "Pick the selected card for a bulk action (Ctrl+click picks with the mouse)"],
    ["r", "Refresh the board"]] },
  { title: "Confirm a move or a close", keys: [
    ["Enter or Space", "Yes"],
    ["Esc", "Cancel"]] },
  { title: "Picked cards", keys: [
    ["Shift+H or Shift+L", "Move them to the column on the left or right"],
    ["x", "Close them, or reopen them when all are closed"],
    ["e", "Add a label to them"],
    ["Enter or Space", "Confirm the action shown (the same key again works too)"],
    ["Esc", "Back one step; while it runs, stop after the current card; else clear the picks"]] },
  { title: "Anywhere", keys: [
    ["p", "Choose a project and board"],
    ["s", "Settings"],
    ["m", "Merge requests waiting on your review, and yours"],
    ["?", "These shortcuts (or the keyboard button in the header)"],
    ["Tab or Shift+Tab", "Next or previous bar panel"],
    ["Esc", "Back to the board; on the board, close"]] },
  { title: "Issue", keys: [
    ["o", "Open the issue in the browser"],
    ["c", "Write a comment"],
    ["e", "Edit labels"],
    ["x", "Close the issue, after a confirm, or reopen it"]] },
  { title: "Merge requests", keys: [
    ["j k or ↓ ↑", "Move between merge requests"],
    ["Enter or o", "Open the selected one in the browser"],
    ["r", "Refresh the lists"]] },
  { title: "Comment box", keys: [
    ["Ctrl+Enter", "Post the comment"],
    ["Esc", "Leave the box"]] },
  { title: "Pickers and filters", keys: [
    ["↑ ↓", "Move in the list (j and k too, once you're choosing a board)"],
    ["Enter", "Pick the selected row, or the first match"],
    ["Esc", "Close the picker, the label editor or the new-bot form"]] },
  { title: "Setup panel", keys: [
    ["Enter or Space", "Its main button"],
    ["r", "Try again"]] }
]
// A key as keycaps and the words between them: "Shift+H or L" ->
// [{cap:"Shift"},{text:"+"},{cap:"H"},{text:"or"},{cap:"L"}].
function keyParts(key) {
  var out = []
  String(key).split(" ").forEach(function(word) {
    if (word === "") return
    if (word === "or") { out.push({ text: "or" }); return }
    var parts = word.length > 1 ? word.split("+") : [word]
    parts.forEach(function(p, i) { if (i > 0) out.push({ text: "+" }); out.push({ cap: p }) })
  })
  return out
}
// Adaptive refresh. A board's pace comes from its answers: sig (each card's
// column and labels), calm (answers in a row without a change) and active
// (cards in an "in progress" or "doing" column).
function boardSig(data) {
  return (data.columns || []).map(function(c) {
    return columnKey(c) + "=" + (c.issues || []).map(function(i) {
      return i.iid + "[" + (i.labels || []).slice().sort().join(",") + "]"
    }).sort().join(" ")
  }).join("|")
}
function boardActive(data) {
  return (data.columns || []).some(function(c) {
    return c.kind === "label" && /^(in[ -]?progress|doing)$/i.test(String(c.name || "").trim()) && (c.issues || []).length > 0
  })
}
// The first answer counts as calm 2 (the user's interval); a change resets to 0.
function nextPace(prev, data) {
  if (!data || data.state !== "ready") return prev || null
  var sig = boardSig(data)
  return { sig: sig, calm: !prev ? 2 : sig === prev.sig ? prev.calm + 1 : 0, active: boardActive(data) }
}
// The interval to use, in seconds, and why. Something moved in the last two
// answers: half the setting. Then the setting; after every two more calm
// answers it doubles, up to 4x the setting, but not past the setting while
// cards are in progress. Never under 30 s.
var paceFloorSec = 30
function adaptiveInterval(baseSec, pace) {
  var base = Math.max(paceFloorSec, Number(baseSec) || 60)
  if (!pace) return { sec: base, why: "your setting" }
  if (pace.calm < 2) return { sec: Math.max(paceFloorSec, Math.round(base / 2)), why: "cards moved recently" }
  var slow = Math.min(base * 4, base * Math.pow(2, Math.floor((pace.calm - 2) / 2)))
  if (slow > base && pace.active) return { sec: base, why: "cards in progress" }
  return { sec: slow, why: slow > base ? "nothing changed lately" : "your setting" }
}
function durationText(sec) {
  sec = Math.round(Number(sec) || 0)
  if (sec < 60) return sec + " s"
  var m = Math.floor(sec / 60), r = sec % 60
  return r === 0 ? m + " min" : m + " min " + r + " s"
}
// The popup's height cap for a view. Settings and Keys are short, fixed lists:
// no cap, so they grow to the free screen height Omarchy's panel allows and
// scroll only past it. The board and an issue keep the cap (long columns or
// descriptions would otherwise make the popup jump to full height).
function heightCap(view, cap) { return view === "settings" || view === "keys" ? 0 : cap }

if (typeof module !== "undefined") module.exports = { pipelineMarks: pipelineMarks, pipelineMark: pipelineMark, columnKey: columnKey, listSpec: listSpec, movedColumns: movedColumns, cursorMove: cursorMove, cursorFix: cursorFix, cursorAt: cursorAt, keyGroups: keyGroups, keyParts: keyParts, boardSig: boardSig, boardActive: boardActive, nextPace: nextPace, paceFloorSec: paceFloorSec, adaptiveInterval: adaptiveInterval, durationText: durationText, heightCap: heightCap }
