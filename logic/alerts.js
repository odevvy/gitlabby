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

// Desktop alerts (settings.alerts, keyed by project like bots): { review, idle, pipeline }.
function alertsFor(raw, project) {
  var e = raw && typeof raw === "object" && !Array.isArray(raw) ? raw[project] : null
  return { review: !!(e && e.review === true), idle: !!(e && e.idle === true), pipeline: !!(e && e.pipeline === true) }
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
// The board on its server (host: a bare name, gitlab.com when not one).
function boardUrl(data, host) {
  var p = String(data && data.project || "")
  if (!/^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)+$/.test(p)) return ""
  var id = data.board && /^[0-9]+$/.test(String(data.board.id)) ? "/-/boards/" + data.board.id : "/-/boards"
  return "https://" + (Core.serverHost(host) || "gitlab.com") + "/" + p + id
}
// What changed from one good answer to the next, as notifications:
// [{ headline, body (plain), url }]. opts: { review, idle, bots (settings.bots),
// ignore (iids this user just moved), host (the server; gitlab.com if none) }. Several cards entering review make one.
function alertEvents(prev, next, opts) {
  var out = []
  if (!prev || !next || prev.state !== "ready" || next.state !== "ready" || prev.project !== next.project) return out
  var project = String(next.project), host = Core.serverHost(opts.host) || "gitlab.com"
  if (opts.review) {
    var before = reviewRows(prev), now = reviewRows(next), ignore = opts.ignore || []
    var came = Object.keys(now).filter(function(iid) { return !before[iid] && ignore.indexOf(Number(iid)) === -1 && ignore.indexOf(String(iid)) === -1 })
      .map(function(iid) { return now[iid] })
    if (came.length === 1) {
      var r = came[0]
      out.push({ headline: "#" + r.iid + " is in review", body: "#" + r.iid + " " + oneLine(r.title, 80) + " · " + project, url: httpsUrl(r.url) || boardUrl(next, host) })
    } else if (came.length > 1) {
      var shown = came.slice(0, 3).map(function(r) { return "#" + r.iid + " " + oneLine(r.title, 40) })
      out.push({ headline: came.length + " cards entered review", body: shown.join(", ") + (came.length > 3 ? " +" + (came.length - 3) + " more" : "") + " · " + project, url: boardUrl(next, host) })
    }
  }
  if (opts.idle) {
    var cfg = botsConfig(opts.bots, Core.serverKey(host, project))
    var was = botStates(cfg, prev.columns), is = botStates(cfg, next.columns)
    var stopped = is.filter(function(b, i) { return was[i] && was[i].state === "working" && b.state !== "working" })
    if (stopped.length > 0)
      out.push({ headline: "Stopped working: " + stopped.map(function(b) { return oneLine(b.name, 30) }).join(", "),
                 body: "On " + project + ": " + stopped.map(function(b) { return oneLine(b.name, 30) + (b.state === "waiting" ? " is waiting in " + b.column : " has no cards left") }).join("; "),
                 url: boardUrl(next, host) })
  }
  return out
}
// The pipeline alert (v0.1.76): board-fetch pipes, your own open merge
// requests in one project with their head pipelines. Its arguments, or null
// for a project path or id board-fetch would refuse.
function pipesArgs(project) {
  var p = String(project || "")
  return (/^[A-Za-z0-9][A-Za-z0-9_.-]*(\/[A-Za-z0-9_.-]+)+$/.test(p) && p.indexOf("..") === -1) || /^[1-9][0-9]*$/.test(p) ? ["pipes", "--project", p] : null
}
// Its answer, checked: { state, message, project, mrs: [{ iid, title, url, pipeline: { status, url, id } or null }] }.
var pipeStates = ["passed", "failed", "running", "pending", "canceled"]
function pipesAnswer(raw) {
  var data = null
  try { data = JSON.parse(String(raw || "")) } catch (error) {}
  if (!data || typeof data !== "object" || Array.isArray(data)) return { state: "error", message: "GitLab returned an unreadable response.", project: "", mrs: [] }
  var state = String(data.state || "error")
  if (state !== "ready" || !Array.isArray(data.mrs)) return { state: state === "ready" ? "error" : state, message: String(data.message || ""), project: "", mrs: [] }
  var mrs = data.mrs.filter(function(m) { return m && typeof m === "object" && /^[1-9][0-9]*$/.test(String(m.iid)) }).map(function(m) {
    var p = m.pipeline && typeof m.pipeline === "object" && pipeStates.indexOf(String(m.pipeline.status)) !== -1 ? m.pipeline : null
    return { iid: Number(m.iid), title: String(m.title || ""), url: httpsUrl(m.url),
      pipeline: p ? { status: String(p.status), url: httpsUrl(p.url), id: typeof p.id === "string" ? p.id : "" } : null }
  })
  return { state: "ready", message: "", project: String(data.project || ""), mrs: mrs }
}
// The project's merge requests on its server, or "" for a path that isn't one.
function mrListUrl(project, host) {
  var p = String(project || "")
  if (!/^[A-Za-z0-9_.-]+(\/[A-Za-z0-9_.-]+)+$/.test(p)) return ""
  return "https://" + (Core.serverHost(host) || "gitlab.com") + "/" + p + "/-/merge_requests"
}
// What finished between two good pipes answers, as notifications. An MR's
// head pipeline ended (passed or failed) if it was running or pending at the
// last look, or if it is another pipeline (its id) than the last look's; an MR
// that wasn't there last time, or canceled, says nothing. opts: { host }.
// The last alert, for the bar icon's tip and Settings > Alerts (v0.1.111):
// "Last alert: #42 in review · 14:26" from the notification's headline and
// the time it was sent (hhmm, already formatted); "" before the first one.
function lastAlertText(last, hhmm) {
  if (!last || !last.text) return ""
  return "Last alert: " + String(last.text).replace(/ is in review$/, " in review") + " · " + hhmm
}
// Settings > Alerts, under the boxes: the background pace, then the last alert.
function alertStatusText(paceText, last, hhmm) {
  return "Checking every " + paceText + ". " + (lastAlertText(last, hhmm) || "No alerts since the shell started.")
}
function pipelineEvents(prev, next, opts) {
  var out = []
  if (!prev || !next || prev.state !== "ready" || next.state !== "ready" || prev.project !== next.project) return out
  var project = String(next.project), host = Core.serverHost(opts && opts.host) || "gitlab.com", before = {}
  ;(prev.mrs || []).forEach(function(m) { before[m.iid] = m })
  var ended = (next.mrs || []).filter(function(m) {
    var p = m.pipeline, was = before[m.iid]
    if (!was || !p || (p.status !== "passed" && p.status !== "failed")) return false
    var q = was.pipeline
    if (q && (q.status === "running" || q.status === "pending")) return true
    return p.id !== "" && (!q || (q.id !== "" && q.id !== p.id))
  })
  if (ended.length === 1) {
    var m = ended[0]
    out.push({ headline: "Pipeline " + m.pipeline.status + " on !" + m.iid, body: "!" + m.iid + " " + oneLine(m.title, 80) + " · " + project, url: httpsUrl(m.url) || mrListUrl(project, host) })
  } else if (ended.length > 1) {
    var shown = ended.slice(0, 3).map(function(x) { return "!" + x.iid + " " + x.pipeline.status })
    out.push({ headline: ended.length + " pipelines finished", body: shown.join(", ") + (ended.length > 3 ? " +" + (ended.length - 3) + " more" : "") + " · " + project, url: mrListUrl(project, host) })
  }
  return out
}
// The command for one notification (bin/omarchy-notification-send in Omarchy
// 4.0.6): options, then the headline (plain text) and the body (StyledText, so
// escaped; it never starts with "-", so it can't be read as an option), and
// --exec last with the click command as separate words. Low urgency under
// our own app name: Do Not Disturb holds it (only critical notify-send passes).
// A click opens the link as the popup's do (Settings > Open links in, links):
// "app" an app window (omarchy-launch-webapp), anything else a browser tab
// (omarchy-launch-browser). https only.
function notifyArgv(ev, links) {
  var argv = ["omarchy-notification-send", "--app-name", "GitLabby", "-u", "low", "-g", "\uf296", oneLine(ev.headline, 120), escaped(oneLine(ev.body, 300))]
  if (httpsUrl(ev.url)) argv = argv.concat(["--exec", links === "app" ? "omarchy-launch-webapp" : "omarchy-launch-browser", ev.url])
  return argv
}

if (typeof module !== "undefined") module.exports = { alertsFor: alertsFor, withAlert: withAlert, reviewRows: reviewRows, boardUrl: boardUrl, alertEvents: alertEvents, notifyArgv: notifyArgv, pipesArgs: pipesArgs, pipesAnswer: pipesAnswer, mrListUrl: mrListUrl, pipelineEvents: pipelineEvents, lastAlertText: lastAlertText, alertStatusText: alertStatusText }
