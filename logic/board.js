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
// The popup's keys, by where they work (KeysView, two columns: the first four
// groups on the left), and the README's Keyboard section, which
// tests/logic.test.js holds to this list. A key: " / " separates choices, +
// joins a chord, _ is a space inside one cap ("h_j_k_l" is one cap). An
// action: what it does, then after " · " a quiet note. Each fits one line.
// The words for the action that leaves the plugin: where Settings sends links.
function openLabel(mode) { return mode === "app" ? "Open in app window" : "Open in browser" }
var keyGroups = [
  { title: "Board", keys: [
    ["h_j_k_l / ←_↓_↑_→", "Move between cards"],
    ["Enter / Space", "Open the issue"],
    ["o", "Open in browser"],
    ["y", "Copy the link · or right-click"],
    ["Shift+H / L", "Move left / right · asks first when the project is in confirmMoves"],
    ["v", "Pick for bulk · or Ctrl+click"],
    ["b", "Show or hide the bots"],
    ["r", "Refresh"]] },
  { title: "Picked cards", keys: [
    ["Shift+H / L", "Move them left / right"],
    ["x", "Close, or reopen if all closed"],
    ["e", "Add a label"],
    ["Enter / Space", "Run the action shown · or its key"],
    ["Esc", "Step back or stop · else unpick"]] },
  { title: "Confirm a move or a close", keys: [
    ["Enter / Space", "Yes"],
    ["Esc", "Cancel"]] },
  { title: "Setup panel", keys: [
    ["Enter / Space", "Its main button"],
    ["r", "Try again"]] },
  { title: "Header menus", keys: [
    ["j_k / ↓_↑", "Move the selection"],
    ["Enter / Space", "Choose it"],
    ["Esc", "Close the menu"]] },
  { title: "Anywhere", keys: [
    ["p", "Project and board"],
    ["s", "Settings"],
    ["m", "Merge requests"],
    ["t", "To-do"],
    ["?", "These shortcuts"],
    ["Tab / Shift+Tab", "Next / previous control"],
    ["Ctrl+Tab", "Next bar panel"],
    ["Ctrl+Shift+Tab", "Previous bar panel"],
    ["Esc", "Back to the board, then close"]] },
  { title: "Issue", keys: [
    ["o", "Open in browser"],
    ["y", "Copy the link"],
    ["c", "Write a comment"],
    ["e", "Edit labels"],
    ["x", "Close or reopen · asks first"]] },
  { title: "Comment box", keys: [
    ["Ctrl+Enter", "Post"],
    ["Esc", "Leave the box"]] },
  { title: "Merge requests", keys: [
    ["j_k / ↓_↑", "Move between them"],
    ["Enter / o", "Open in browser"],
    ["y", "Copy the link · or right-click"],
    ["r", "Refresh the lists"]] },
  { title: "To-do", keys: [
    ["j_k / ↓_↑", "Move between them"],
    ["Enter / o", "Open in browser"],
    ["y", "Copy the link · or right-click"],
    ["r", "Refresh the lists"]] },
  { title: "Scrolling", keys: [
    ["j_k / ↓_↑", "Scroll · settings, shortcuts, an issue"]] },
  { title: "Pickers and filters", keys: [
    ["j_k / ↓_↑", "Move up / down"],
    ["Ctrl+j / k", "The same while typing a filter · or Ctrl+n / p"],
    ["Enter", "Pick the row or first match"],
    ["Esc", "Close the picker or form"]] },
  { title: "Outlined control", keys: [
    ["Enter / Space", "Press it, or tick the box"],
    ["h_l / ←_→", "Pick a segment in Settings"],
    ["Esc", "Drop the outline"]] }
]
// A key as caps and the quiet "/" between choices: "Shift+H / L" ->
// [{cap:"Shift"},{cap:"H",joined:true},{text:"/"},{cap:"L"}] (joined: drawn
// tight against the cap before it, a chord); "h_j_k_l" -> [{cap:"h j k l"}].
function keyParts(key) {
  var out = []
  String(key).split(" ").forEach(function(word) {
    if (word === "") return
    if (word === "/") { out.push({ text: "/" }); return }
    var parts = word.length > 1 ? word.split("+") : [word]
    parts.forEach(function(p, i) { out.push(i > 0 ? { cap: p.replace(/_/g, " "), joined: true } : { cap: p.replace(/_/g, " ") }) })
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
// Opening the popup: due once the last fetch is older than the setting itself
// (never the slowed pace), less 2 s so a tick on the boundary counts.
function openMaxAgeMs(baseSec) { return Math.max(paceFloorSec, Number(baseSec) || 60) * 1000 - 2000 }
function adaptiveInterval(baseSec, pace) {
  var base = Math.max(paceFloorSec, Number(baseSec) || 60)
  if (!pace) return { sec: base, why: "your setting" }
  if (pace.calm < 2) return { sec: Math.max(paceFloorSec, Math.round(base / 2)), why: "cards moved recently" }
  var slow = Math.min(base * 4, base * Math.pow(2, Math.floor((pace.calm - 2) / 2)))
  if (slow > base && pace.active) return { sec: base, why: "cards in progress" }
  return { sec: slow, why: slow > base ? "nothing changed lately" : "your setting" }
}
// The pace in words, for the tip on "Updated": the setting first, then what
// the pace did to it and why ("Every 2 min · slowed to 4 min, nothing changed
// lately"); just the setting when it holds. closedToo: an alert also has it
// refresh with the popup closed, at the same pace (BoardService.background).
function cadenceText(baseSec, cad, closedToo) {
  var base = Math.max(paceFloorSec, Number(baseSec) || 60), t = "Every " + durationText(base)
  if (cad.sec > base) t += " · slowed to " + durationText(cad.sec) + ", " + cad.why
  else if (cad.sec < base) t += " · sped up to " + durationText(cad.sec) + ", " + cad.why
  else if (cad.why === "cards in progress") t += " · not slowed, cards in progress"
  return t + (closedToo ? " · also while closed, for alerts" : "")
}
function durationText(sec) {
  sec = Math.round(Number(sec) || 0)
  if (sec < 60) return sec + " s"
  var m = Math.floor(sec / 60), r = sec % 60
  return r === 0 ? m + " min" : m + " min " + r + " s"
}
// Keyed lists (BoardView.qml): the steps that turn the keys a ListModel holds
// (have) into the wanted ones (want), keeping every row that stays, so its
// delegate is updated in place instead of rebuilt. Steps, applied in order:
// { op: "remove", at }, { op: "move", from, to } (one row) and
// { op: "insert", at, k }. A key twice in want counts once.
function keyOps(have, want) {
  var seen = {}, keys = []
  want.forEach(function(k) { k = String(k); if (!seen[k]) { seen[k] = true; keys.push(k) } })
  var cur = have.map(String), ops = []
  for (var i = cur.length - 1; i >= 0; i--) if (!seen[cur[i]]) { ops.push({ op: "remove", at: i }); cur.splice(i, 1) }
  for (var j = 0; j < keys.length; j++) {
    var at = cur.indexOf(keys[j], j)
    if (at === -1) { ops.push({ op: "insert", at: j, k: keys[j] }); cur.splice(j, 0, keys[j]) }
    else if (at !== j) { ops.push({ op: "move", from: at, to: j }); cur.splice(j, 0, cur.splice(at, 1)[0]) }
  }
  return ops
}

if (typeof module !== "undefined") module.exports = { pipelineMarks: pipelineMarks, pipelineMark: pipelineMark, columnKey: columnKey, listSpec: listSpec, movedColumns: movedColumns, cursorMove: cursorMove, cursorFix: cursorFix, cursorAt: cursorAt, keyGroups: keyGroups, openLabel: openLabel, keyParts: keyParts, boardSig: boardSig, boardActive: boardActive, nextPace: nextPace, paceFloorSec: paceFloorSec, openMaxAgeMs: openMaxAgeMs, adaptiveInterval: adaptiveInterval, durationText: durationText, cadenceText: cadenceText, keyOps: keyOps }
