// Small shared helpers: settings lists, JSON copies, escaping, ages, safe links. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

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
// Settings > Bots edits settings.bots as saved (not botsConfig's cleaned
// copy), so unknown keys, workingLists and other projects survive. Each edit
// returns the whole new map for Board.saveBots.
function plain(v) { return !!v && typeof v === "object" && !Array.isArray(v) }
function copied(raw) { return plain(raw) ? JSON.parse(JSON.stringify(raw)) : {} }
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
// The one check before a link opens or rides in a notification: https, one
// word, no quote or angle bracket that could end an attribute.
function httpsUrl(url) { return /^https:\/\/[^\s"<>\\]+$/.test(String(url || "")) && urlHost(url) !== "" ? String(url) : "" }
// Extract a DNS hostname with an optional valid port (self-hosted GitLab).
// Reject userinfo, encoded hostnames, backslashes and ambiguous authorities.
function urlHost(url) {
  var m = /^https?:\/\/([^/?#:]+)(?::([0-9]{1,5}))?(?:[/?#]|$)/.exec(String(url || ""))
  return m && (!m[2] || (Number(m[2]) > 0 && Number(m[2]) <= 65535)) ? serverHost(m[1]) : ""
}
function gitlabUrl(url, host) {
  var link = httpsUrl(url), allowed = serverHost(host)
  return link !== "" && allowed !== "" && urlHost(link) === allowed ? link : ""
}
// 2000000 -> "2,000,000": a comment's full length on its trimmed line.
function thousands(n) { return String(Math.floor(Number(n) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ",") }
function oneLine(text, max) {
  var t = String(text || "").replace(/\s+/g, " ").trim()
  return t.length > max ? t.slice(0, max - 1) + "…" : t
}
// The GitLab server setting, as glab's --hostname takes it: a bare name, any
// case, with https:// and a trailing / dropped. "" when it is not one: http,
// a port or a path (those belong in glab's own config for the host).
// The sign-in command (Setup's Sign in runs it in a shell: Omarchy's terminal
// wrapper is bash -c): the host only after the same check as serverHost, and
// only letters, digits, dots and dashes, so nothing in it can reach the shell.
function signInCommand(host) {
  var h = serverHost(host)
  return h !== "" && h !== "gitlab.com" && /^[a-z0-9.-]+$/.test(h) ? "glab auth login --hostname " + h : "glab auth login"
}
function serverHost(raw) {
  var h = String(raw === undefined || raw === null ? "" : raw).trim().toLowerCase()
  if (h.indexOf("https://") === 0) h = h.slice(8)
  h = h.replace(/\/+$/, "")
  var label = "[a-z0-9]([a-z0-9-]*[a-z0-9])?"
  return h.length <= 253 && new RegExp("^" + label + "(\\." + label + ")*$").test(h) ? h : ""
}
// The key a project's own settings (bots, alerts, confirm moves, column
// state) are saved under: gitlab.com's stay as the bare path, as before; on
// another server, its name and a colon first (a name never has a colon).
function serverKey(host, project) {
  return !host || host === "gitlab.com" ? project : host + ":" + project
}

if (typeof module !== "undefined") module.exports = { plainJson: plainJson, lowerList: lowerList, has: has, toggled: toggled, countLabel: countLabel, escaped: escaped, plain: plain, copied: copied, age: age, savedNote: savedNote, httpsUrl: httpsUrl, gitlabUrl: gitlabUrl, oneLine: oneLine, thousands: thousands, serverHost: serverHost, serverKey: serverKey, signInCommand: signInCommand }
