// Access level and the view-only / read-only token hints. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { Core = m.Core; }
function has(list, name) { return Core.has(list, name) }

// Write access per project (the view-only hint, AccessHint.qml). An entry
// comes from board-fetch access ({ level, scopes }) or from a refused write.
// GitLab roles: 0 none, 5 Minimal, 10 Guest, 15 Planner, 20 Reporter, 30
// Developer; labels and closing need Planner or more.
var plannerLevel = 15
function accessEntry(raw) {
  var d = null
  try { d = JSON.parse(String(raw || "")) } catch (error) { d = null }
  if (!d || d.state !== "ready" || typeof d.level !== "number") return { known: false, level: -1, scopes: null, refused: "" }
  return { known: true, level: d.level, scopes: Array.isArray(d.scopes) ? d.scopes.map(String) : null, refused: "" }
}
// A write's error: "scope" (the token has no api scope), "forbidden" (403), or "".
function writeRefusal(message) {
  var m = String(message || "")
  return /insufficient_scope/i.test(m) ? "scope" : /\b403\b|forbidden/i.test(m) ? "forbidden" : ""
}
function refusedEntry(entry, kind) { return Object.assign({ known: false, level: -1, scopes: null }, entry || {}, { refused: kind }) }
// "" (writes on), "read-token" (glab's token can't write), "view-only" (below
// Planner on this project, or GitLab refused a change with 403).
function accessNote(entry) {
  if (!entry) return ""
  if (entry.refused === "scope" || (Array.isArray(entry.scopes) && entry.scopes.indexOf("api") === -1)) return "read-token"
  if ((entry.known && entry.level < plannerLevel) || entry.refused === "forbidden") return "view-only"
  return ""
}
// The hint's words: { title, body, link } (link: show the token page button).
function accessHint(note, entry, project, host) {
  var login = "glab auth login --hostname " + host
  if (note === "read-token") return { link: false,
    title: "Signed in with a read-only token, so moves, labels and close are off.",
    body: "glab's token has no api scope. To change cards, run " + login + " in a terminal with a token that has api." }
  var why = entry && entry.known && entry.level < plannerLevel
    ? (entry.level <= 0 ? "you're not a member" : entry.level < 10 ? "you have Minimal access" : "you're a Guest")
    : "GitLab refused a change (403)"
  return { link: true,
    title: "View-only on " + project + ": " + why + ", so moves, labels and close are off here.",
    body: "Your glab sign-in can change anything your account can. If you only read boards, a token that can only read is safer: "
      + "create one with just the read_api scope, then run " + login + " in a terminal and paste it there, never anywhere else. "
      + "glab in your terminal becomes read-only too, for every project." }
}
// Settings > Account: what glab's token may do, from the scopes board-fetch
// access already read (personal_access_tokens/self: the token's record, never
// its value). "" until the entry is known; no scopes (a browser/OAuth sign-in,
// or GitLab refused the lookup): can't be read.
function accessLine(entry) {
  if (!entry || !entry.known) return ""
  var s = entry.scopes
  if (!Array.isArray(s) || s.length === 0) return "Access: can't be read for this sign-in (browser sign-in, not a token)."
  var t = "Access: " + s.join(", ")
  if (s.indexOf("api") !== -1) return t + " \u00b7 read and write. Only moving cards, labels and comments need api; read_api is enough to look."
  if (s.indexOf("read_api") !== -1) return t + " \u00b7 read only. Moving cards, labels and comments need api."
  return t
}
// GitLab's own token page, prefilled (docs: Prefill personal access token
// details): a name and the read_api scope. Never a token.
function patUrl(host) {
  return "https://" + host + "/-/user_settings/personal_access_tokens?name=GitLab+board&description=Read-only+token+for+the+Omarchy+GitLab+board&scopes=read_api"
}

if (typeof module !== "undefined") module.exports = { plannerLevel: plannerLevel, accessEntry: accessEntry, writeRefusal: writeRefusal, refusedEntry: refusedEntry, accessNote: accessNote, accessHint: accessHint, accessLine: accessLine, patUrl: patUrl }
