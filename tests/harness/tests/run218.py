# GLB-05: observe actual image requests, with every reply served in memory.
import sys, os, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
from network import install, requests
install(lib)
from lib import *
from fixtures import BOARD
b=copy.deepcopy(BOARD);row=next(i for c in b['columns'] for i in c['issues'])
row['assignees']=[{'username':'alice','name':'Alice Smith','avatar':'https://outside.invalid/avatar.png'}]
h=Harness(sys.argv[1],{'id':'odevvy.gitlabby','settingsRevision':2,'defaultProject':'group/app','defaultCollapsed':[]})
h.ev('root.opened = true');h.spin(50);h.answer('board',b);h.spin(100)
h.ok('an external avatar never reaches the image network manager',not requests)
h.ok('existing initials are the fallback, with no new UI',bool(h.visible(lambda x:x.objectName()=='avatarInitials' and x.property('text')=='AS')))
row['assignees'][0]['avatar']='https://gitlab.com/uploads/alice.png'
h.ev('root.refresh()');h.answer('board',b);h.spin(100)
h.ok('a configured-host avatar still loads',h.until(lambda:'https://gitlab.com/uploads/alice.png' in requests))
n=len(requests);h.ev('root.setShowAvatars(false)');h.spin(40)
row['assignees'][0]['avatar']='https://gitlab.com/uploads/new.png';h.ev('root.refresh()');h.answer('board',b);h.spin(100)
h.ok('the existing off switch still prevents all image requests',len(requests)==n)
h.ev("root.settings = Object.assign({}, root.settings, {gitlabHost:'gitlab.example',showAvatars:true})");h.spin(40)
h.ev("root.switchTo('group/app','','')");h.spin(40)
row['assignees'][0]['avatar']='https://gitlab.example/uploads/alice.png';h.answer('board',b);h.spin(100)
h.ok('self-hosted avatars use the configured server',h.until(lambda:'https://gitlab.example/uploads/alice.png' in requests))
h.ok('no unrelated image host was requested',all(u.startswith(('https://gitlab.com/','https://gitlab.example/')) for u in requests),requests)
sys.exit(h.finish())
