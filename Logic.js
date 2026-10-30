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

// Desktop alerts (settings.alerts, keyed by project like bots): { review, idle }.
function alertsFor(raw, project) {
  var e = raw && typeof raw === "object" && !Array.isArray(raw) ? raw[project] : null
  return { review: !!(e && e.review === true), idle: !!(e && e.idle === true) }
}
function withAlert(raw, project, kind, on) {
  var all = plainJson(raw), cur = alertsFor(all, project)
  cur[kind] = !!on
  all[project] = cur
  return all
}
// The cards in the board's Review column(s), by iid.
function reviewRows(data) {
  var out = {}
  ;(data && data.columns || []).forEach(function(c) {
    if (c.kind === "label" && String(c.name || "").trim().toLowerCase() === "review")
      (c.issues || []).forEach(function(row) { out[row.iid] = row })
  })
  return out
}
function httpsUrl(url) { return /^https:\/\/[^\s"'<>]+$/.test(String(url || "")) ? String(url) : "" }
function boardUrl(data) {
  var p = String(data && data.project || "")
  if (!/^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)+$/.test(p)) return ""
  var id = data.board && /^[0-9]+$/.test(String(data.board.id)) ? "/-/boards/" + data.board.id : "/-/boards"
  return "https://gitlab.com/" + p + id
}
function oneLine(text, max) {
  var t = String(text || "").replace(/\s+/g, " ").trim()
  return t.length > max ? t.slice(0, max - 1) + "…" : t
}
// What changed from one good answer to the next, as notifications:
// [{ headline, body (plain), url }]. opts: { review, idle, bots (settings.bots),
// ignore (iids this user just moved) }. Several cards entering review make one.
function alertEvents(prev, next, opts) {
  var out = []
  if (!prev || !next || prev.state !== "ready" || next.state !== "ready" || prev.project !== next.project) return out
  var project = String(next.project)
  if (opts.review) {
    var before = reviewRows(prev), now = reviewRows(next), ignore = opts.ignore || []
    var came = Object.keys(now).filter(function(iid) { return !before[iid] && ignore.indexOf(Number(iid)) === -1 && ignore.indexOf(String(iid)) === -1 })
      .map(function(iid) { return now[iid] })
    if (came.length === 1) {
      var r = came[0]
      out.push({ headline: "#" + r.iid + " is in review", body: "#" + r.iid + " " + oneLine(r.title, 80) + " · " + project, url: httpsUrl(r.url) || boardUrl(next) })
    } else if (came.length > 1) {
      var shown = came.slice(0, 3).map(function(r) { return "#" + r.iid + " " + oneLine(r.title, 40) })
      out.push({ headline: came.length + " cards entered review", body: shown.join(", ") + (came.length > 3 ? " +" + (came.length - 3) + " more" : "") + " · " + project, url: boardUrl(next) })
    }
  }
  if (opts.idle) {
    var cfg = botsConfig(opts.bots, project)
    var was = botStates(cfg, prev.columns), is = botStates(cfg, next.columns)
    var stopped = is.filter(function(b, i) { return was[i] && was[i].state === "working" && b.state !== "working" })
    if (stopped.length > 0)
      out.push({ headline: "Stopped working: " + stopped.map(function(b) { return oneLine(b.name, 30) }).join(", "),
                 body: "On " + project + ": " + stopped.map(function(b) { return oneLine(b.name, 30) + (b.state === "waiting" ? " is waiting in " + b.column : " has no cards left") }).join("; "),
                 url: boardUrl(next) })
  }
  return out
}
// The command for one notification (bin/omarchy-notification-send in Omarchy
// 4.0.6): options, then the headline (plain text) and the body (StyledText, so
// escaped; it never starts with "-", so it can't be read as an option), and
// --exec last with the click command as separate words. Low urgency under
// our own app name: Do Not Disturb holds it (only critical notify-send passes).
function notifyArgv(ev) {
  var argv = ["omarchy-notification-send", "--app-name", "GitLab board", "-u", "low", "-g", "\uf296", oneLine(ev.headline, 120), escaped(oneLine(ev.body, 300))]
  if (httpsUrl(ev.url)) argv = argv.concat(["--exec", "xdg-open", ev.url])
  return argv
}

// --- Merge requests view (board-fetch mrs) -------------------------------------
// The answer, checked: rows keep only what the view shows, links only https.
// Anything but a ready answer is { state, message } with no rows.
function mrsAnswer(raw) {
  var data = null
  try { data = JSON.parse(String(raw || "")) } catch (e) {}
  if (!data || typeof data !== "object") return { state: "error", message: "board-fetch gave an unreadable answer.", review: [], mine: [] }
  if (data.state !== "ready") return { state: String(data.state || "error"), message: String(data.message || "Could not load merge requests."), review: [], mine: [] }
  return { state: "ready", message: "", scope: String(data.scope || "all"), updatedAt: String(data.updatedAt || ""), review: mrRows(data.review), mine: mrRows(data.mine) }
}
var reviewerStates = ["unreviewed", "review_started", "reviewed", "requested_changes", "approved", "unapproved"]
function mrPerson(p) {
  p = p && typeof p === "object" ? p : {}
  return { username: String(p.username || ""), name: String(p.name || p.username || ""), avatar: httpsUrl(p.avatar) }
}
function mrRows(list) {
  return (Array.isArray(list) ? list : []).filter(function(r) { return r && typeof r === "object" && Number(r.iid) > 0 }).map(function(r) {
    var iid = Number(r.iid)
    return { iid: iid, title: String(r.title || ""), url: httpsUrl(r.url), draft: r.draft === true, project: String(r.project || ""),
      branch: String(r.branch || ""), updatedAt: String(r.updatedAt || ""), status: String(r.status || ""), author: mrPerson(r.author),
      pipeline: r.pipeline && typeof r.pipeline === "object" ? Object.assign({}, r.pipeline, { mr: "!" + iid }) : null,
      reviewers: (Array.isArray(r.reviewers) ? r.reviewers : []).filter(function(p) { return p && typeof p === "object" }).map(function(p) {
        var o = mrPerson(p)
        o.state = reviewerStates.indexOf(p.state) !== -1 ? p.state : ""
        return o
      }) }
  })
}
// The pill on a row, from GitLab's detailed_merge_status; tone picks its color.
// Statuses that only mean "GitLab is still checking" show nothing.
var mrStatuses = {
  mergeable: ["Ready", "good"], ci_still_running: ["Pipeline running", ""], ci_must_pass: ["Pipeline must pass", "warn"],
  draft_status: ["Draft", ""], requested_changes: ["Changes requested", "warn"], conflict: ["Conflicts", "bad"],
  need_rebase: ["Needs rebase", "warn"], not_approved: ["Needs approval", ""], discussions_not_resolved: ["Open threads", ""],
  merge_request_blocked: ["Blocked", "warn"], status_checks_must_pass: ["Checks must pass", "warn"], merge_time: ["Not before its merge time", ""]
}
var toneColors = { good: "#2da160", warn: "#c17d10", bad: "#ec5941" }
function mrStatus(row) {
  if (row && row.draft) return { text: "Draft", color: "" }
  var s = row && Object.prototype.hasOwnProperty.call(mrStatuses, row.status) ? mrStatuses[row.status] : null
  return s ? { text: s[0], color: toneColors[s[1]] || "" } : { text: "", color: "" }
}
// A reviewer's state as a small mark on their avatar, and the words for its tip.
var reviewerMarks = {
  approved: { glyph: "\uf00c", color: "#2da160", words: "approved" },
  requested_changes: { glyph: "\uf12a", color: "#c17d10", words: "requested changes" },
  reviewed: { glyph: "\uf075", color: "#428fdc", words: "left a review" },
  review_started: { glyph: "\uf040", color: "#428fdc", words: "is reviewing" },
  unapproved: { glyph: "\uf05e", color: "#89888d", words: "withdrew their approval" },
  unreviewed: { glyph: "", color: "", words: "hasn't reviewed yet" }
}
function reviewerMark(person) {
  var m = person && Object.prototype.hasOwnProperty.call(reviewerMarks, person.state) ? reviewerMarks[person.state] : null
  var name = person ? person.name || person.username || "?" : "?"
  return { glyph: m ? m.glyph : "", color: m ? m.color : "", tip: name + (m ? " " + m.words : "") }
}
// The second line of a row: project, branch, and who wrote it (review) or how
// many reviewers it has (yours).
function mrSubline(row, section) {
  var n = (row.reviewers || []).length
  var who = section === "review" ? (row.author && row.author.name ? "by " + row.author.name : "")
    : n === 0 ? "no reviewer yet" : n === 1 ? "1 reviewer" : n + " reviewers"
  return [row.project, row.branch, who].filter(function(x) { return x !== "" }).join("  \u00b7  ")
}
// The header button's badge: how many wait on his review ("" when unknown or none).
function mrBadge(answer) {
  var n = answer && answer.state === "ready" ? answer.review.length : 0
  return n <= 0 ? "" : n > 9 ? "9+" : String(n)
}
// board-fetch arguments for a scope: "all", or one project path.
function mrsArgs(scope) {
  return /^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)+$/.test(String(scope)) && String(scope).indexOf("..") === -1 ? ["mrs", "--project", String(scope)] : ["mrs"]
}

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

