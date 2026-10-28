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

test("links: http(s) as is, GitLab-relative on the issue's host, nothing else", () => {
  const issueUrl = "https://gitlab.com/group/app/-/issues/5"
  assert.equal(L.linkUrl("/group/app/-/issues/6", issueUrl), "https://gitlab.com/group/app/-/issues/6")
  assert.equal(L.linkUrl("https://example.com/x", issueUrl), "https://example.com/x")
  assert.equal(L.linkUrl("javascript:alert(1)", issueUrl), "")
  assert.equal(L.linkUrl("/relative", ""), "")
})

const md = (text) => L.markdown(text, (t) => t.length * 7, (px) => px)

test("markdown: raw HTML is text, images are links, hrefs can't break out", () => {
  const x = md("<script>alert(1)</script> <img src=https://evil.example/x.png> ![pic](https://evil.example/p.png)")
  assert.ok(!x.includes("<script") && !x.includes("<img") && x.includes("&lt;img"))
  assert.ok(x.includes('<a href="https://evil.example/p.png">pic</a>'))
  assert.ok(!md('[a](https://x.example/"onmouseover=1)').includes('href="https://x.example/"onmouseover'))
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

test("the README's Keyboard section lists exactly the keys the popup shows", () => {
  const readme = require("node:fs").readFileSync(require("node:path").join(__dirname, "..", "README.md"), "utf8")
  const section = readme.split("\n## Keyboard\n")[1].split("\n## ")[0]
  const rows = section.split("\n").filter(l => /^\| (?!Key |---)/.test(l)).map(l => l.replace(/`/g, ""))
  assert.deepEqual(rows, L.keys.map(([k, a]) => "| " + k + " | " + a + " |"))
})
