// Pure logic for the board and the issue view. No Qt here, so tests/logic.test.js
// runs it under node; QML passes in font metrics and Style.space (same pattern
// as Omarchy's panels/clock/Model.js).

// The widget's settings as plain JSON. Omarchy hands them over through Qt
// (QVariantMap), so their lists arrive as Qt sequences, not JS arrays:
// Array.isArray says false. A JSON round trip makes them real arrays (as
// Omarchy's own Indicators widget does); anything that can't be copied is {}.
function plainJson(value) {
  if (value === undefined || value === null) return {}
  try { var v = JSON.parse(JSON.stringify(value)); return v && typeof v === "object" ? v : {} } catch (e) { return {} }
}

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

// A column's count: "20+" when board-fetch says there are more than it holds
// (Closed, capped at the latest 20). Open and label columns are never capped.
function countLabel(column) { return String((column.issues || []).length) + (column.capped ? "+" : "") }

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
// never offers them. board-fetch guards the same set (any board's list label);
// its `def workflow` is this list (tests/run.sh checks they match).
var workflowLabels = ["research", "todo", "approved", "in progress", "review"]
function statusLabels(fetched, columns) {
  var names = (columns || []).filter(function(c) { return c.kind === "label" }).map(function(c) { return c.name })
  return lowerList(workflowLabels.concat(fetched || [], names))
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

// A busy dot's color: the column's own (#rrggbb), unless it is hard to see on
// the popup's background (WCAG contrast under 2:1) or unknown; then "" and the
// dot keeps the theme accent. background may be #rrggbb or #aarrggbb.
function luminance(hex) {
  var n = parseInt(String(hex).slice(-6), 16)
  return [n >> 16 & 255, n >> 8 & 255, n & 255].map(function(v) {
    v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
  }).reduce(function(sum, v, i) { return sum + v * [0.2126, 0.7152, 0.0722][i] }, 0)
}
function dotColor(color, background) {
  if (!/^#[0-9a-fA-F]{6}$/.test(String(color || "")) || !/^#([0-9a-fA-F]{2})?[0-9a-fA-F]{6}$/.test(String(background || ""))) return ""
  var a = luminance(color), b = luminance(background)
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) >= 2 ? color : ""
}

// Settings > Bots edits settings.bots as saved (not botsConfig's cleaned
// copy), so unknown keys, workingLists and other projects survive. Each edit
// returns the whole new map for Board.saveBots.
function plain(v) { return !!v && typeof v === "object" && !Array.isArray(v) }
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
function copied(raw) { return plain(raw) ? JSON.parse(JSON.stringify(raw)) : {} }
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
// Code spans and Markdown links are set aside as \x01n\x01 / \x02n\x02 while
// the other passes run (a URL inside link text is not linked again), then put
// back. Those two characters are dropped from the text first.
var lineLimit = 2000
function inline(text) {
  var spans = [], links = []
  text = String(text).replace(/[\x01\x02]/g, "")
  if (text.length > lineLimit) return escaped(text)
  return escaped(text)
    .replace(/`([^`]+)`/g, function(m, c) { spans.push(c); return "\x01" + (spans.length - 1) + "\x01" })
    .replace(/!?\[([^\][]*)\]\(([^)\s"]+)(?:[\s"][^)]*)?\)/g, function(m, t, url) {
      links.push("<a href=\"" + url + "\">" + (t || url) + "</a>"); return "\x02" + (links.length - 1) + "\x02" })
    .replace(/(^|[\s(])(https?:\/\/[^\s()"<]+)/g, "$1<a href=\"$2\">$2</a>")
    .replace(/\*\*(.+?)\*\*|__(.+?)__/g, "<b>$1$2</b>")
    .replace(/(^|\W)([*_])(\S(?:.*?\S)?)\2(?=\W|$)/g, "$1<i>$3</i>")
    .replace(/~~(.+?)~~/g, "<s>$1</s>")
    .replace(/\x02(\d+)\x02/g, function(m, i) { return links[i] })
    .replace(/\x01(\d+)\x01/g, function(m, i) { return "<code>&nbsp;" + spans[i] + "&nbsp;</code>" })
}

// A comment line GitLab would run as a quick action (/close, /label ...):
// board-fetch refuses those, the box says so before Post.
function quickAction(text) { return /(^|\n)[ \t]*\//.test(String(text || "")) }

// What a confirmed move does on GitLab, for the confirm (settings.confirmMoves).
function moveNote(from, to) {
  if (to.kind === "closed") return "This closes it on GitLab. Its labels stay."
  if (from.kind === "closed") return to.kind === "label" ? "This reopens it on GitLab and changes its status label." : "This reopens it on GitLab."
  if (from.kind === "label" && to.kind === "open") return "This removes its status label on GitLab."
  return "This changes its status label on GitLab."
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
// The popup's keys, by where they work (KeysView, and the README's Keyboard
// section, which tests/logic.test.js holds to this list). In a key, spaces
// separate keys, "or" separates choices, and + joins a chord.
var keyGroups = [
  { title: "Board", keys: [
    ["h j k l or ← ↓ ↑ →", "Move between cards"],
    ["Enter or Space", "Open the selected issue"],
    ["o", "Open the selected issue in the browser"],
    ["Shift+H or Shift+L", "Move the selected card to the column on the left or right, after a confirm"],
    ["r", "Refresh the board"]] },
  { title: "Confirm a move or a close", keys: [
    ["Enter or Space", "Yes"],
    ["Esc", "Cancel"]] },
  { title: "Anywhere", keys: [
    ["p", "Choose a project and board"],
    ["s", "Settings"],
    ["?", "These shortcuts (or the keyboard button in the header)"],
    ["Tab or Shift+Tab", "Next or previous bar panel"],
    ["Esc", "Back to the board; on the board, close"]] },
  { title: "Issue", keys: [
    ["o", "Open the issue in the browser"],
    ["c", "Write a comment"],
    ["e", "Edit labels"],
    ["x", "Close the issue, after a confirm, or reopen it"]] },
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

// The popup's height cap for a view. Settings and Keys are short, fixed lists:
// no cap, so they grow to the free screen height Omarchy's panel allows and
// scroll only past it. The board and an issue keep the cap (long columns or
// descriptions would otherwise make the popup jump to full height).
function heightCap(view, cap) { return view === "settings" || view === "keys" ? 0 : cap }

if (typeof module !== "undefined") {
  module.exports = {
    pipelineMark: pipelineMark, heightCap: heightCap,
    lowerList: lowerList, has: has, toggled: toggled, escaped: escaped, countLabel: countLabel, labelStyle: labelStyle, age: age, savedNote: savedNote,
    columnKey: columnKey, listSpec: listSpec, movedColumns: movedColumns, byline: byline, people: people,
    workflowLabels: workflowLabels, statusLabels: statusLabels, addableLabels: addableLabels, withColors: withColors, statusOn: statusOn, botsConfig: botsConfig, botStates: botStates, dotColor: dotColor, inColumn: inColumn,
    botsEntry: botsEntry, botUsable: botUsable, botNameTaken: botNameTaken, withBot: withBot, withoutBot: withoutBot, withBusy: withBusy,
    linkUrl: linkUrl, inline: inline, quickAction: quickAction, moveNote: moveNote, lineLimit: lineLimit, markdown: markdown, descriptionLimit: descriptionLimit, cursorMove: cursorMove, plainJson: plainJson, cursorFix: cursorFix, keyGroups: keyGroups, keyParts: keyParts
  }
}
