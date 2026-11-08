# GLB-01: real helper processes racing logout never leave private saved boards.
import json, os, pathlib, subprocess, sys, tempfile, time
src = pathlib.Path(sys.argv[1]).resolve()
passed = failed = 0
def ok(name, value):
    global passed, failed
    if value: passed += 1
    else: failed += 1; print("FAIL", name)
with tempfile.TemporaryDirectory() as td:
    d = pathlib.Path(td); (d / "bin").mkdir(); (d / "fx").mkdir()
    for name, value in {"boards": [{"id":7,"name":"Dev","lists":[]}],
                        "open": [{"iid":1,"title":"Private test card","labels":[],"state":"opened"}],
                        "closed": []}.items():
        (d / "fx" / (name + ".json")).write_text(json.dumps(value))
    wrapper = d / "bin/glab"
    wrapper.write_text('''#!/bin/bash
if [[ $1 == config && $2 == get ]]; then
  if [[ -e $CASE/gate-account ]]; then
    if [[ -e $CASE/account-once ]]; then
      # Capture the username before logout, then delay delivery to the helper.
      touch "$CASE/account-entered"
      while [[ -e $CASE/gate-account ]]; do sleep 0.02; done
      echo me; exit 0
    fi
    touch "$CASE/account-once"
  fi
  if [[ -e $CASE/signedout ]]; then exit 0; fi
  if [[ -e $CASE/account ]]; then cat "$CASE/account"; exit 0; fi
fi
if [[ $1 == auth && $2 == logout ]]; then touch "$CASE/signedout"; fi
if [[ ${*: -1} == *"issues?state=opened"* && -e $CASE/gate ]]; then
  touch "$CASE/entered"
  while [[ -e $CASE/gate ]]; do sleep 0.02; done
fi
exec "$REAL_FAKE" "$@"
''')
    wrapper.chmod(0o755)
    env = dict(os.environ, CASE=str(d), REAL_FAKE=str(src / "tests/fake-glab"),
               PATH=str(d / "bin") + ":" + os.environ["PATH"], FAKE_DIR=str(d / "fx"),
               FAKE_LOG=str(d / "calls"), XDG_CACHE_HOME=str(d / "cache"))
    def run(*args):
        return json.loads(subprocess.check_output([str(src / "board-fetch"), *args], env=env, timeout=12))
    args = ("--project", "group/app", "--board", "7")
    ok("normal fetch can save a private card", run(*args)["state"] == "ready" and run("cached", *args).get("cached"))
    (d / "gate").touch()
    board = subprocess.Popen([str(src / "board-fetch"), *args], env=env, stdout=subprocess.PIPE)
    limit = time.monotonic() + 5
    while not (d / "entered").exists() and time.monotonic() < limit: time.sleep(0.01)
    ok("fetch reached the delayed private response", (d / "entered").exists())
    logout = subprocess.Popen([str(src / "board-fetch"), "logout"], env=env, stdout=subprocess.PIPE)
    time.sleep(0.15)
    (d / "gate").unlink()
    b = json.loads(board.communicate(timeout=12)[0]); out = json.loads(logout.communicate(timeout=12)[0])
    ok("logout completes and removes private boards after the old request ends",
       b["state"] == "ready" and out["state"] == "logged-out" and not (d / "cache/odevvy.gitlabby").exists())
    ok("no cache without a saved account", run("cached", *args) == {"state":"none"})
    run(*args)
    ok("a late anonymous response cannot persist an unknown-account board", not (d / "cache/odevvy.gitlabby").exists())
    (d / "signedout").unlink(); (d / "entered").unlink(); (d / "gate").touch()
    board = subprocess.Popen([str(src / "board-fetch"), *args], env=env, stdout=subprocess.PIPE)
    limit = time.monotonic() + 5
    while not (d / "entered").exists() and time.monotonic() < limit: time.sleep(0.01)
    (d / "account").write_text("other\n"); (d / "gate").unlink()
    board.communicate(timeout=12)
    ok("a response from the old account is never saved under a replacement account", not (d / "cache/odevvy.gitlabby").exists())
    (d / "account").unlink(); (d / "gate-account").touch()
    board = subprocess.Popen([str(src / "board-fetch"), *args], env=env, stdout=subprocess.PIPE)
    limit = time.monotonic() + 5
    while not (d / "account-entered").exists() and time.monotonic() < limit: time.sleep(0.01)
    logout = subprocess.Popen([str(src / "board-fetch"), "logout"], env=env, stdout=subprocess.PIPE)
    time.sleep(0.15); (d / "gate-account").unlink()
    board.communicate(timeout=12); out = json.loads(logout.communicate(timeout=12)[0])
    ok("logout also wins the final account-check-to-rename race", out["state"] == "logged-out" and not (d / "cache/odevvy.gitlabby").exists())
print(f"passed {passed}, failed {failed}")
sys.exit(bool(failed))
