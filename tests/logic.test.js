// Unit tests for Logic.js, the board's Qt-free logic. Run: node --test tests/logic.test.js
"use strict"
const test = require("node:test")
const assert = require("node:assert/strict")
const L = require("../Logic.js")

test("settings lists are lowercase names from an array or a comma string", () => {
  assert.deepEqual(L.lowerList("Closed, Research ,,"), ["closed", "research"])
  assert.deepEqual(L.lowerList([" Open", "TODO"]), ["open", "todo"])
  assert.deepEqual(L.lowerList(null), [])
  assert.ok(L.has(["research"], "Research"))
  assert.ok(!L.has(undefined, "open"))
  assert.deepEqual(L.toggled(["open"], "Closed"), ["open", "closed"])
  assert.deepEqual(L.toggled(["open", "closed"], "OPEN"), ["closed"])
})

test("escaped makes text safe for StyledText and RichText", () => {
  assert.equal(L.escaped("<b>a & b</b>"), "&lt;b&gt;a &amp; b&lt;/b&gt;")
})

test("column counts: 20+ only for a capped column", () => {
  const n = k => Array.from({ length: k }, (_, i) => ({ iid: i + 1 }))
  assert.equal(L.countLabel({ name: "Closed", issues: n(20), capped: true }), "20+")
  assert.equal(L.countLabel({ name: "Closed", issues: n(20) }), "20")
  assert.equal(L.countLabel({ name: "todo", issues: n(3), capped: false }), "3")
  assert.equal(L.countLabel({ name: "Open" }), "0")
})

test("label colors: own text color wins, else dark on light and white on dark", () => {
  assert.equal(L.labelStyle(undefined), null)
  assert.equal(L.labelStyle({ color: null }), null)
  assert.deepEqual(L.labelStyle({ color: "#f0f0f0", textColor: null }), { bg: "#f0f0f0", fg: "#1f1e24" })
  assert.deepEqual(L.labelStyle({ color: "#428bca", textColor: null }), { bg: "#428bca", fg: "#ffffff" })
  assert.deepEqual(L.labelStyle({ color: "#ffff00", textColor: "#333333" }), { bg: "#ffff00", fg: "#333333" })
})

test("age labels", () => {
  const now = "2026-10-28T12:00:00Z"
  const ago = (minutes) => new Date(Date.parse(now) - minutes * 60000).toISOString()
  const day = 24 * 60
  const cases = [[0, "0m"], [59, "59m"], [60, "1h"], [day - 1, "23h"], [day, "1d"], [13 * day, "13d"], [14 * day, "2w"],
    [59 * day, "8w"], [60 * day, "2mo"], [364 * day, "12mo"], [365 * day, "1y"], [800 * day, "2y"]]
  for (const [minutes, label] of cases) assert.equal(L.age(ago(minutes), now), label, minutes + " minutes")
  assert.equal(L.age("", now), "")
  assert.equal(L.age(null, now), "")
  assert.equal(L.age("2026-10-28T13:00:00Z", now), "", "in the future")
  assert.match(L.age(new Date(Date.now() - 3 * 3600000).toISOString()), /^[23]h$/, "defaults to now")
})

const open = { name: "Open", kind: "open", issues: [] }
const todo = { name: "todo", kind: "label", listId: 2, issues: [] }
const doing = { name: "doing", kind: "label", listId: 3, issues: [] }
const closed = { name: "Closed", kind: "closed", issues: [] }
const board = (cols) => [open, todo, doing, closed].map((c) => Object.assign({}, c, { issues: cols[c.name] || [] }))
const ids = (columns) => Object.fromEntries(columns.map((c) => [c.name, c.issues.map((i) => i.iid)]))
const row = (iid, labels) => ({ iid, title: "#" + iid, labels })

test("saved board note: how old the copy is, then updating", () => {
  const now = "2026-10-28T12:00:00Z"
  assert.equal(L.savedNote("2026-10-28T09:00:00Z", now), "Saved 3h ago · updating…")
  assert.equal(L.savedNote("2026-10-28T11:59:30Z", now), "Saved just now · updating…")
  assert.equal(L.savedNote("2026-10-28T12:05:00Z", now), "Saved just now · updating…", "clock skew")
  assert.equal(L.savedNote("", now), "Saved just now · updating…")
})

test("move between label lists swaps the label and puts the card on top", () => {
  const columns = board({ todo: [row(1, ["todo", "bug"]), row(2, ["todo"])], doing: [row(3, ["doing"])] })
  const after = L.movedColumns(columns, columns[1].issues[0], todo, doing)
  assert.deepEqual(ids(after), { Open: [], todo: [2], doing: [1, 3], Closed: [] })
  assert.deepEqual(after[2].issues[0].labels, ["bug", "doing"])
  assert.deepEqual(columns[1].issues[0].labels, ["todo", "bug"], "input left as it was")
})

test("closing keeps the labels and takes the card out of every other list", () => {
  const card = row(1, ["todo", "doing"])
  const columns = board({ todo: [card], doing: [card] })
  const after = L.movedColumns(columns, card, todo, closed)
  assert.deepEqual(ids(after), { Open: [], todo: [], doing: [], Closed: [1] })
  assert.deepEqual(after[3].issues[0].labels, ["todo", "doing"])
})

test("an issue in two lists stays in the other one, with its new labels", () => {
  const card = row(1, ["todo", "doing"])
  const columns = board({ todo: [card], doing: [card] })
  const after = L.movedColumns(columns, card, todo, open)
  assert.deepEqual(ids(after), { Open: [1], todo: [], doing: [1], Closed: [] })
  assert.deepEqual(after[2].issues[0].labels, ["doing"])
})

test("reopening from Closed into a label list adds that label", () => {
  const columns = board({ Closed: [row(4, [])] })
  const after = L.movedColumns(columns, columns[3].issues[0], closed, todo)
  assert.deepEqual(ids(after), { Open: [], todo: [4], doing: [], Closed: [] })
  assert.deepEqual(after[1].issues[0].labels, ["todo"])
})

test("column keys and the list argument for board-fetch move", () => {
  assert.equal(L.columnKey(todo), "label:2")
  assert.equal(L.columnKey(open), "open:Open")
  assert.equal(L.listSpec(todo), "2")
  assert.equal(L.listSpec(closed), "closed")
})

test("byline and people lines", () => {
  const now = "2026-10-28T12:00:00Z"
  assert.equal(L.byline({ createdAt: "2026-10-28T11:40:00Z" }, now), "created 20m ago")
  assert.equal(L.byline({ author: "o_devvy", createdAt: "2026-10-28T09:00:00Z", updatedAt: "2026-10-28T11:55:00Z" }, now),
    "o_devvy · created 3h ago · updated 5m ago")
  assert.equal(L.people({}), "")
  assert.equal(L.people({ assignees: ["dee", "o_devvy"], milestone: "v1.2" }), "assigned dee, o_devvy · milestone v1.2")
  assert.equal(L.people({ assignees: [{ username: "dee" }] }), "assigned dee")
})

test("links: https as is, GitLab-relative on the issue's host, nothing else", () => {
  const issueUrl = "https://gitlab.com/group/app/-/issues/5"
  assert.equal(L.linkUrl("/group/app/-/issues/6", issueUrl), "https://gitlab.com/group/app/-/issues/6")
  assert.equal(L.linkUrl("https://example.com/x", issueUrl), "https://example.com/x")
  for (const bad of ["javascript:alert(1)", "file:///etc/passwd", "http://example.com/x", "--gpu-launcher=x", "vscode://x"])
    assert.equal(L.linkUrl(bad, issueUrl), "", bad)
  assert.equal(L.linkUrl("/relative", ""), "")
  assert.equal(L.linkUrl("/relative", "http://gitlab.com/a"), "", "no http host for relative links either")
})

const md = (text) => L.markdown(text, (t) => t.length * 7, (px) => px)

test("markdown: raw HTML is text, images are links, hrefs can't break out", () => {
  const x = md("<script>alert(1)</script> <img src=https://evil.example/x.png> ![pic](https://evil.example/p.png)")
  assert.ok(!x.includes("<script") && !x.includes("<img") && x.includes("&lt;img"))
  assert.ok(x.includes('<a href="https://evil.example/p.png">pic</a>'))
  assert.ok(!md('[a](https://x.example/"onmouseover=1)').includes('href="https://x.example/"onmouseover'))
})

