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
  assert.deepEqual(L.keyGroups.map(g => g.title), ["Board", "Confirm a move or a close", "Anywhere", "Issue", "Comment box", "Pickers and filters", "Setup panel"])
  assert.match(action("Setup panel", "Enter or Space"), /main button/)
  assert.match(action("Setup panel", "r"), /Try again/)
  assert.match(action("Anywhere", "?"), /keyboard button in the header/)
  for (const k of ["o", "c", "e", "x"]) assert.ok(action("Issue", k), k)
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
