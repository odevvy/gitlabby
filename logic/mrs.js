// The Merge requests view (board-fetch mrs). Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { Core = m.Core; }
function httpsUrl(url) { return Core.httpsUrl(url) }

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

if (typeof module !== "undefined") module.exports = { mrsAnswer: mrsAnswer, reviewerStates: reviewerStates, mrPerson: mrPerson, mrRows: mrRows, mrStatuses: mrStatuses, toneColors: toneColors, mrStatus: mrStatus, reviewerMarks: reviewerMarks, reviewerMark: reviewerMark, mrSubline: mrSubline, mrBadge: mrBadge, mrsArgs: mrsArgs }