test("markdown: long descriptions are cut at a line break, long lines stay plain", () => {
  const para = "word ".repeat(19) + "ends\n"  // 100 characters
  const x = md(para.repeat(300))
  assert.equal(x, md(para.repeat(L.descriptionLimit / 100)), "cut after the last whole line under the limit")
  assert.equal(md("a".repeat(L.descriptionLimit + 5)).length, md("a".repeat(L.descriptionLimit)).length, "no line break: cut at the limit")
  assert.equal(L.inline("**b** ".repeat(500)), "**b** ".repeat(500), "a line over lineLimit gets no markup")
  assert.equal(L.inline("x".repeat(L.lineLimit) + " **b**"), "x".repeat(L.lineLimit) + " **b**")
  assert.ok(L.inline("x".repeat(L.lineLimit - 6) + " **b**").endsWith("<b>b</b>"))
  assert.equal(L.inline("<b>".repeat(1000)), "&lt;b&gt;".repeat(1000), "still escaped")
})

test("markdown: hostile descriptions render fast", () => {
  const fast = (name, text) => {
    const start = process.hrtime.bigint(); md(text)
    const ms = Number(process.hrtime.bigint() - start) / 1e6
    assert.ok(ms < 100, name + ": " + ms.toFixed(1) + " ms")
  }
  fast("120 KB of *a", "*a" + " *a".repeat(40000))
  fast("20 KB of [", "[".repeat(20000))
  fast("1 MB of *a", "*a" + " *a".repeat(340000))
  const line = (unit) => unit.repeat(Math.ceil(L.lineLimit / unit.length)).slice(0, L.lineLimit)
  for (const unit of ["[](", "[a](" + "b".repeat(60), " *a", "[", "![", "\\*_a"])
    fast("lines of " + unit.slice(0, 8) + " under both limits", Array(10).fill(line(unit)).join("\n"))
})

test("markdown: link text has no [, a title follows the URL", () => {
  assert.equal(L.inline("[a [b](https://x)"), '[a <a href="https://x">b</a>')
  assert.equal(L.inline('[t](https://x "T")'), '<a href="https://x">t</a>')
  assert.equal(L.inline("[t](https://x)y)"), '<a href="https://x">t</a>y)')
})

test("markdown: code, inline styles and bare links", () => {
  const x = md("```\n<b>code</b>\n  indented\n```\nafter **bold** _it_ ~~gone~~ `a_b` parse_prefs_body https://gitlab.com/a?b=1&c=2")
  assert.ok(x.includes("<pre>&lt;b&gt;code&lt;/b&gt;\n  indented</pre>"))
  assert.ok(x.includes("<b>bold</b>") && x.includes("<i>it</i>") && x.includes("<s>gone</s>"))
  assert.ok(x.includes("<code>&nbsp;a_b&nbsp;</code>") && x.includes("parse_prefs_body"))
  assert.ok(x.includes('<a href="https://gitlab.com/a?b=1&amp;c=2">'))
  assert.equal(md("```\nx"), "<pre>x</pre>", "an unterminated fence still closes")
})

test("markdown: headings, line breaks, lists, tables, quotes, rules", () => {
  assert.equal(md("## Goal\nline one\nline two"), "<p class='h2'>Goal</p><p>line one<br>line two</p>")
  assert.equal(md("#### Deep"), "<p class='h3'>Deep</p>")
  assert.equal(md("- item"), "<p class='li' style='margin-left: 14px; text-indent: -14px'>• item</p>")
  assert.ok(md("  - nested").includes("margin-left: 28px"), "one level in by the width of two spaces")
  const x = md("| a | b |\n|---|---|\n| 1 | 2 |\n\n1. one\n   - [x] done\n> quoted\n---")
  assert.ok(x.includes("<th>a</th><th>b</th>") && x.includes("<td>1</td><td>2</td>"))
  assert.ok(x.includes("1. one") && x.includes("☑ done") && x.includes("class='quote'") && x.includes("<hr>"))
})

test("keyboard cursor: moves skip collapsed and empty columns, clamp at the edges", () => {
  const lanes = [[1, 2, 3], null, [], [4], [5, 6]]
  const at = (col, row) => ({ col, row, iid: lanes[col][row] })
  assert.deepEqual(L.cursorMove(lanes, at(0, 0), 0, 1), at(0, 1))
  assert.deepEqual(L.cursorMove(lanes, at(0, 2), 0, 1), at(0, 2))
  assert.deepEqual(L.cursorMove(lanes, at(0, 0), 0, -1), at(0, 0))
  assert.deepEqual(L.cursorMove(lanes, at(0, 2), 1, 0), at(3, 0))  // over the strip and the empty column; row clamps
  assert.deepEqual(L.cursorMove(lanes, at(3, 0), 1, 0), at(4, 0))
  assert.deepEqual(L.cursorMove(lanes, at(4, 1), 1, 0), at(4, 1))
  assert.deepEqual(L.cursorMove(lanes, at(4, 1), -1, 0), at(3, 0))
  assert.deepEqual(L.cursorMove(lanes, at(0, 1), -1, 0), at(0, 1))
  assert.equal(L.cursorMove([null, []], { col: 0, row: 0 }, 1, 0), null)
})

test("keyboard cursor after a refresh: same issue if shown, else nearest card", () => {
  assert.deepEqual(L.cursorFix([[1], [7, 2]], { col: 0, row: 0, iid: 2 }), { col: 1, row: 1, iid: 2 })
  assert.deepEqual(L.cursorFix([[2], [2]], { col: 1, row: 0, iid: 2 }), { col: 1, row: 0, iid: 2 })  // in two lists: keeps its column
  assert.deepEqual(L.cursorFix([[1, 3], [4]], { col: 0, row: 5, iid: 9 }), { col: 0, row: 1, iid: 3 })
  assert.deepEqual(L.cursorFix([[1], null, [5]], { col: 1, row: 0, iid: 9 }), { col: 0, row: 0, iid: 1 })
  assert.deepEqual(L.cursorFix([[1]], { col: 4, row: 0 }), { col: 0, row: 0, iid: 1 })  // columns hidden
  assert.equal(L.cursorFix([], { col: 0, row: 0 }), null)
})

