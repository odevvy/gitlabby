// Desktop alerts: settings, what changed between two board answers, notify-send arguments. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js, bots.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
var Bots = typeof module !== "undefined" ? require("./bots.js") : null
function use(m) { Core = m.Core; Bots = m.Bots; }
function plainJson(value) { return Core.plainJson(value) }
function has(list, name) { return Core.has(list, name) }
function httpsUrl(url) { return Core.httpsUrl(url) }
function oneLine(text, max) { return Core.oneLine(text, max) }
function escaped(text) { return Core.escaped(text) }
function botsConfig(all, project) { return Bots.botsConfig(all, project) }
function botStates(config, columns) { return Bots.botStates(config, columns) }

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
function boardUrl(data) {
  var p = String(data && data.project || "")
  if (!/^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)+$/.test(p)) return ""
  var id = data.board && /^[0-9]+$/.test(String(data.board.id)) ? "/-/boards/" + data.board.id : "/-/boards"
  return "https://gitlab.com/" + p + id
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

if (typeof module !== "undefined") module.exports = { alertsFor: alertsFor, withAlert: withAlert, reviewRows: reviewRows, boardUrl: boardUrl, alertEvents: alertEvents, notifyArgv: notifyArgv }
