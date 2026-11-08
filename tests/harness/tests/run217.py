# GLB-03: exercise real popup and notification launch boundaries, never a browser.
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import *
from fixtures import BOARD
h=Harness(sys.argv[1], {"id":"odevvy.gitlabby","settingsRevision":2,"defaultProject":"group/app","openLinks":"app"})
h.ev("root.opened = true");h.spin(50);h.answer("board",BOARD)
def opened(url, markdown=False):
    h.ev("root.opened = true"); n=len(h.launched())
    h.ev("root.openUrl(%s, %s)"%(json.dumps(url),"true" if markdown else "false"));h.spin(30)
    return h.launched()[n:]
h.ok("configured GitLab issue still opens in the selected app window",opened("https://gitlab.com/group/app/-/issues/2")==[["omarchy-launch-webapp","https://gitlab.com/group/app/-/issues/2"]])
h.ok("a generated off-host link does nothing",opened("https://outside.invalid/login")==[])
h.ok("an explicit external Markdown link uses a browser with its address bar",opened("https://outside.invalid/login",True)==[["omarchy-launch-browser","https://outside.invalid/login"]])
h.ok("same-host Markdown retains app-window preference",opened("https://gitlab.com/help",True)==[["omarchy-launch-webapp","https://gitlab.com/help"]])
for bad in ["https://gitlab.com@outside.invalid/x","https://user:password@gitlab.com/x","https://gitlab.com\\@outside.invalid/x","https://gitlab.com/a\\b","https://gitlab.com/a b","https://gitlab.com/a\nb","file:///tmp/x","javascript:alert(1)"]:
    h.ok("unsafe or ambiguous authority cannot launch: "+bad,opened(bad)==[] and opened(bad,True)==[])
h.ev("root.opened = true; root.showView('board'); root.openIssue(root.columns[1].issues[0])");h.spin(50)
h.answer("issue",{"state":"ready","issue":{"iid":2,"title":"Test issue","description":"[documentation](https://outside.invalid/docs)","url":"https://gitlab.com/group/app/-/issues/2","labels":[],"assignees":[]}});h.spin(50)
iw=h.cls("IssueView");n=len(h.launched());h.ev("description.linkActivated('https://outside.invalid/docs')",h.ctx_of(iw),iw);h.spin(30)
h.ok("actual rendered Markdown activation reaches the external-browser path",h.launched()[n:]==[["omarchy-launch-browser","https://outside.invalid/docs"]])
h.ev("root.settings = Object.assign({}, root.settings, {gitlabHost:'gitlab.example'})");h.spin(60)
h.ok("self-hosted GitLab is allowed",opened("https://gitlab.example/group/app/-/issues/2")==[["omarchy-launch-webapp","https://gitlab.example/group/app/-/issues/2"]])
h.ok("old server is not still trusted after switching",opened("https://gitlab.com/group/app/-/issues/2")==[])
n=len(h.launched());h.ev("root.feed.notify([{headline:'h',body:'b',url:'https://outside.invalid/login'}],{host:'gitlab.example',links:'app'})");h.spin(30)
h.ok("off-host notification is sent without an executable click target",len(h.launched()[n:])==1 and '--exec' not in h.launched()[n])
n=len(h.launched());h.ev("root.feed.notify([{headline:'h',body:'b',url:'https://gitlab.example/group/app/-/issues/2'}],{host:'gitlab.example',links:'app'})");h.spin(30)
h.ok("notification service passes the configured host, not a hard-coded default",h.launched()[n:][0][-3:]==['--exec','omarchy-launch-webapp','https://gitlab.example/group/app/-/issues/2'])
sys.exit(h.finish())