test("the README's Keyboard section lists exactly the keys the popup shows, group by group", () => {
  const readme = require("node:fs").readFileSync(require("node:path").join(__dirname, "..", "README.md"), "utf8")
  const section = readme.split("\n## Keyboard\n")[1].split("\n## ")[0]
  const groups = []
  section.split("\n").forEach(l => {
    const title = /^\*\*(.+)\*\*$/.exec(l)
    if (title) groups.push({ title: title[1], rows: [] })
    else if (/^\| (?!Key |---)/.test(l)) groups[groups.length - 1].rows.push(l.replace(/`/g, ""))
  })
  assert.deepEqual(groups, L.keyGroups.map(g => ({ title: g.title, rows: g.keys.map(([k, a]) => "| " + k + " | " + a + " |") })))
})

test("the key groups: every view's keys, the setup panel's, no key twice in a group", () => {
  const group = title => (L.keyGroups.find(g => g.title === title) || { keys: [] }).keys
  const action = (title, key) => (group(title).find(([k]) => k === key) || [])[1] || ""
  assert.deepEqual(L.keyGroups.map(g => g.title), ["Board", "Confirm a move or a close", "Anywhere", "Issue", "Merge requests", "Comment box", "Pickers and filters", "Setup panel"])
  assert.match(action("Setup panel", "Enter or Space"), /main button/)
  assert.match(action("Setup panel", "r"), /Try again/)
  assert.match(action("Anywhere", "?"), /keyboard button in the header/)
  for (const k of ["o", "c", "e", "x"]) assert.ok(action("Issue", k), k)
  assert.match(action("Anywhere", "m"), /Merge requests/)
  for (const k of ["j k or ↓ ↑", "Enter or o", "r"]) assert.ok(action("Merge requests", k), k)
  for (const g of L.keyGroups) assert.equal(new Set(g.keys.map(([k]) => k)).size, g.keys.length, g.title)
})

test("keycaps: words are caps, or is said, + joins a chord", () => {
  assert.deepEqual(L.keyParts("Shift+H or Shift+L"), [{ cap: "Shift" }, { text: "+" }, { cap: "H" }, { text: "or" }, { cap: "Shift" }, { text: "+" }, { cap: "L" }])
  assert.deepEqual(L.keyParts("h j k l"), [{ cap: "h" }, { cap: "j" }, { cap: "k" }, { cap: "l" }])
  assert.deepEqual(L.keyParts("?"), [{ cap: "?" }])
  assert.deepEqual(L.keyParts("Ctrl+Enter"), [{ cap: "Ctrl" }, { text: "+" }, { cap: "Enter" }])
})

test("label editor: status labels are never editable or offered", () => {
  const columns = [{ name: "Open", kind: "open" }, { name: "Doing", kind: "label", listId: 4 }, { name: "Closed", kind: "closed" }, { name: "alice", kind: "other" }]
  const status = L.statusLabels(["Ready"], columns)
  assert.deepEqual(status.slice().sort(), ["approved", "doing", "in progress", "ready", "research", "review", "todo"])
  const all = [{ name: "api" }, { name: "bug" }, { name: "Doing" }, { name: "Todo" }, { name: "ux" }, { name: "Bugfix" }]
  assert.deepEqual(L.addableLabels(all, ["bug"], status, "").map(l => l.name), ["api", "ux", "Bugfix"])
  assert.deepEqual(L.addableLabels(all, ["bug"], status, " BUG ").map(l => l.name), ["Bugfix"])
  assert.deepEqual(L.addableLabels(all, [], status, "do").map(l => l.name), [])
})

test("label editor: colors from the labels list fill gaps, the board's win", () => {
  const base = { bug: { color: "#ff0000" } }
  const out = L.withColors(base, [{ name: "bug", color: "#000000" }, { name: "ux", color: "#00ff00", textColor: "#000000" }, { name: "api", color: null }])
  assert.deepEqual(out, { bug: { color: "#ff0000" }, ux: { color: "#00ff00", textColor: "#000000" } })
  assert.deepEqual(base, { bug: { color: "#ff0000" } })
})

test("closing: the status labels an issue keeps, in its order, any case", () => {
  const status = L.statusLabels([], [{ name: "Doing", kind: "label", listId: 3 }])
  assert.deepEqual(L.statusOn(["app-ui", "Review", "doing", "bug"], status), ["Review", "doing"])
  assert.deepEqual(L.statusOn(["bug"], status), [])
  assert.deepEqual(L.statusOn(undefined, status), [])
})

const P41 = { "group/p41": { busyLists: ["approved", "in progress", "review"], bots: [
  { name: "App UI", label: "app-ui" }, { name: "API Engineer", label: "api" }, { name: "Auth & Mail", label: "auth-mail" },
  { name: "Product Lead", label: "" }, { name: "Spec QA", list: "review" }] } }
const card = (iid, labels) => ({ iid, title: "t" + iid, labels })
const BOT_COLUMNS = [
  { name: "Open", kind: "open", issues: [card(1, ["app-ui"]), card(2, [])] },
  { name: "todo", kind: "label", issues: [card(3, ["todo", "auth-mail"]), card(4, ["todo"])] },
  { name: "Approved", kind: "label", issues: [card(5, ["Approved", "APP-UI"])] },
  { name: "in progress", kind: "label", issues: [card(6, ["in progress", "app-ui"]), card(7, ["in progress"]), card(8, ["in progress", "api", "auth-mail"])] },
  { name: "review", kind: "label", issues: [card(9, ["review", "api"]), card(10, ["review", "docs"])] },
  { name: "In Progress", kind: "other", issues: [card(11, ["app-ui", "in progress"])] },
  { name: "review", kind: "other", issues: [card(14, ["review"])] },
  { name: "Closed", kind: "closed", issues: [card(12, ["auth-mail", "in progress"]), card(13, ["review", "api"])] }]
const view = states => Object.fromEntries(states.map(s => [s.name, s.state + " " + s.issues.map(i => "#" + i.iid + ":" + i.list).join(",")]))

test("bots: busy rules (owner labels, no owner, two owners, Spec QA's list, any case)", () => {
  assert.deepEqual(view(L.botStates(L.botsConfig(P41, "group/p41"), BOT_COLUMNS)), {
    "App UI": "working #5:Approved,#6:in progress",
    "API Engineer": "working #8:in progress,#9:review",
    "Auth & Mail": "working #8:in progress",
    "Product Lead": "working #7:in progress,#10:review",
    "Spec QA": "working #9:review,#10:review"
  })
})

test("bots: closed, Open, todo and non-label lists (even with a busy name) never count; waiting vs idle", () => {
  const cols = BOT_COLUMNS.filter(c => c.name !== "in progress")
  assert.deepEqual(view(L.botStates(L.botsConfig(P41, "group/p41"), cols)), {
    "App UI": "waiting #5:Approved",
    "API Engineer": "waiting #9:review",
    "Auth & Mail": "idle ",
    "Product Lead": "waiting #10:review",
    "Spec QA": "working #9:review,#10:review"
  })
  const empty = L.botStates(L.botsConfig(P41, "group/p41"), [{ name: "review", kind: "label", issues: [] }])
  assert.deepEqual(empty.map(s => s.state), ["idle", "idle", "idle", "idle", "idle"])
})

test("bots: an issue in two busy lists counts once, as working if either is", () => {
  const cols = [{ name: "approved", kind: "label", issues: [card(20, ["approved", "in progress", "api"])] },
                { name: "in progress", kind: "label", issues: [card(20, ["approved", "in progress", "api"])] }]
  const api = L.botStates(L.botsConfig(P41, "group/p41"), cols)[1]
  assert.equal(api.state, "working")
  assert.deepEqual(api.issues.map(i => [i.iid, i.list]), [[20, "in progress"]])
})

test("bots: the dot's column is the furthest along of the issues that set the state", () => {
  const col = (name, color, issues) => ({ name, kind: "label", color, issues })
  const cols = [col("todo", "#4f86d6", [card(30, ["todo", "auth-mail"])]), col("approved", "#d4473f", [card(31, ["approved", "auth-mail"])]),
                col("in progress", "#e6cf17", [card(40, ["in progress", "api"]), card(41, ["in progress", "app-ui"])]),
                col("review", "#86c29a", [card(50, ["review", "api"])])]
  const cfg = L.botsConfig({ "a/b": { busyLists: ["todo", "approved", "in progress", "review"], bots: [
    { name: "API Engineer", label: "api" }, { name: "Auth & Mail", label: "auth-mail" }, { name: "App UI", label: "app-ui" },
    { name: "Spec QA", list: "review" }, { name: "Idle", label: "none" }] } }, "a/b")
  const pick = s => [s.state, s.column, s.color, s.oneList]
  const [api, auth, app, qa, idle] = L.botStates(cfg, cols)
  // working in progress, waiting in review: the filled dot wears in progress, not review
  assert.deepEqual(pick(api), ["working", "in progress", "#e6cf17", ""])
  // only waiting: the furthest along of them (approved beats todo)
  assert.deepEqual(pick(auth), ["waiting", "approved", "#d4473f", ""])
  assert.deepEqual(pick(app), ["working", "in progress", "#e6cf17", "in progress"])
  assert.deepEqual(pick(qa), ["working", "review", "#86c29a", "review"])
  assert.deepEqual(pick(idle), ["idle", "", "", ""])
  // a column without a color (no-board fallback without label colors): no color
  assert.equal(L.botStates(cfg, [col("review", undefined, [card(50, ["review", "api"])])])[0].color, "")
})

test("the column said once: in research, in review, but in progress as it is", () => {
  assert.equal(L.inColumn("research"), "in research")
  assert.equal(L.inColumn("In Progress"), "In Progress")
  assert.equal(L.inColumn("inbox"), "in inbox")
})

test("busy dot color: the column's own, unless it is too close to the background", () => {
  const bg = "#132235"
  assert.equal(L.dotColor("#e6cf17", bg), "#e6cf17")
  assert.equal(L.dotColor("#e5e7eb", bg), "#e5e7eb")
  assert.equal(L.dotColor("#1f2a44", bg), "")          // dark blue on dark blue: accent instead
  assert.equal(L.dotColor("#e5e7eb", "#ffffff"), "")   // near-white on a light theme
  assert.equal(L.dotColor("#e6cf17", "#ff132235"), "#e6cf17")  // #aarrggbb background
  assert.equal(L.dotColor("", bg), "")
  assert.equal(L.dotColor(undefined, bg), "")
  assert.equal(L.dotColor("red", bg), "")
})

test("bots: no config, another project, or no usable bot shows nothing", () => {
  assert.equal(L.botsConfig(undefined, "group/p41"), null)
  assert.equal(L.botsConfig({}, "group/p41"), null)
  assert.equal(L.botsConfig(P41, "group/other"), null)
  assert.equal(L.botsConfig({ "a/b": { bots: [] } }, "a/b"), null)
  assert.equal(L.botsConfig({ "a/b": { bots: "x" } }, "a/b"), null)
  assert.equal(L.botsConfig({ "a/b": { bots: [{ name: "" , label: "x" }, { name: "N" }, { name: "Q", list: " " }, null] } }, "a/b"), null)
  assert.deepEqual(L.botStates(null, BOT_COLUMNS), [])
})

test("bots: workingLists can be set; a list bot is working whenever its list has issues, busy list or not", () => {
  const cfg = L.botsConfig({ "a/b": { busyLists: ["Doing", "Check"], workingLists: ["check"], bots: [{ name: "Dev", label: "dev" }, { name: "QA", list: "CHECK" }] } }, "a/b")
  const cols = [{ name: "Doing", kind: "label", issues: [card(1, ["Doing", "DEV"])] }, { name: "Check", kind: "label", issues: [] }]
  assert.deepEqual(L.botStates(cfg, cols).map(s => s.state), ["waiting", "idle"])
  const qa = L.botsConfig({ "a/b": { busyLists: ["Doing"], bots: [{ name: "QA", list: "check" }] } }, "a/b")
  assert.deepEqual(L.botStates(qa, [{ name: "Check", kind: "label", issues: [card(2, [])] }]).map(s => s.state + s.issues.length), ["working1"])
})

test("markdown: a URL inside link text is not linked again; marker characters can't fake a span", () => {
  assert.equal(L.inline("[see https://x.io/a](https://y.io/b)"), '<a href="https://y.io/b">see https://x.io/a</a>')
  assert.equal(L.inline("go https://a.io/x and [t](https://b.io)"), 'go <a href="https://a.io/x">https://a.io/x</a> and <a href="https://b.io">t</a>')
  assert.equal(L.inline("x \x010\x01 \x020\x02 y"), "x 0 0 y")
  assert.equal(L.inline("**[b](https://c.io)**"), '<b><a href="https://c.io">b</a></b>')
})

test("comments: a line starting with / is a quick action; / elsewhere or in backticks is not", () => {
  for (const t of ["/close", "Looks good\n/label ~review", "ok\n  \t/unlabel ~x"]) assert.equal(L.quickAction(t), true, t)
  for (const t of ["", "see a/b and /usr", "`/close`", "path: /etc"]) assert.equal(L.quickAction(t), false, t)
})

test("move confirm: says what the move does on GitLab", () => {
  const open = { kind: "open" }, closed = { kind: "closed" }, a = { kind: "label", name: "a" }, b = { kind: "label", name: "b" }
  assert.equal(L.moveNote(a, b), "This changes its status label on GitLab.")
  assert.equal(L.moveNote(open, a), "This changes its status label on GitLab.")
  assert.equal(L.moveNote(a, open), "This removes its status label on GitLab.")
  assert.equal(L.moveNote(a, closed), "This closes it on GitLab. Its labels stay.")
  assert.equal(L.moveNote(closed, a), "This reopens it on GitLab and changes its status label.")
  assert.equal(L.moveNote(closed, open), "This reopens it on GitLab.")
})

// --- Settings > Bots: edits keep the saved JSON as it was apart from the edit ---
const P41RAW = { "firelink21/phrase41": { busyLists: ["approved", "in progress", "review"], bots: [
  { name: "App UI", label: "app-ui" }, { name: "API Engineer", label: "api" }, { name: "Auth & Mail", label: "auth-mail" },
  { name: "Product Lead", label: "" }, { name: "Spec QA", list: "review" }] }, "other/proj": { bots: [{ name: "X", label: "x" }], workingLists: ["Doing"], note: 1 } }
const P = "firelink21/phrase41"

test("bots editor: reads the saved entry, or says what is wrong with it", () => {
  assert.deepEqual(L.botsEntry(undefined, P), { problem: "", entry: null })
  assert.deepEqual(L.botsEntry({}, P), { problem: "", entry: null })
  assert.equal(L.botsEntry(P41RAW, P).entry, P41RAW[P])
  assert.equal(L.botsEntry(JSON.stringify(P41RAW), P).problem, "setting")  // bar set without --json
  assert.equal(L.botsEntry([P41RAW], P).problem, "setting")
  assert.equal(L.botsEntry(3, P).problem, "setting")
  assert.equal(L.botsEntry({ [P]: "x" }, P).problem, "entry")
  assert.equal(L.botsEntry({ [P]: { bots: "x" } }, P).problem, "entry")
  assert.ok(L.botUsable({ name: "Product Lead", label: "" }) && L.botUsable({ name: "Q", list: "review" }))
  assert.ok(!L.botUsable({ name: " ", label: "x" }) && !L.botUsable({ name: "N" }) && !L.botUsable({ name: "Q", list: " " }) && !L.botUsable(null))
  assert.ok(L.botNameTaken(P41RAW[P], " auth & mail ") && !L.botNameTaken(P41RAW[P], "Auth") && !L.botNameTaken(null, "x"))
})

test("bots editor: add, remove and busy toggles change only their part", () => {
  const before = JSON.stringify(P41RAW)
  const added = L.withBot(P41RAW, P, { name: "Decider", label: "needs-decision" }, ["todo"])
  assert.equal(JSON.stringify(added), before.replace('{"name":"Spec QA","list":"review"}]', '{"name":"Spec QA","list":"review"},{"name":"Decider","label":"needs-decision"}]'))
  assert.equal(JSON.stringify(P41RAW), before)  // never in place
  assert.equal(JSON.stringify(L.withoutBot(added, P, 5)), before)
  assert.equal(JSON.stringify(L.withoutBot(P41RAW, P, 2)), before.replace('{"name":"Auth & Mail","label":"auth-mail"},', ""))
  assert.equal(JSON.stringify(L.withBusy(L.withBusy(P41RAW, P, "todo", true), P, "Todo", false)), before)
  assert.deepEqual(L.withBusy(P41RAW, P, "Review", false)[P].busyLists, ["approved", "in progress"])
  assert.deepEqual(L.withBusy({ [P]: { bots: [] } }, P, "review", true)[P].busyLists, ["review"])
  // The first bot: a new entry with every label column busy; the last one out takes the entry.
  const first = L.withBot({ "other/proj": P41RAW["other/proj"] }, P, { name: "Spec QA", list: "review" }, ["research", "todo", "review"])
  assert.deepEqual(first[P], { busyLists: ["research", "todo", "review"], bots: [{ name: "Spec QA", list: "review" }] })
  assert.deepEqual(L.withoutBot(first, P, 0), { "other/proj": P41RAW["other/proj"] })
  assert.deepEqual(L.withBot(undefined, P, { name: "A", label: "a" }, []), { [P]: { busyLists: [], bots: [{ name: "A", label: "a" }] } })
  // A malformed setting or entry is replaced only by an add; remove and toggles leave it.
  assert.deepEqual(L.withBot("{oops", P, { name: "A", label: "" }, ["review"]), { [P]: { busyLists: ["review"], bots: [{ name: "A", label: "" }] } })
  assert.deepEqual(L.withBot({ [P]: { bots: "x" }, k: 1 }, P, { name: "A", label: "" }, []), { [P]: { busyLists: [], bots: [{ name: "A", label: "" }] }, k: 1 })
  assert.deepEqual(L.withoutBot({ [P]: { bots: "x" } }, P, 0), { [P]: { bots: "x" } })
  assert.deepEqual(L.withBusy({ [P]: "x" }, P, "review", true), { [P]: "x" })
  // Malformed bot rows can be removed like any other.
  assert.deepEqual(L.withoutBot({ [P]: { bots: [{ name: "" }, { name: "A", label: "a" }] } }, P, 0), { [P]: { bots: [{ name: "A", label: "a" }] } })
})

// The plugin's QML files, relative to the plugin dir: the top level and components/.
function qmlFiles() {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const top = fs.readdirSync(dir).filter(f => f.endsWith(".qml"))
  const sub = fs.existsSync(path.join(dir, "components")) ? fs.readdirSync(path.join(dir, "components")).filter(f => f.endsWith(".qml")).map(f => "components/" + f) : []
  return top.concat(sub)
}

test("layout: every plugin type a QML file uses resolves from its own folder or an imported one", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const files = qmlFiles()
  const ours = new Map(files.map(f => [path.basename(f, ".qml"), f]))  // type name -> its file
  assert.ok(ours.has("Board") && ours.has("BoardText") && ours.has("IconTip"), [...ours.keys()].join(" "))
  assert.ok(fs.existsSync(path.join(dir, "Board.qml")), "the manifest's barWidget stays at the top")
  const problems = []
  for (const f of files) {
    const src = fs.readFileSync(path.join(dir, f), "utf8"), here = path.dirname(f)
    const folders = [here].concat([...src.matchAll(/^import "([^"]+)"\s*$/gm)].map(m => path.normalize(path.join(here, m[1]))))
    const inline = new Set([...src.matchAll(/^\s*component (\w+):/gm)].map(m => m[1]))
    for (const m of src.matchAll(/^import "([^"]+\.js)" as \w+/gm))
      if (!fs.existsSync(path.join(dir, here, m[1]))) problems.push(f + ": " + m[1] + " not found")
    for (const m of src.matchAll(/(?:^|[\s:;{])([A-Z]\w*) \{/g)) {
      const name = m[1]
      if (inline.has(name) || !ours.has(name)) continue  // Qt, Quickshell, Omarchy, or this file's own component
      if (!folders.includes(path.dirname(ours.get(name)))) problems.push(f + ": " + name + " (in " + ours.get(name) + ") isn't in its folder or imports")
    }
  }
  assert.deepEqual(problems, [])
})

test("icon buttons: every GlyphButton has a tip, and every key in a tip's brackets is a real key", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const keys = new Set(L.keyGroups.flatMap(g => g.keys.flatMap(([k]) => k.split(" or "))))
  const tips = []
  for (const f of qmlFiles().filter(f => path.basename(f) !== "GlyphButton.qml")) {
    const src = fs.readFileSync(path.join(dir, f), "utf8")
    for (const m of src.matchAll(/GlyphButton \{/g)) {
      let depth = 0, end = m.index
      for (; end < src.length; end++) { if (src[end] === "{") depth++; else if (src[end] === "}" && --depth === 0) break }
      assert.match(src.slice(m.index, end), /\btip: "/, f + ": a GlyphButton without a tip")
      tips.push(src.slice(m.index, end))
    }
    for (const m of src.matchAll(/IconTip \{[^\n]*/g)) tips.push(m[0])
  }
  assert.ok(tips.length >= 17, "found " + tips.length)  // 6 GlyphButtons, 11 IconTips (v0.1.30)
  const bracketed = tips.flatMap(t => [...t.matchAll(/\(([^()"]+)\)"/g)].map(m => m[1]))
  for (const k of bracketed) assert.ok(keys.has(k), "'" + k + "' in a tip is not a shortcut")
  assert.deepEqual([...new Set(bracketed)].sort(), ["?", "Esc", "e", "m", "o", "p", "r", "s", "x"])
})

// v0.1.30 regression: his saved setting, exactly as in shell.json. Omarchy
// hands settings over through Qt, so its lists arrive as sequences:
// Array.isArray false, though JSON.stringify gives the array. Stand-in: an
// object whose toJSON is the array.
const PHRASE41 = '{"firelink21/phrase41":{"bots":[{"label":"app-ui","name":"App UI"},{"label":"api","name":"API Engineer"},{"label":"auth-mail","name":"Auth & Mail"},{"name":"Product Lead","label":""}],"busyLists":["approved","in progress","review"]}}'
const sequence = list => Object.assign(Object.create(null), { length: list.length, toJSON: () => list.slice() })
test("his saved bots setting: Settings and the board read the same four bots", () => {
  const raw = JSON.parse(PHRASE41), P = "firelink21/phrase41"
  assert.deepEqual(L.botsEntry(raw, P), { problem: "", entry: raw[P] })
  const c = L.botsConfig(raw, P)
  assert.deepEqual(c.bots, [{ name: "App UI", label: "app-ui" }, { name: "API Engineer", label: "api" }, { name: "Auth & Mail", label: "auth-mail" }, { name: "Product Lead", label: "" }])
  assert.deepEqual(c.busyLists, ["approved", "in progress", "review"])
  assert.ok(raw[P].bots.every(L.botUsable))
})
test("settings from Qt: lists as sequences are read once they pass plainJson", () => {
  const P = "firelink21/phrase41", fromQt = JSON.parse(PHRASE41)
  fromQt[P].bots = sequence(fromQt[P].bots); fromQt[P].busyLists = sequence(fromQt[P].busyLists)
  assert.equal(L.botsEntry(fromQt, P).problem, "entry")  // the 0.1.29 bug, when read as is
  assert.equal(L.botsConfig(fromQt, P), null)
  const settings = L.plainJson({ bots: fromQt, defaultCollapsed: sequence(["closed", "research", "open"]), refreshIntervalSec: 120 })
  assert.deepEqual(L.botsEntry(settings.bots, P), { problem: "", entry: JSON.parse(PHRASE41)[P] })
  assert.equal(L.botsConfig(settings.bots, P).bots.length, 4)
  assert.deepEqual(L.lowerList(settings.defaultCollapsed), ["closed", "research", "open"])
  assert.deepEqual(L.withBusy(settings.bots, P, "todo", true)[P].busyLists, ["approved", "in progress", "review", "todo"])
  assert.deepEqual(L.plainJson(null), {})
  assert.deepEqual(L.plainJson(undefined), {})
  assert.deepEqual(L.plainJson("x"), {})
  const loop = {}; loop.self = loop
  assert.deepEqual(L.plainJson(loop), {})
})

test("pipeline marks: five statuses, https links only, nothing otherwise", () => {
  const m = L.pipelineMark({ status: "passed", url: "https://gitlab.com/g/a/-/pipelines/31", mr: "!31" })
  assert.deepEqual(m, { glyph: "\uf058", color: "#2da160", url: "https://gitlab.com/g/a/-/pipelines/31", tip: "Pipeline passed on !31: open it on GitLab" })
  const glyphs = ["passed", "failed", "running", "pending", "canceled"].map(s => L.pipelineMark({ status: s }).glyph)
  assert.equal(new Set(glyphs).size, 5)
  assert.equal(L.pipelineMark({ status: "failed" }).tip, "Pipeline failed")
  assert.equal(L.pipelineMark({ status: "canceled", url: "http://x/p/1", mr: "!4" }).url, "")
  assert.equal(L.pipelineMark({ status: "canceled", url: "http://x/p/1", mr: "!4" }).tip, "Pipeline canceled on !4")
  assert.equal(L.pipelineMark({ status: "running", url: "javascript:alert(1)" }).url, "")
  assert.equal(L.pipelineMark({ status: "pending", mr: "<b>x</b>" }).tip, "Pipeline pending")
  for (const p of [null, undefined, {}, { status: "success" }, { status: "manual" }, { status: "toString" }, "passed"]) assert.equal(L.pipelineMark(p), null)
})

test("shared refresh: one BoardService for every screen; Board.qml fetches boards only through it", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, "manifest.json"), "utf8"))
  assert.deepEqual(manifest.kinds, ["bar-widget", "service"])
  assert.deepEqual(manifest.entryPoints, { barWidget: "Board.qml", service: "BoardService.qml" })
  const board = fs.readFileSync(path.join(dir, "Board.qml"), "utf8")
  const service = fs.readFileSync(path.join(dir, "BoardService.qml"), "utf8")
  // The widget asks the shell for its own service, else keeps a private one of the same kind.
  assert.match(board, /bar\.shell\.serviceFor\(moduleName\)/)
  assert.match(board, /readonly property var feed: sharedFeed \|\| localFeed/)
  assert.match(board, /BoardService \{ id: localFeed \}/)
  // No board fetch of its own: "board" appears in no command the widget builds.
  assert.doesNotMatch(board, /helperPath\(\), "board"/)
  assert.match(service, /args: \["board", "--project", project, "--board", boardId\]/)
  // Two Processes in the service: one board fetch at a time for the whole shell
  // (fetch), and one merge-request list (mrFetch, which never runs "board").
  assert.equal((service.match(/^\s*Process \{/gm) || []).length, 2)
  assert.deepEqual([...service.matchAll(/^\s*Process \{\s*\n\s*id: (\w+)/gm)].map(m => m[1]), ["fetch", "mrFetch"])
})

test("popup height: Settings and Keys have no cap (they grow to the free screen height); board and issue keep it", () => {
  assert.equal(L.heightCap("settings", 960), 0)
  assert.equal(L.heightCap("keys", 960), 0)
  for (const v of ["board", "issue", "picker", ""]) assert.equal(L.heightCap(v, 960), 960)
  const fs = require("node:fs"), path = require("node:path")
  const board = fs.readFileSync(path.join(__dirname, "..", "Board.qml"), "utf8")
  assert.match(board, /contentHeight: panel\.fittedContentHeight\(keyCatcher\.implicitHeight, Logic\.heightCap\(root\.view, Style\.space\(640\)\)\)/)
})

test("compact settings: Start collapsed and the busy columns are wrapping rows of check boxes with the same gaps", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const settings = fs.readFileSync(path.join(dir, "SettingsView.qml"), "utf8")
  const bots = fs.readFileSync(path.join(dir, "BotsSection.qml"), "utf8")
  // One Flow of check boxes for Start collapsed (no full-width row per column).
  assert.match(settings, /Flow \{\s*width: parent\.width\s*spacing: Style\.space\(6\)\s*Repeater \{\s*model: view\.host\.availableColumns/)
  assert.doesNotMatch(settings, /id: rows/)
  // The busy row wraps with the same small gap; the room between boxes is the box's own padding.
  assert.match(bots, /Flow \{\s*width: parent\.width\s*spacing: Style\.space\(6\)/)
  assert.match(bots, /implicitWidth: checkRow\.implicitWidth \+ Style\.space\(10\)/)
})

test("adaptive refresh: pace from answers, interval from pace", () => {
  const col = (name, iids, labels) => ({ name, kind: "label", listId: name.length, issues: iids.map(i => ({ iid: i, labels: labels || [name] })) })
  const ans = cols => ({ state: "ready", columns: cols })
  const a = ans([col("todo", [1, 2]), col("review", [3])])
  // The first answer: calm 2 (the setting). Same again: calm grows. A move or a label change: 0.
  let p = L.nextPace(null, a)
  assert.equal(p.calm, 2)
  p = L.nextPace(p, ans([col("todo", [2, 1]), col("review", [3])]))
  assert.equal(p.calm, 3, "order and updatedAt don't count")
  assert.equal(L.nextPace(p, ans([col("todo", [1]), col("review", [3, 2])])).calm, 0, "a card moved")
  assert.equal(L.nextPace(p, ans([col("todo", [1, 2], ["todo", "api"]), col("review", [3])])).calm, 0, "a label changed")
  assert.equal(L.nextPace(p, ans([col("todo", [1, 2, 4]), col("review", [3])])).calm, 0, "a card came")
  // Errors keep the pace.
  assert.equal(L.nextPace(p, { state: "error" }), p)
  assert.equal(L.nextPace(null, { state: "error" }), null)
  // Active: a card in an in-progress or doing column.
  assert.ok(L.boardActive(ans([col("In Progress", [5])])))
  assert.ok(L.boardActive(ans([col("doing", [5])])))
  assert.ok(!L.boardActive(ans([col("in progress", [])])))
  assert.ok(!L.boardActive(ans([col("todo", [5]), col("review", [6])])), "other columns with cards are not in progress")
  assert.ok(!L.boardActive({ columns: [{ name: "in progress", kind: "open", issues: [{ iid: 1 }] }] }))
  // Intervals for a 60 s setting.
  const at = (calm, active) => L.adaptiveInterval(60, { calm, active: !!active })
  assert.deepEqual(L.adaptiveInterval(60, null), { sec: 60, why: "your setting" })
  assert.deepEqual(at(0), { sec: 30, why: "cards moved recently" })
  assert.deepEqual(at(1), { sec: 30, why: "cards moved recently" })
  assert.deepEqual([2, 3, 4, 5, 6, 7, 8, 50].map(c => at(c).sec), [60, 60, 120, 120, 240, 240, 240, 240])
  assert.equal(at(6).why, "nothing changed lately")
  assert.deepEqual(at(6, true), { sec: 60, why: "cards in progress" })
  assert.deepEqual(at(0, true).sec, 30)
  // Never under 30 s, never over 4x the setting.
  assert.equal(L.adaptiveInterval(30, { calm: 0 }).sec, 30)
  assert.equal(L.adaptiveInterval(10, { calm: 0 }).sec, 30)
  assert.equal(L.adaptiveInterval(900, { calm: 99 }).sec, 3600)
  assert.equal(L.adaptiveInterval(900, { calm: 0 }).sec, 450)
  assert.deepEqual([30, 60, 450, 3600].map(L.durationText), ["30 s", "1 min", "7 min 30 s", "60 min"])
  // Board.qml paces its timer and the due check from the shared cadence.
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const board = fs.readFileSync(path.join(dir, "Board.qml"), "utf8")
  assert.match(board, /interval: root\.cadence\.sec \* 1000/)
  assert.match(board, /feed\.request\(project, boardId, ifDue === true, cadence\.sec \* 1000 - 2000, moveFloor\)/)
  assert.match(board, /Logic\.adaptiveInterval\(refreshIntervalSec, feed\.paces\[fetchKey\]\)/)
})

test("alerts: settings per project, events between two good answers, the notify command", () => {
  // Settings: off by default; per project; other keys kept.
  assert.deepEqual(L.alertsFor(null, "a/b"), { review: false, idle: false })
  assert.deepEqual(L.alertsFor({ "a/b": { review: true } }, "a/b"), { review: true, idle: false })
  assert.deepEqual(L.alertsFor({ "a/b": { review: "yes" } }, "a/b"), { review: false, idle: false }, "only true counts")
  assert.deepEqual(L.withAlert({ "x/y": { idle: true } }, "a/b", "review", true), { "x/y": { idle: true }, "a/b": { review: true, idle: false } })
  assert.deepEqual(L.withAlert("junk", "a/b", "idle", true), { "a/b": { review: false, idle: true } })
  const row = (iid, labels, title) => ({ iid, title: title || "Card " + iid, labels, url: "https://gitlab.com/g/p/-/issues/" + iid })
  const ans = (cols, extra) => Object.assign({ state: "ready", project: "g/p", board: { id: 7 }, columns: cols }, extra || {})
  const col = (name, rows) => ({ name, kind: "label", listId: name.length, issues: rows })
  const a = ans([col("todo", [row(1, ["todo"]), row(2, ["todo", "app-ui"])]), col("in progress", [row(3, ["in progress", "api"])]), col("Review", [row(4, ["review"])])])
  const on = { review: true, idle: true, bots: { "g/p": { busyLists: ["in progress", "review"], bots: [{ name: "App UI", label: "app-ui" }, { name: "API", label: "api" }] } } }
  // Nothing changed: nothing. Not two good answers: nothing.
  assert.deepEqual(L.alertEvents(a, a, on), [])
  assert.deepEqual(L.alertEvents(null, a, on), [])
  assert.deepEqual(L.alertEvents({ state: "error" }, a, on), [])
  // One card into review: its own link; a title with markup stays plain here.
  const b = ans([col("todo", [row(1, ["todo"])]), col("in progress", [row(3, ["in progress", "api"])]), col("Review", [row(4, ["review"]), row(2, ["review", "app-ui"], "Fix <b> & co")])])
  assert.deepEqual(L.alertEvents(a, b, { review: true }), [{ headline: "#2 is in review", body: "#2 Fix <b> & co · g/p", url: "https://gitlab.com/g/p/-/issues/2" }])
  assert.deepEqual(L.alertEvents(a, b, { review: false }), [])
  assert.deepEqual(L.alertEvents(a, Object.assign({}, b, { project: "other/p" }), on), [], "another project: a fresh start")
  assert.deepEqual(L.alertEvents(a, b, { review: true, ignore: [2] }), [], "his own move")
  // Several: one notification, the board's link, at most three named.
  const many = ans([col("Review", [4, 5, 6, 7, 8].map(i => row(i, ["review"])))])
  assert.deepEqual(L.alertEvents(ans([col("Review", [row(4, ["review"])])]), many, { review: true }),
    [{ headline: "4 cards entered review", body: "#5 Card 5, #6 Card 6, #7 Card 7 +1 more · g/p", url: "https://gitlab.com/g/p/-/boards/7" }])
  // A bot stops working (in progress -> not): one notification for the bots that stopped.
  const c = ans([col("todo", [row(1, ["todo"]), row(2, ["todo", "app-ui"])]), col("in progress", []), col("Review", [row(4, ["review"]), row(3, ["review", "api"])])])
  assert.deepEqual(L.alertEvents(a, c, { idle: true, bots: on.bots }), [{ headline: "Stopped working: API", body: "On g/p: API is waiting in Review", url: "https://gitlab.com/g/p/-/boards/7" }])
  assert.deepEqual(L.alertEvents(a, c, { idle: false, bots: on.bots }), [])
  // Only https links; a bad project path: no board link.
  assert.equal(L.httpsUrl("http://x"), "")
  assert.equal(L.httpsUrl("https://gitlab.com/a b"), "")
  assert.equal(L.boardUrl({ project: "g/p;rm", board: { id: 7 } }), "")
  assert.equal(L.boardUrl({ project: "g/sub/p", board: { id: "x" } }), "https://gitlab.com/g/sub/p/-/boards")
  // The command (Omarchy bin/omarchy-notification-send): our app name, low urgency, the
  // body escaped for StyledText, --exec last with separate words, https only.
  assert.deepEqual(L.notifyArgv({ headline: "#2 is in review", body: "#2 Fix <b> & co · g/p", url: "https://gitlab.com/g/p/-/issues/2" }),
    ["omarchy-notification-send", "--app-name", "GitLab board", "-u", "low", "-g", "\uf296", "#2 is in review", "#2 Fix &lt;b&gt; &amp; co · g/p", "--exec", "xdg-open", "https://gitlab.com/g/p/-/issues/2"])
  assert.equal(L.notifyArgv({ headline: "h", body: "b", url: "javascript:x" }).indexOf("--exec"), -1)
  // Headlines and bodies start with our own text, never "-": not read as options.
  for (const ev of [...L.alertEvents(a, b, on), ...L.alertEvents(a, c, on)]) {
    assert.ok(!ev.headline.startsWith("-") && !ev.body.startsWith("-"))
  }
  const svc = require("node:fs").readFileSync(require("node:path").join(__dirname, "..", "BoardService.qml"), "utf8")
  // The only notifier, in the shared service.
  assert.equal((svc.match(/execDetached\(/g) || []).length, 1)
  assert.match(svc, /Quickshell\.execDetached\(Logic\.notifyArgv\(ev\)\)/)
})

test("alerts wiring: Settings saves settings.alerts per project; each copy hands its board to the service", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const board = fs.readFileSync(path.join(dir, "Board.qml"), "utf8")
  const settings = fs.readFileSync(path.join(dir, "SettingsView.qml"), "utf8")
  assert.match(board, /readonly property var alerts: Logic\.alertsFor\(saved\("alerts", null\), project\)/)
  assert.match(board, /onWatchCfgChanged: feed\.watch\(watchOwner, watchCfg\)/)
  assert.match(board, /Component\.onDestruction: feed\.watch\(watchOwner, null\)/)
  assert.match(board, /if \(nextAlerts !== undefined\) entry\.alerts = nextAlerts/)
  // No notifier in the widget: one per event comes from the service only.
  assert.doesNotMatch(board, /omarchy-notification-send|notifyArgv/)
  assert.match(settings, /onClicked: view\.host\.setAlert\(alertCheck\.modelData\.kind, !alertCheck\.on\)/)
})

test("merge requests: the answer checked, status pills, reviewer marks, sublines, the badge, the scope", () => {
  const row = { iid: 88, title: "Fix <b>", url: "https://gitlab.com/g/p/-/merge_requests/88", draft: false, project: "g/p", branch: "b", updatedAt: "2026-10-30T12:00:00Z",
    status: "conflict", author: { username: "bot", name: "Bot", avatar: "http://x/a.png" }, pipeline: { status: "running", url: "https://gitlab.com/p/1" },
    reviewers: [{ username: "me", name: "Me", avatar: "", state: "approved" }, { username: "x", name: "X", state: "bogus" }, "junk"] }
  const a = L.mrsAnswer(JSON.stringify({ state: "ready", scope: "all", review: [row, { iid: 0 }, null], mine: "junk" }))
  assert.equal(a.state, "ready")
  assert.deepEqual(a.mine, [])
  assert.equal(a.review.length, 1, "rows without an iid dropped")
  const r = a.review[0]
  assert.deepEqual(r.author, { username: "bot", name: "Bot", avatar: "" }, "http avatar dropped")
  assert.deepEqual(r.pipeline, { status: "running", url: "https://gitlab.com/p/1", mr: "!88" })
  assert.deepEqual(r.reviewers.map(p => p.state), ["approved", ""])
  assert.equal(L.mrsAnswer(JSON.stringify(Object.assign({}, row, { url: "javascript:x" }))).state, "error", "not an answer object: no state ready")
  assert.equal(L.mrsAnswer(JSON.stringify({ state: "ready", review: [Object.assign({}, row, { url: "http://x" })] })).review[0].url, "")
  assert.deepEqual(L.mrsAnswer("nope"), { state: "error", message: "board-fetch gave an unreadable answer.", review: [], mine: [] })
  assert.deepEqual(L.mrsAnswer('{"state":"logged-out","message":"Not signed in."}'), { state: "logged-out", message: "Not signed in.", review: [], mine: [] })
  // Pills: GitLab's status, draft first; "still checking" shows nothing.
  assert.deepEqual(L.mrStatus({ status: "mergeable" }), { text: "Ready", color: "#2da160" })
  assert.deepEqual(L.mrStatus({ status: "conflict" }), { text: "Conflicts", color: "#ec5941" })
  assert.deepEqual(L.mrStatus({ status: "requested_changes" }), { text: "Changes requested", color: "#c17d10" })
  assert.deepEqual(L.mrStatus({ status: "mergeable", draft: true }), { text: "Draft", color: "" })
  assert.deepEqual(L.mrStatus({ status: "checking" }), { text: "", color: "" })
  assert.deepEqual(L.mrStatus({ status: "toString" }), { text: "", color: "" })
  // Reviewer marks.
  assert.equal(L.reviewerMark({ name: "Me", state: "approved" }).tip, "Me approved")
  assert.equal(L.reviewerMark({ name: "Me", state: "requested_changes" }).color, "#c17d10")
  assert.deepEqual(L.reviewerMark({ name: "Me", state: "unreviewed" }), { glyph: "", color: "", tip: "Me hasn't reviewed yet" })
  assert.deepEqual(L.reviewerMark({ username: "me", state: "" }), { glyph: "", color: "", tip: "me" })
  assert.notEqual(L.reviewerMark({ state: "reviewed" }).glyph, "")
  // Second line.
  assert.equal(L.mrSubline(r, "review"), "g/p  \u00b7  b  \u00b7  by Bot")
  assert.equal(L.mrSubline(r, "mine"), "g/p  \u00b7  b  \u00b7  2 reviewers")
  assert.equal(L.mrSubline(Object.assign({}, r, { reviewers: [] }), "mine"), "g/p  \u00b7  b  \u00b7  no reviewer yet")
  assert.equal(L.mrSubline(Object.assign({}, r, { reviewers: [{}] }), "mine"), "g/p  \u00b7  b  \u00b7  1 reviewer")
  // Badge: waiting on his review only; unknown or none: no badge.
  assert.equal(L.mrBadge(a), "1")
  assert.equal(L.mrBadge({ state: "ready", review: new Array(12).fill(r) }), "9+")
  assert.equal(L.mrBadge({ state: "ready", review: [] }), "")
  assert.equal(L.mrBadge(undefined), "")
  assert.equal(L.mrBadge({ state: "error", review: [r] }), "")
  // Scope: all, or one project path; anything else falls back to all.
  assert.deepEqual(L.mrsArgs("all"), ["mrs"])
  assert.deepEqual(L.mrsArgs("g/sub/p"), ["mrs", "--project", "g/sub/p"])
  assert.deepEqual(L.mrsArgs("g/../p"), ["mrs"])
  assert.deepEqual(L.mrsArgs("--project"), ["mrs"])
  // The service: fetched only on request (no timer calls it), its own process.
  const fs = require("node:fs"), path = require("node:path")
  const svc = fs.readFileSync(path.join(__dirname, "..", "BoardService.qml"), "utf8")
  assert.equal((svc.match(/requestMrs\(/g) || []).length, 2, "defined once, called once (the pending one)")
  assert.match(svc, /mrFetch\.command = \[helperPath\(\)\]\.concat\(Logic\.mrsArgs\(scope\)\)/)
  assert.match(svc, /Date\.now\(\) - last\.startedAt < 60000/)
})

test("merge requests view wiring: m and the header button open it; it loads on open, scope or r only", () => {
  const fs = require("node:fs"), path = require("node:path"), dir = path.join(__dirname, "..")
  const board = fs.readFileSync(path.join(dir, "Board.qml"), "utf8")
  const view = fs.readFileSync(path.join(dir, "MrsView.qml"), "utf8")
  assert.match(board, /MrsView \{ id: mrsView; host: root; anchors\.fill: parent; visible: root\.view === "mrs" \}/)
  assert.match(board, /if \(name === "mrs" && view !== "mrs"\) mrsView\.open\(\)/)
  assert.match(board, /else if \(key === "m"\) root\.toggleView\("mrs"\)/)
  assert.match(board, /key === "r" && root\.view === "mrs"\) mrsView\.refresh\(\)/)
  assert.match(board, /root\.view === "mrs" && dy !== 0\) mrsView\.moveCursor\(dy\)/)
  assert.match(board, /else if \(root\.view === "mrs"\) mrsView\.activate\(\)/)
  assert.match(board, /Logic\.mrBadge\(\(root\.feed\.mrAnswers\[mrsView\.scope\] \|\| \{\}\)\.data\)/)
  // Only the view asks for the lists, and only these three ways.
  assert.deepEqual([...board.matchAll(/requestMrs\(/g)].length, 0)
  assert.deepEqual([...view.matchAll(/host\.feed\.requestMrs\(([^)]*)\)/g)].map(m => m[1]), ["scope, false", "scope, true", "scope, false"])
  // Read-only: a row opens its link and nothing else runs.
  assert.doesNotMatch(view, /execDetached|Process \{|helperPath/)
  assert.match(view, /host\.openUrl\(rows\[cursor\]\.url\)/)
  // Titles and messages from GitLab are plain text: every text is a BoardText
  // (PlainText), and none switches to rich text.
  assert.match(fs.readFileSync(path.join(dir, "components", "BoardText.qml"), "utf8"), /textFormat: Text\.PlainText/)
  assert.doesNotMatch(view, /textFormat|\bText \{|\bLabel \{/)
})

// --- 0.1.38 bulk actions ---------------------------------------------------------
const bcol = (name, kind, listId, iids, labels) => ({ name, kind, listId, issues: iids.map(i => ({ iid: i, title: "T" + i, labels: labels || (kind === "label" ? [name] : []) })) })
const BCOLS = [bcol("Open", "open", undefined, [10]), bcol("todo", "label", 3, [20, 21]), bcol("review", "label", 5, [50]), bcol("Closed", "closed", undefined, [9]), bcol("ann", "assignee", 8, [60])]

test("bulk picks: a card in its list, toggled, capped at 20, dropped once off the board", () => {
  assert.equal(L.bulkCap, 20)
  assert.equal(L.pickKey(BCOLS[1], 20), "label:3|20")
  let t = L.togglePick([], "label:3|20")
  assert.deepEqual(t, { picked: ["label:3|20"], full: false })
  assert.deepEqual(L.togglePick(t.picked, "label:3|20"), { picked: [], full: false })
  const twenty = Array.from({ length: 20 }, (_, i) => "label:3|" + (100 + i))
  assert.deepEqual(L.togglePick(twenty, "label:3|20"), { picked: twenty, full: true })
  assert.equal(L.togglePick(twenty, "label:3|100").picked.length, 19, "removing works at the cap")
  assert.deepEqual(L.livePicks(BCOLS, ["label:5|50", "label:3|99", "label:3|20"]), ["label:5|50", "label:3|20"])
  assert.deepEqual(L.pickedCards(BCOLS, ["label:3|21"]).map(p => [p.row.iid, p.column.name]), [[21, "todo"]])
})

test("bulk plan: each card's own --from, skips said out loud", () => {
  const cards = L.pickedCards(BCOLS, ["label:3|20", "label:5|50", "closed:Closed|9", "assignee:8|60"])
  const move = L.bulkPlan(cards, { kind: "move", to: BCOLS[2] }, "g/p", "7")
  assert.deepEqual(move.map(s => s.args), [
    ["move", "--project", "g/p", "--board", "7", "--iid", "20", "--from", "3", "--to", "5"], null,
    ["move", "--project", "g/p", "--board", "7", "--iid", "9", "--from", "closed", "--to", "5"], null])
  assert.deepEqual(move.map(s => s.skip), ["", "Already in review", "", "Can't move cards out of ann"])
  const add = L.bulkPlan(cards.slice(0, 2), { kind: "add", label: "todo" }, "g/p", "7")
  assert.deepEqual(add.map(s => s.args), [null, ["relabel", "--project", "g/p", "--iid", "50", "--add", "todo"]])
  const rm = L.bulkPlan(cards.slice(0, 2), { kind: "remove", label: "todo" }, "g/p", "7")
  assert.deepEqual(rm.map(s => s.skip), ["", "Doesn't have todo"])
  assert.deepEqual(rm[0].args, ["relabel", "--project", "g/p", "--iid", "20", "--remove", "todo"])
  assert.equal(L.closeOrReopen(cards), "close")
  assert.equal(L.closeOrReopen(cards.slice(2, 3)), "reopen")
  const close = L.bulkPlan(cards.slice(0, 3), { kind: "close" }, "g/p", "7")
  assert.deepEqual(close.map(s => s.args && s.args.slice(0, 1)), [["close"], ["close"], null])
  assert.equal(close[2].skip, "Already closed")
  assert.equal(L.bulkPlan(cards.slice(0, 1), { kind: "reopen" }, "g/p", "7")[0].skip, "Already open")
})

test("bulk wording: question, button, note and grouped lines", () => {
  const to = BCOLS[2]
  assert.equal(L.bulkQuestion({ kind: "move", to }, 3), "Move 3 cards to review?")
  assert.equal(L.bulkQuestion({ kind: "add", label: "bug" }, 1), "Add bug to 1 card?")
  assert.equal(L.bulkQuestion({ kind: "remove", label: "bug" }, 2), "Remove bug from 2 cards?")
  assert.equal(L.bulkQuestion({ kind: "reopen" }, 2), "Reopen 2 cards?")
  assert.equal(L.bulkButton({ kind: "move", to }, 3), "Move 3 cards")
  assert.equal(L.bulkButton({ kind: "close" }, 1), "Close 1 card")
  assert.match(L.bulkNote({ kind: "move", to: BCOLS[3] }), /closes on GitLab and keeps its labels/)
  assert.match(L.bulkNote({ kind: "add", label: "bug" }), /^Only the label bug changes\. One card at a time/)
  const cards = L.pickedCards(BCOLS, ["label:3|20", "label:5|50", "label:3|21", "closed:Closed|9"])
  const lines = L.bulkLines(L.bulkPlan(cards, { kind: "move", to }, "g/p", "7"), { kind: "move", to })
  assert.deepEqual(lines, [{ text: "todo \u2192 review", skip: false, iids: "#20 #21" }, { text: "Closed \u2192 review", skip: false, iids: "#9" },
    { text: "Skipped, already in review", skip: true, iids: "#50" }])
})

test("bulk outcome: done, ordinary failures go on, sign-in and timeouts stop", () => {
  const mv = { kind: "move", to: BCOLS[2] }
  assert.deepEqual(L.bulkOutcome({ state: "ready" }, mv), { ok: true, stop: false, text: "Moved to review" })
  assert.deepEqual(L.bulkOutcome({ state: "ready" }, { kind: "add", label: "bug" }).text, "Added bug")
  assert.deepEqual(L.bulkOutcome({ state: "stale", message: "#4 changed" }, mv), { ok: false, stop: false, text: "Not moved: it changed on GitLab after the board loaded. Nothing was written." })
  assert.deepEqual(L.bulkOutcome({ state: "error", message: "Move failed: 403 Forbidden" }, mv), { ok: false, stop: false, text: "Move failed: 403 Forbidden" })
  assert.equal(L.bulkOutcome({ state: "logged-out", message: "Not signed in to gitlab.com. Run: glab auth login" }, mv).stop, true)
  assert.equal(L.bulkOutcome({ state: "no-glab", message: "x" }, mv).stop, true)
  const t = L.bulkOutcome({ state: "error", message: "GitLab did not answer within 30 seconds. The move may have gone through." }, mv)
  assert.deepEqual(t, { ok: false, stop: true, text: "GitLab did not answer within 30 seconds. The move may have gone through." })
  assert.equal(L.bulkOutcome({ state: "error", message: "GitLab did not answer within 30 seconds." }, mv).text, "GitLab did not answer within 30 seconds. It may have gone through.")
  assert.equal(L.bulkOutcome({ state: "timeout", message: "" }, mv).text, "No answer from glab. It may have gone through.")
  assert.equal(L.bulkOutcome(null, mv).text, "Failed.")
})

test("bulk summary counts done of the cards it tried to change", () => {
  const r = st => st.map(s => ({ status: s }))
  assert.equal(L.bulkSummary({ kind: "move", to: BCOLS[2] }, r(["done", "done", "failed"])), "Moved 2 of 3 cards to review. 1 failed.")
  assert.equal(L.bulkSummary({ kind: "close" }, r(["done", "skipped"])), "Closed 1 of 1 card.")
  assert.equal(L.bulkSummary({ kind: "add", label: "bug" }, r(["done", "failed", "untried", "untried"])), "Added bug to 1 of 4 cards. 1 failed, 2 not tried.")
})
