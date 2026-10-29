// Pure logic for the board and the issue view. No Qt here, so tests/logic.test.js
// runs it under node; QML passes in font metrics and Style.space (same pattern
// as Omarchy's panels/clock/Model.js).

// Settings lists: lowercase names, from an array or a comma-separated string.
function lowerList(value) {
  var list = Array.isArray(value) ? value : String(value || "").split(",")
  return list.map(function(v) { return String(v).trim().toLowerCase() }).filter(function(v) { return v !== "" })
}
function has(list, name) { return (list || []).indexOf(String(name).toLowerCase()) !== -1 }
function toggled(list, name) {
  var key = String(name).toLowerCase()
  return has(list, key) ? list.filter(function(v) { return v !== key }) : list.concat([key])
}

function escaped(text) { return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") }

// A label's colors ({ color, textColor }, validated #rrggbb from board-fetch).
// Text: the label's own text color, else dark or white by luminance.
function labelStyle(entry) {
  if (!entry || !entry.color) return null
  var n = parseInt(entry.color.slice(1), 16)
  var light = (0.299 * (n >> 16 & 255) + 0.587 * (n >> 8 & 255) + 0.114 * (n & 255)) / 255 > 0.6
  return { bg: entry.color, fg: entry.textColor || (light ? "#1f1e24" : "#ffffff") }
}

// Status labels: the board's list labels and the workflow labels of the
// no-board fallback. They change only by dragging a card, so the label editor
// never offers them. board-fetch guards the same set (any board's list label).
var workflowLabels = ["research", "todo", "approved", "in progress", "review"]
function statusLabels(fetched, columns) {
  var names = (columns || []).filter(function(c) { return c.kind === "label" }).map(function(c) { return c.name })
  return lowerList(workflowLabels.concat(fetched || [], names))
}
function editableLabels(labels, status) {
  return (labels || []).map(String).filter(function(name) { return !has(status, name) })
}
// Project labels ({ name, color, textColor }) the issue could take: not on it,
// not status, matching the filter (any case, anywhere in the name).
function addableLabels(all, current, status, filter) {
  var needle = String(filter || "").trim().toLowerCase()
  return (all || []).filter(function(l) {
    return (current || []).indexOf(l.name) === -1 && !has(status, l.name) && l.name.toLowerCase().indexOf(needle) !== -1
  })
}
// The issue's status labels, in its own order: closing keeps them.
function statusOn(labels, status) {
  return (labels || []).map(String).filter(function(name) { return has(status, name) })
}
// The board's label colors plus those from board-fetch labels.
function withColors(colors, labels) {
  var out = {}
  Object.keys(colors || {}).forEach(function(k) { out[k] = colors[k] })
  ;(labels || []).forEach(function(l) { if (l.color && !out[l.name]) out[l.name] = { color: l.color, textColor: l.textColor } })
  return out
}

// "5m", "3h", "4d", "2w", "6mo", "1y" from iso to since (default: now).
function age(iso, since) {
  var ms = new Date(since || Date.now()) - new Date(iso)
  if (!iso || !(ms >= 0)) return ""
  var m = ms / 60000, h = m / 60, d = h / 24
  return m < 60 ? Math.floor(m) + "m" : h < 24 ? Math.floor(h) + "h" : d < 14 ? Math.floor(d) + "d"
    : d < 60 ? Math.floor(d / 7) + "w" : d < 365 ? Math.floor(d / 30) + "mo" : Math.floor(d / 365) + "y"
}

// Header note while the saved board shows and the fresh one loads.
function savedNote(iso, now) {
  var a = age(iso, now)
  return (a === "" || a === "0m" ? "Saved just now" : "Saved " + a + " ago") + " · updating…"
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

// "o_devvy · created 3h ago · updated 5m ago"; card rows (shown while the
// issue loads) have no author or updatedAt yet, so those parts come later.
function byline(issue, now) {
  var created = age(issue.createdAt, now), updated = age(issue.updatedAt, now)
  return [issue.author || "", created ? "created " + created + " ago" : "", updated ? "updated " + updated + " ago" : ""]
    .filter(function(part) { return part !== "" }).join(" · ")
}
function people(issue) {
  var names = (issue.assignees || []).map(function(a) { return a.username || a })  // card rows carry objects
  return [names.length ? "assigned " + names.join(", ") : "", issue.milestone ? "milestone " + issue.milestone : ""]
    .filter(function(part) { return part !== "" }).join(" · ")
}

// A Markdown link to open: absolute https as is, GitLab-relative paths on
// the issue's host; anything else "".
function linkUrl(link, issueUrl) {
  var value = String(link || "")
  if (/^\//.test(value) && issueUrl) value = String(issueUrl).replace(/^(https:\/\/[^\/]+).*$/, "$1") + value
  return /^https:\/\//.test(value) ? value : ""
}

// GitLab Markdown to the HTML subset Text.RichText draws, so headings,
// spacing, bullets and code can be styled (Text.MarkdownText can't be).
// All text is escaped first: raw HTML in the issue shows as text, and images
// become links, so nothing is loaded from the network.
// A longer line stays plain text: the passes below can take time quadratic in
// a line's length, and they run on the shell's UI thread.
var lineLimit = 2000
function inline(text) {
  var spans = []
  if (String(text).length > lineLimit) return escaped(text)
  return escaped(text)
    .replace(/`([^`]+)`/g, function(m, c) { spans.push(c); return "\x01" + (spans.length - 1) + "\x01" })
    .replace(/!?\[([^\][]*)\]\(([^)\s"]+)(?:[\s"][^)]*)?\)/g, function(m, t, url) { return "<a href=\"" + url + "\">" + (t || url) + "</a>" })
    .replace(/(^|[\s(])(https?:\/\/[^\s()"]+)/g, "$1<a href=\"$2\">$2</a>")
    .replace(/\*\*(.+?)\*\*|__(.+?)__/g, "<b>$1$2</b>")
    .replace(/(^|\W)([*_])(\S(?:.*?\S)?)\2(?=\W|$)/g, "$1<i>$3</i>")
    .replace(/~~(.+?)~~/g, "<s>$1</s>")
    .replace(/\x01(\d+)\x01/g, function(m, i) { return "<code>&nbsp;" + spans[i] + "&nbsp;</code>" })
}
// Only the first descriptionLimit characters are drawn, cut at a line break;
// the issue view links to the rest on GitLab.
var descriptionLimit = 20000
function clipped(md) {
  var text = String(md)
  if (text.length <= descriptionLimit) return text
  var cut = text.lastIndexOf("\n", descriptionLimit)
  return text.slice(0, cut > 0 ? cut : descriptionLimit)
}
// advance(text): its width in px in the description font; space(px): Style.space.
function markdown(md, advance, space) {
  var out = [], block = [], open = "<p>", rows = [], code = null
  function flush() {
    if (block.length) out.push(open + block.map(inline).join("<br>") + "</p>")
    if (rows.length) out.push("<table border='1' cellspacing='0' cellpadding='" + space(3) + "'>" + rows.join("") + "</table>")
    block = []; rows = []; open = "<p>"
  }
  clipped(md).replace(/\r/g, "").split("\n").forEach(function(line) {
    var m
    if (code !== null) {
      if (/^\s*(```|~~~)/.test(line)) { out.push("<pre>" + code.join("\n") + "</pre>"); code = null }
      else code.push(escaped(line))
    } else if (/^\s*(```|~~~)/.test(line)) { flush(); code = [] }
    else if ((m = /^(#{1,6})\s+(.*?)[\s#]*$/.exec(line))) { flush(); out.push("<p class='h" + Math.min(m[1].length, 3) + "'>" + inline(m[2]) + "</p>") }
    else if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { flush(); out.push("<hr>") }
    else if ((m = /^(\s*)([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?(.*)$/.exec(line))) {
      // Hanging indent: wrapped lines line up with the text, not the bullet.
      flush()
      var mark = (m[3] ? (/[xX]/.test(m[3]) ? "☑" : "☐") : /\d/.test(m[2]) ? m[2] : "•") + " "
      var level = Math.floor(m[1].replace(/\t/g, "  ").length / 2), hang = advance(mark)
      open = "<p class='li' style='margin-left: " + Math.round(level * advance("  ") + hang) + "px; text-indent: -" + Math.round(hang) + "px'>"
      block = [mark + m[4]]
    } else if ((m = /^\s*\|(.*)\|\s*$/.exec(line))) {
      if (block.length) flush()
      if (!/^[\s|:-]+$/.test(m[1])) {
        var tag = rows.length ? "td" : "th"
        rows.push("<tr>" + m[1].split("|").map(function(c) { return "<" + tag + ">" + inline(c.trim()) + "</" + tag + ">" }).join("") + "</tr>")
      }
    } else if ((m = /^\s*>\s?(.*)$/.exec(line))) {
      if (open.indexOf("quote") === -1) { flush(); open = "<p class='quote' style='margin-left: " + space(10) + "px'>" }
      block.push(m[1])
    } else if (line.trim() === "") flush()
    else { if (rows.length) flush(); block.push(line.trim()) }  // GitLab keeps single line breaks
  })
  if (code !== null) out.push("<pre>" + code.join("\n") + "</pre>")
  flush()
  return out.join("")
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
var keys = [
  ["h j k l or arrows", "Move between cards; up and down in the picker"],
  ["Enter or Space", "Open the selected issue; pick the selected row; the setup panel's main button"],
  ["o", "Open the issue in the browser"],
  ["c", "Write a comment (issue view)"],
  ["Ctrl+Enter", "Post the comment"],
  ["r", "Refresh the board; Try again on the setup panel"],
  ["p", "Choose a project and board"],
  ["s", "Settings"],
  ["?", "This list of keys"],
  ["Tab or Shift+Tab", "Next or previous bar panel"],
  ["Escape", "Leave the comment box; otherwise back to the board; on the board, close"]
]

if (typeof module !== "undefined") {
  module.exports = {
    lowerList: lowerList, has: has, toggled: toggled, escaped: escaped, labelStyle: labelStyle, age: age, savedNote: savedNote,
    columnKey: columnKey, listSpec: listSpec, movedColumns: movedColumns, byline: byline, people: people,
    workflowLabels: workflowLabels, statusLabels: statusLabels, editableLabels: editableLabels, addableLabels: addableLabels, withColors: withColors, statusOn: statusOn,
    linkUrl: linkUrl, inline: inline, lineLimit: lineLimit, markdown: markdown, descriptionLimit: descriptionLimit, cursorMove: cursorMove, cursorFix: cursorFix, keys: keys
  }
}
