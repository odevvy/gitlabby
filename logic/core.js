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
function httpsUrl(url) { return /^https:\/\/[^\s"<>]+$/.test(String(url || "")) ? String(url) : "" }
function oneLine(text, max) {
  var t = String(text || "").replace(/\s+/g, " ").trim()
  return t.length > max ? t.slice(0, max - 1) + "…" : t
}

if (typeof module !== "undefined") module.exports = { plainJson: plainJson, lowerList: lowerList, has: has, toggled: toggled, countLabel: countLabel, escaped: escaped, plain: plain, copied: copied, age: age, savedNote: savedNote, httpsUrl: httpsUrl, oneLine: oneLine }
