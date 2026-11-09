# GLB-05 and R2-04: avatars only from the configured host, and never through
# Qt's network stack (which follows redirects to any host). Qt's image requests
# are observed in memory (network.py); board-fetch avatars answers stand in.
import sys, os, copy, base64, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib
from network import install, requests, PNG
web=lambda:[u for u in requests if not u.startswith('data:')]
install(lib)
from lib import *
from fixtures import BOARD
DATA = "data:image/png;base64," + base64.b64encode(PNG).decode()
b=copy.deepcopy(BOARD);rows=[i for c in b['columns'] for i in c['issues']];row=rows[0]
row['assignees']=[{'username':'alice','name':'Alice Smith','avatar':'https://outside.invalid/avatar.png'}]
h=Harness(sys.argv[1],{'id':'odevvy.gitlabby','settingsRevision':2,'defaultProject':'group/app','defaultCollapsed':[]})
pics=lambda:[it.property('source').toString() for it in h.walk() if it.objectName()=='avatarImage']
asked=lambda:[c for c in h.running('avatars', raw=True)]
written=lambda:h.ev(h.PROCS+".filter(function(p){ return p.running && p.command[1] === 'avatars' }).map(function(p){ return p.written[p.written.length - 1] })")
h.ev('root.opened = true');h.spin(50);h.answer('board',b);h.spin(100)
h.ok('an external avatar is never asked for',not asked() and not web(),(asked(),web()))
h.ok('existing initials are the fallback, with no new UI',bool(h.visible(lambda x:x.objectName()=='avatarInitials' and x.property('text')=='AS')))
PIC='https://gitlab.com/uploads/alice.png?v=1'
row['assignees'][0]['avatar']=PIC;rows[1]['assignees']=[{'username':'alice','name':'Alice Smith','avatar':PIC}]
h.ev('root.refresh()');h.answer('board',b);h.spin(100)
h.ok('a configured-host avatar is asked of board-fetch once, on stdin',[c[1:] for c in asked()]==[['avatars','--hostname','gitlab.com']] and written()==[PIC+'\n'],(asked(),written()))
h.ok('... and never of Qt, so no redirect can be followed',not web() and all(p=='' for p in pics()),(web(),pics()))
h.answer('avatars',{'state':'ready','avatars':{PIC:DATA}});h.spin(150)
h.ok('its answer shows as the picture, from memory',pics().count(DATA)==2 and not web(),pics())
h.ok('the initials give way once it loads',h.until(lambda:not h.visible(lambda x:x.objectName()=='avatarInitials' and x.property('text')=='AS')))
h.ok('a picture already in is not asked for again',not asked())
BAD='https://gitlab.com/uploads/bob.png';row['assignees'].append({'username':'bob','name':'Bob','avatar':BAD})
h.ev('root.refresh()');h.answer('board',b);h.spin(100)
h.answer('avatars',{'state':'ready','avatars':{BAD:'https://outside.invalid/bob.png'}});h.spin(100)
h.ok('an answer that is not a data image gives initials, never a URL',h.ev("root.feed.avatars[%r]"%BAD)=='' and not any('outside' in p for p in pics()) and not web(),pics())
h.ok('a refused picture is not asked for again',not asked())
n=len(web());h.ev('root.setShowAvatars(false)');h.spin(40)
row['assignees'][0]['avatar']='https://gitlab.com/uploads/new.png';h.ev('root.refresh()');h.answer('board',b);h.spin(100)
h.ok('the existing off switch still prevents all image requests',len(web())==n and not asked() and all(p=='' for p in pics()),(asked(),pics()))
h.ev("root.settings = Object.assign({}, root.settings, {gitlabHost:'gitlab.example',showAvatars:true})");h.spin(40)
h.ok('another server forgets the pictures',h.ev('Object.keys(root.feed.avatars).length')==0)
h.ev("root.switchTo('group/app','','')");h.spin(40)
row['assignees'][0]['avatar']='https://gitlab.example/uploads/alice.png';h.answer('board',b);h.spin(100)
h.ok('self-hosted avatars are asked of the configured server',[c[1:] for c in asked()]==[['avatars','--hostname','gitlab.example']] and written()==['https://gitlab.example/uploads/alice.png\n'],(asked(),written()))
h.ok('stdin closes once the URLs are in, so board-fetch ends',h.ev(h.PROCS+".filter(function(p){ return p.running && p.command[1] === 'avatars' })[0].stdinEnabled") is False)
h.ev('root.feed.forget()');h.answer('avatars',{'state':'ready','avatars':{'https://gitlab.example/uploads/alice.png':DATA}});h.spin(100)
h.ok('an answer asked for before forgetting is dropped',h.ev('Object.keys(root.feed.avatars).length')==0)
h.ok('... and asked again afresh',written()==['https://gitlab.example/uploads/alice.png\n'],written())
h.answer('avatars',{'state':'ready','avatars':{}});h.spin(100)
many=['https://gitlab.example/uploads/u%d.png'%i for i in range(41)]
h.ev('%s.forEach(function(u){ root.feed.avatar(u) })'%json.dumps(many));h.spin(150)
h.ok('at most 40 pictures a run',written()==['\n'.join(many[:40])+'\n'],written())
h.answer('avatars',{'state':'ready','avatars':{}});h.spin(150)
h.ok('the rest follow in the next run',written()==[many[40]+'\n'],written())
h.ok('Qt never requested an image from the network at all',not web(),web())
sys.exit(h.finish())
