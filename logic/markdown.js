// Issue text: byline, people, links, inline Markdown and the description renderer. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { Core = m.Core; }
function age(iso, since) { return Core.age(iso, since) }
function escaped(text) { return Core.escaped(text) }

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
// the issue's host; anything else "". The same check as Board.openUrl
// (Core.httpsUrl), so the tooltip never shows a link a click won't open.
function linkUrl(link, issueUrl) {
  var value = String(link || "")
  if (/^\//.test(value) && issueUrl) value = String(issueUrl).replace(/^(https:\/\/[^\/]+).*$/, "$1") + value
  return Core.httpsUrl(value)
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
function quickAction(text) { return /(^|[\r\n])[ \t]*\//.test(String(text || "")) }
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

if (typeof module !== "undefined") module.exports = { byline: byline, people: people, linkUrl: linkUrl, lineLimit: lineLimit, inline: inline, quickAction: quickAction, moveNote: moveNote, descriptionLimit: descriptionLimit, clipped: clipped, markdown: markdown }
