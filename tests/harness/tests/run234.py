# 0.1.134 (SEC-02): only https destinations (the same rule as a Markdown click)
# keep an href in the issue description. javascript, file, data and http stay
# visible as plain text. Comments are plain text too, so the same strings
# never become markup there.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD

h = Harness(sys.argv[1], {"id": "odevvy.gitlabby", "settingsRevision": 2, "defaultProject": "group/app"})
h.ev("root.opened = true"); h.spin(50); h.answer("board", BOARD); h.spin(80)
h.ev("root.openIssue(root.columns[1].issues[0])"); h.spin(80)
ISSUE = {
    "iid": 2, "title": "Header palette button", "state": "opened", "labels": ["todo"],
    "url": "https://gitlab.com/group/app/-/issues/2",
    "description": "See [docs](https://outside.invalid/docs) and [click me](javascript:evil) and ![](file:///etc/passwd) and [note](data:text/html,hi) and http://example.com/x and [six](/group/app/-/issues/6).",
    "author": "ada", "milestone": "", "assignees": [],
    "createdAt": "2026-10-29T12:00:00Z", "updatedAt": "2026-10-29T12:00:00Z"
}
NOTES = [{
    "id": 1, "body": "See [docs](https://outside.invalid/docs) and [click me](javascript:evil) and file:///etc/passwd",
    "createdAt": "2026-10-30T12:00:00Z", "author": {"username": "ada", "name": "Ada Example"}
}]
h.answer("issue", {"state": "ready", "message": "", "issue": ISSUE}); h.spin(80)
h.answer("notes", {"state": "ready", "message": "", "iid": 2, "more": False, "notes": NOTES}); h.spin(200)
iw = h.cls("IssueView")
html = h.ev("description.text", h.ctx_of(iw), iw)
h.ok("https Markdown keeps an href a click would open", '<a href="https://outside.invalid/docs">docs</a>' in html, html)
h.ok("a GitLab-relative path is resolved on the issue's host", '<a href="https://gitlab.com/group/app/-/issues/6">six</a>' in html, html)
h.ok("javascript is plain visible text, no href", "click me" in html and "href=\"javascript:" not in html, html)
h.ok("file: is plain visible text, no href", "file:///etc/passwd" in html and "href=\"file:" not in html, html)
h.ok("data: is plain visible text, no href", "note" in html and "href=\"data:" not in html, html)
h.ok("an http auto-link stays visible text, no href", "http://example.com/x" in html and "href=\"http:" not in html, html)
bodies = [str(it.property("text")) for it in h.visible(lambda it: it.metaObject().className().startswith("BoardText"))]
comment = next((t for t in bodies if "javascript:evil" in t), "")
h.ok("the same strings in a comment stay literal plain text",
     "[click me](javascript:evil)" in comment and "href=" not in comment, comment)
sys.exit(h.finish())