// The popup's height cap for a view. Settings and Keys are short, fixed lists:
// no cap, so they grow to the free screen height Omarchy's panel allows and
// scroll only past it. The board and an issue keep the cap (long columns or
// descriptions would otherwise make the popup jump to full height).
function heightCap(view, cap) { return view === "settings" || view === "keys" ? 0 : cap }

if (typeof module !== "undefined") {
  module.exports = {
    pipelineMark: pipelineMark, heightCap: heightCap, mrsAnswer: mrsAnswer, mrStatus: mrStatus, reviewerMark: reviewerMark, mrSubline: mrSubline, mrBadge: mrBadge, mrsArgs: mrsArgs, boardSig: boardSig, boardActive: boardActive, nextPace: nextPace, adaptiveInterval: adaptiveInterval, durationText: durationText, alertsFor: alertsFor, withAlert: withAlert, reviewRows: reviewRows, httpsUrl: httpsUrl, boardUrl: boardUrl, alertEvents: alertEvents, notifyArgv: notifyArgv,
    lowerList: lowerList, has: has, toggled: toggled, escaped: escaped, countLabel: countLabel, labelStyle: labelStyle, age: age, savedNote: savedNote,
    columnKey: columnKey, listSpec: listSpec, movedColumns: movedColumns, byline: byline, people: people,
    workflowLabels: workflowLabels, statusLabels: statusLabels, addableLabels: addableLabels, withColors: withColors, statusOn: statusOn, botsConfig: botsConfig, botStates: botStates, dotColor: dotColor, inColumn: inColumn,
    botsEntry: botsEntry, botUsable: botUsable, botNameTaken: botNameTaken, withBot: withBot, withoutBot: withoutBot, withBusy: withBusy,
    linkUrl: linkUrl, inline: inline, quickAction: quickAction, moveNote: moveNote, lineLimit: lineLimit, markdown: markdown, descriptionLimit: descriptionLimit, cursorMove: cursorMove, plainJson: plainJson, cursorFix: cursorFix, keyGroups: keyGroups, keyParts: keyParts,
    bulkCap: bulkCap, pickKey: pickKey, togglePick: togglePick, pickedCards: pickedCards, livePicks: livePicks, movable: movable, closeOrReopen: closeOrReopen,
    bulkPlan: bulkPlan, bulkQuestion: bulkQuestion, bulkButton: bulkButton, bulkNote: bulkNote, bulkLines: bulkLines, bulkOutcome: bulkOutcome, bulkSummary: bulkSummary
  }
}
