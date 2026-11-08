# GLB-04: a label write needs every group-board page, not a partial inventory.
import json, os, pathlib, shutil, subprocess, sys, tempfile
src=pathlib.Path(sys.argv[1]).resolve(); passed=failed=0
def ok(name,value):
    global passed,failed
    if value: passed+=1
    else: failed+=1; print("FAIL",name)
with tempfile.TemporaryDirectory() as td:
    d=pathlib.Path(td); (d/"bin").mkdir(); (d/"fx").mkdir()
    wrapper=d/"bin/glab"
    wrapper.write_text('''#!/bin/bash
# Like GitLab, page two is returned only when the caller asks for pagination.
if [[ ${*: -1} == groups/top%2Fsub/boards* && -e $CASE/page2 ]]; then
  echo '[]'
  [[ " $* " != *" --paginate "* ]] || cat "$CASE/page2"
  exit 0
fi
exec "$REAL_FAKE" "$@"
'''); wrapper.chmod(0o755)
    env=dict(os.environ,CASE=str(d),REAL_FAKE=str(src/"tests/fake-glab"),PATH=str(d/"bin")+":"+os.environ["PATH"],
             FAKE_DIR=str(d/"fx"),FAKE_LOG=str(d/"log"),XDG_CACHE_HOME=str(d/"cache"))
    def fx(name,value): (d/"fx"/(name+".json")).write_text(json.dumps(value))
    fx("boards",[]);fx("labels",[{"name":"ordinary"},{"name":"Late status"}]);fx("put",{"iid":1,"labels":["ordinary"],"state":"opened"})
    def run(cmd="relabel",label="ordinary",bulk=False):
        (d/"log").write_text("")
        args=[str(src/"board-fetch"),cmd,"--project","top/sub/app"]
        if cmd=="relabel":args += ["--iid","1","--add",label]
        out=subprocess.check_output(args,env=env,input=(json.dumps(["relabel","--project","top/sub/app","--iid","1","--add",label])+"\n").encode() if bulk else None,timeout=12)
        writes=[x for x in (d/"log").read_text().splitlines() if x.startswith("PUT ")]
        return json.loads(out.splitlines()[0]),writes
    fx("project",{"namespace":{"kind":"user"}})
    out,writes=run();ok("a verified user namespace permits the ordinary label write",out["state"]=="ready" and len(writes)==1)
    fx("project",{"namespace":{"kind":"group","full_path":"top/sub"}})
    fx("group-boards-top%2Fsub",[]);fx("group-boards-top",[])
    out,writes=run();ok("complete empty group inventories permit ordinary writes",out["state"]=="ready" and len(writes)==1)
    (d/"fx/project.json").unlink();out,writes=run();ok("unreadable namespace fails closed",out["state"]=="error" and not writes)
    fx("project",{});out,writes=run();ok("missing namespace fails closed",out["state"]=="error" and not writes)
    fx("project",{"namespace":{"kind":"group","full_path":"top/sub"}})
    (d/"fx/group-boards-top%2Fsub.json").unlink();out,writes=run();ok("unreadable group fails closed",out["state"]=="error" and not writes)
    out,writes=run("labels");ok("label picker does not advertise an incomplete inventory",out["state"]=="error")
    out,writes=run("bulk",bulk=True);ok("bulk relabel also fails closed",out["state"]=="error" and not writes)
    fx("group-boards-top%2Fsub",{"unexpected":"object"});out,writes=run();ok("malformed group response fails closed",out["state"]=="error" and not writes)
    fx("group-boards-top%2Fsub",[]);(d/"fx/group-boards-top.json").unlink();out,writes=run();ok("unreadable parent group fails closed",out["state"]=="error" and not writes)
    fx("group-boards-top",[]);(d/"page2").write_text(json.dumps([{"lists":[{"label":{"name":"Late status"}}]}]))
    out,writes=run(label="Late status");ok("a status label on group-board page two is never written",out["state"]=="error" and not writes)
    out,writes=run("labels");ok("page-two status label is absent from editable choices",out["state"]=="ready" and "Late status" not in [x["name"] for x in out["labels"]])
print(f"passed {passed}, failed {failed}");sys.exit(bool(failed))
