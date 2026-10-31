#!/usr/bin/env bash
# Offline tests for board-fetch against tests/fake-glab. No network, no token.
set -uo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fetch="$here/../board-fetch"
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"; cp "$here/fake-glab" "$work/bin/glab"
# board-fetch runs glab as `timeout -k 5 30 glab ...`; this stand-in keeps the
# real timeout (coreutils) but cuts the limits to 1 s so the T tests run fast.
real_timeout=$(command -v timeout)
{ printf '#!/usr/bin/env bash\nreal=%q\n' "$real_timeout"; cat <<'SH'; } >"$work/bin/timeout"
# Each glab call's limit (what is left of the deadline, at most 30) goes to $FAKE_LOG.limits.
if [[ $1 == -k && $2 == 5 && $3 =~ ^[0-9]+$ && $3 -ge 1 && $3 -le 30 && $4 == glab ]]; then
  printf '%s\n' "$3" >>"$FAKE_LOG.limits"; exec "$real" -k 1 1 "${@:4}"
fi
[[ $1 == 5 && $2 == glab && $3 == config ]] && exec "$real" 1 "${@:2}"  # the account lookup
exit 99
SH
chmod +x "$work/bin/timeout"
export PATH="$work/bin:$PATH" FAKE_LOG="$work/log" FAKE_DIR="$work/fx" XDG_CACHE_HOME="$work/cache"  # never the real ~/.cache
unset XDG_RUNTIME_DIR  # no sign-in mark unless a test sets one (E block)
pass=0 fail=0
check() { # name jq-expression json
  if jq -e "$2" >/dev/null 2>&1 <<<"$3"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL: $1"; echo "  $3" | cut -c1-400; fi
}
fx() { mkdir -p "$FAKE_DIR"; cat >"$FAKE_DIR/$1.json"; }
reset() { rm -rf "$FAKE_DIR" "$FAKE_LOG"; }
cols='[.columns[] | {(.name): [.issues[].iid]}] | add'

# --- A: board with label lists, an assignee list, open + closed -------------
reset
fx boards <<'J'
[{"id":7,"name":"Dev","hide_backlog_list":false,"hide_closed_list":false,"labels":[],"milestone":null,"assignee":null,
  "lists":[{"id":2,"position":1,"label":{"name":"Doing"}},{"id":1,"position":0,"label":{"name":"To Do"}},
           {"id":3,"position":2,"label":null,"assignee":{"username":"alice"}}]},
 {"id":8,"name":"Lean","hide_backlog_list":true,"hide_closed_list":true,"labels":[{"name":"team-a"}],
  "milestone":{"title":"v1.0"},"assignee":{"id":42},"weight":3,"lists":[{"id":9,"position":0,"label":{"name":"Doing"}}]}]
J
fx open <<'J'
[{"iid":1,"title":"no labels","state":"opened","labels":[],"web_url":"u1"},
 {"iid":2,"title":"todo","state":"opened","labels":["To Do"],"web_url":"u2"}]
[{"iid":3,"title":"two list labels","state":"opened","labels":["Doing","To Do"],"web_url":"u3"},
 {"iid":4,"title":"other label","state":"opened","labels":["bug"],"web_url":"u4"}]
J
fx closed <<<'[{"iid":9,"title":"done","state":"closed","labels":["Doing"],"web_url":"u9"}]'
out=$("$fetch" --project group/app)
check "A ready" '.state == "ready" and .board == {"id":7,"name":"Dev"} and .fallback == false' "$out"
check "A order" '[.columns[].name] == ["Open","To Do","Doing","alice","Closed"]' "$out"
check "A mapping" "$cols"' == {"Open":[1,4],"To Do":[2,3],"Doing":[3],"alice":[],"Closed":[9]}' "$out"
check "A unsupported note" '.columns[3].kind == "other" and (.columns[3].note | test("not supported"))' "$out"
check "A boards list" '.boards == [{"id":7,"name":"Dev"},{"id":8,"name":"Lean"}]' "$out"
check "A open ordered by board position" '.' "$(grep -q 'state=opened&scope=all&order_by=relative_position&sort=asc' "$FAKE_LOG" && echo true || echo false)"

# --- B+C: hidden Open/Closed lists and board scope --------------------------
: >"$FAKE_LOG"
out=$("$fetch" --project group/app --board 8)
check "B hidden lists" '[.columns[].name] == ["Doing"] and .board.name == "Lean"' "$out"
check "B no closed call" '.' "$(grep -q 'state=closed' "$FAKE_LOG" && echo false || echo true)"
check "C scope filters" '.' "$(grep -q 'state=opened.*&labels=team-a&milestone=v1.0&assignee_id=42&weight=3' "$FAKE_LOG" && echo true || echo false)"

# --- E: saved board id that no longer exists -> first board, with a note ----
out=$("$fetch" --project group/app --board 99)
check "E unknown board" '.board.id == 7 and (.message | test("not found"))' "$out"

# --- D: project without boards -> workflow label fallback -------------------
reset
fx boards <<<'[]'
fx open <<'J'
[{"iid":1,"state":"opened","title":"r","labels":["research"],"web_url":"u"},
 {"iid":2,"state":"opened","title":"t+r","labels":["research","todo"],"web_url":"u"},
 {"iid":3,"state":"opened","title":"ip+rev","labels":["in progress","review"],"web_url":"u"},
 {"iid":4,"state":"opened","title":"none","labels":["api"],"web_url":"u"}]
J
fx closed <<<'[{"iid":5,"state":"closed","title":"c","labels":[],"web_url":"u"}]'
out=$("$fetch" --project 12345)
check "D fallback" '.fallback == true and .board == null and (.message | test("No boards"))' "$out"
check "D mapping" "$cols"' == {"research":[1],"todo":[2],"approved":[],"in progress":[],"review":[3],"Closed":[5],"Unlabeled":[4]}' "$out"

# --- F: projects, boards, issue ---------------------------------------------
fx projects <<<'[{"id":1,"path_with_namespace":"a/b","name_with_namespace":"A / B"},{"id":2,"path_with_namespace":"c/d"}]'
out=$("$fetch" projects)
check "F projects" '.projects == [{"id":1,"path":"a/b"},{"id":2,"path":"c/d"}]' "$out"
check "F projects query" '.' "$(grep -q '^api --hostname gitlab.com --method GET projects?membership=true&simple=true&order_by=last_activity_at&per_page=100&page=1$' "$FAKE_LOG" && echo true || echo false)"
check "F projects: a short page is the last" '.' "$([[ $(grep -c 'GET projects?' "$FAKE_LOG") == 1 ]] && echo true || echo false)"
# Full pages: at most 5 (500 projects), duplicates across pages dropped, order kept.
jq -n '[range(100) | {id: (99 - .), path_with_namespace: "g/p\(99 - .)"}]' | fx projects
: >"$FAKE_LOG"; out=$("$fetch" projects)
check "F projects: at most 5 pages" '.' "$([[ $(grep -c 'GET projects?' "$FAKE_LOG") == 5 ]] && grep -q 'page=5$' "$FAKE_LOG" && echo true || echo false)"
check "F projects: one entry each, in GitLab's order" '(.projects | length) == 100 and .projects[0] == {"id":99,"path":"g/p99"}' "$out"
fx projects <<<'[{"id":1,"path_with_namespace":"a/b","name_with_namespace":"A / B"},{"id":2,"path_with_namespace":"c/d"}]'
fx boards <<<'[{"id":3,"name":"Main","lists":[]}]'
check "F boards" '.boards == [{"id":3,"name":"Main"}]' "$("$fetch" boards --project a/b)"
fx issue <<'J'
{"iid":45,"title":"Bug","state":"opened","labels":["api"],"web_url":"https://x/45","description":"**bold**",
 "author":{"username":"bob"},"milestone":{"title":"M1"},"assignees":[{"username":"ann"},{"username":"cy"}],
 "created_at":"2026-10-27T14:09:17Z","updated_at":"2026-10-27T15:12:15Z"}
J
out=$("$fetch" issue --project a/b --iid 45)
check "F issue" '.issue | .iid == 45 and .author == "bob" and .milestone == "M1" and .assignees == ["ann","cy"] and .description == "**bold**" and .url == "https://x/45"' "$out"
check "F issue endpoint" '.' "$(grep -q 'GET projects/a%2Fb/issues/45$' "$FAKE_LOG" && echo true || echo false)"

# --- H: v1.3 card fields: label colors, assignees, notes, created_at ---------
reset
fx boards <<'J'
[{"id":5,"name":"Flow","lists":[{"id":1,"position":0,"label":{"name":"todo","color":"#428BCA","text_color":"#FFFFFF"}},
  {"id":2,"position":1,"label":{"name":"review","color":"red"}}]}]
J
fx open <<'J'
[{"iid":1,"title":"styled","state":"opened","web_url":"u1","created_at":"2026-10-25T10:00:00Z","user_notes_count":4,
  "labels":[{"id":1,"name":"todo","color":"#428BCA","text_color":"#FFFFFF"},{"id":2,"name":"bug","color":"#d9534f","text_color":"#1F1E24"},
            {"id":3,"name":"odd","color":"javascript:x"}],
  "assignees":[{"username":"ann","name":"Ann Lee","avatar_url":"https://gitlab.com/uploads/a.png"},
               {"username":"cy","name":"Cy","avatar_url":"http://insecure/x.png"},{"username":"dee","avatar_url":null}]},
 {"iid":2,"title":"review me","state":"opened","web_url":"u2","labels":[{"name":"review","color":"#00B140","text_color":"#FFFFFF"}],"assignees":[]}]
J
fx closed <<<'[{"iid":9,"title":"done","state":"closed","web_url":"u9","labels":[{"name":"bug","color":"#d9534f"}],"user_notes_count":1}]'
out=$("$fetch" --project group/app)
check "H labels stay names" '[.columns[] | .issues[] | .labels] == [["todo","bug","odd"],["review"],["bug"]]' "$out"
check "H mapping" "$cols"' == {"Open":[],"todo":[1],"review":[2],"Closed":[9]}' "$out"
check "H label colors" '.labelColors == {"todo":{"color":"#428BCA","textColor":"#FFFFFF"},"bug":{"color":"#d9534f","textColor":null},"review":{"color":"#00B140","textColor":"#FFFFFF"}}' "$out"
check "H column colors" '[.columns[] | .color] == [null,"#428BCA","#00B140",null]' "$out"
check "H card fields" '.columns[1].issues[0] | .createdAt == "2026-10-25T10:00:00Z" and .notes == 4' "$out"
check "H assignees" '.columns[1].issues[0].assignees == [{"username":"ann","name":"Ann Lee","avatar":"https://gitlab.com/uploads/a.png"},{"username":"cy","name":"Cy","avatar":""},{"username":"dee","name":"dee","avatar":""}]' "$out"
check "H defaults" '.columns[2].issues[0] | .notes == 0 and .assignees == [] and .createdAt == null' "$out"
check "H label details requested" '.' "$(grep -c 'with_labels_details=true' "$FAKE_LOG" | grep -qx 2 && echo true || echo false)"

# --- G: validation, auth, failures ------------------------------------------
check "G bad project" '.state == "error"' "$("$fetch" --project 'a/../b')"
check "G bad project 2" '.state == "error"' "$("$fetch" --project 'a b;rm')"
check "G bad board" '.state == "error"' "$("$fetch" --project a/b --board 1x)"
check "G bad iid" '.state == "error"' "$("$fetch" issue --project a/b --iid '1;x')"
check "G logged out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch" --project a/b)"
rm -f "$FAKE_DIR/open.json"; fx boards <<<'[]'
check "G api failure" '.state == "error"' "$("$fetch" --project a/b)"

# --- M: move (the one write) -------------------------------------------------
# Board 7: Open, label lists todo (11) / approved (12), an assignee list (13),
# a list whose label has a comma (14), Closed.
reset
fx board <<'J'
{"id":7,"name":"Dev","hide_backlog_list":false,"hide_closed_list":false,
 "lists":[{"id":11,"position":0,"label":{"name":"todo"}},{"id":12,"position":1,"label":{"name":"approved"}},
          {"id":13,"position":2,"label":null,"assignee":{"username":"alice"}},{"id":14,"position":3,"label":{"name":"a,b"}}]}
J
fx put <<<'{"iid":3,"state":"opened","labels":["approved","app-ui"]}'
at() { jq -cn --arg s "$1" --argjson l "$2" '{iid: 3, state: $s, labels: $l}' | fx issue; }  # issue 3 on GitLab now
mv_() { "$fetch" move --project group/app --board 7 --iid 3 "$@"; }
put() { sed -n 's/^PUT projects\/group%2Fapp\/issues\/3 //p' "$FAKE_LOG" | tail -n1; }
puts() { grep -c '^PUT ' "$FAKE_LOG"; }
body_is() { # name expected-json args...
  local name=$1 want=$2; shift 2; : >"$FAKE_LOG"
  local out; out=$(mv_ "$@")
  check "$name ready" '.state == "ready"' "$out"
  check "$name body" "(. | tojson) == ($want | tojson)" "$(put | jq -cS . 2>/dev/null || echo null)"
}
at opened '["todo","app-ui"]'
body_is "M label->label" '{"add_labels":"approved","remove_labels":"todo"}' --from 11 --to 12
check "M label->label message" '.message == "Moved #3 to approved."' "$(mv_ --from 11 --to 12)"
body_is "M label->closed" '{"state_event":"close"}' --from 11 --to closed
at opened '["app-ui"]'
body_is "M open->label" '{"add_labels":"todo"}' --from open --to 11
body_is "M open->closed" '{"state_event":"close"}' --from open --to closed
at closed '["todo"]'
body_is "M closed->label" '{"add_labels":"todo","state_event":"reopen"}' --from closed --to 11
body_is "M closed->open" '{"state_event":"reopen"}' --from closed --to open
at opened '["approved"]'
body_is "M label->open" '{"remove_labels":"approved"}' --from 12 --to open
at opened '["todo","app-ui"]'
: >"$FAKE_LOG"; mv_ --from 11 --to 12 >/dev/null
check "M GET board, GET issue, then one PUT to the issue" '.' "$(grep '^api ' "$FAKE_LOG" | cut -d' ' -f5,6 | tr '\n' ' ' |
  grep -qx 'GET projects/group%2Fapp/boards/7 GET projects/group%2Fapp/issues/3 PUT --header ' &&
  grep -q '^api --hostname gitlab.com --method PUT --header Content-Type: application/json --input - projects/group%2Fapp/issues/3$' "$FAKE_LOG" &&
  [[ $(puts) == 1 ]] && ! grep -q BAD-WRITE "$FAKE_LOG" && echo true || echo false)"

# Pre-move check: the card may be out of date. If GitLab says the issue is not
# in --from anymore, nothing is written and the answer is state "stale".
stale() { # name state labels args...
  local name=$1; at "$2" "$3"; shift 3; : >"$FAKE_LOG"
  local out; out=$(mv_ "$@")
  check "$name" '.state == "stale" and .message == "#3 changed on GitLab. Board refreshed."' "$out"
  check "$name: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
}
stale "MS label changed elsewhere" opened '["review"]' --from 11 --to 12
stale "MS closed elsewhere" closed '["todo"]' --from 11 --to 12
stale "MS closed elsewhere, from Open" closed '[]' --from open --to 11
stale "MS closed elsewhere, to Closed" closed '["todo"]' --from 11 --to closed
stale "MS reopened elsewhere" opened '["todo"]' --from closed --to 12
stale "MS reopened elsewhere, to Open" opened '[]' --from closed --to open
stale "MS already in the target" opened '["approved"]' --from 11 --to 12
stale "MS left Open for a list" opened '["todo","bug"]' --from open --to 12
stale "MS label objects" opened '[{"name":"review"}]' --from 11 --to 12
at opened '["todo","approved"]'
body_is "MS in both lists: normal swap" '{"add_labels":"approved","remove_labels":"todo"}' --from 11 --to 12
at opened '[{"name":"todo","color":"#428BCA"}]'
body_is "MS label objects in place" '{"add_labels":"approved","remove_labels":"todo"}' --from 11 --to 12
at opened '["bug"]'
body_is "MS Open with other labels" '{"add_labels":"approved"}' --from open --to 12
check "MS issue read failure" '.state == "error" and .message == "Could not load issue #3."' "$(rm -f "$FAKE_DIR/issue.json"; : >"$FAKE_LOG"; mv_ --from 11 --to 12)"
check "MS issue read failure: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
fx issue <<<'{"iid":4,"state":"opened","labels":["todo"]}'
rejects_() { check "$1" '.state == "error"' "$(: >"$FAKE_LOG"; mv_ --from 11 --to 12)"; check "$1: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"; }
rejects_ "MS answer for another issue"
fx issue <<<'not json'
rejects_ "MS unreadable issue"
fx issue <<<'[{"iid":3,"state":"opened","labels":["todo"]}]'
rejects_ "MS issue answer not an object"
at opened '["todo"]'

# Rejections: each must fail before any write.
rejects() { # name args... (expects state error and no PUT)
  local name=$1; shift; : >"$FAKE_LOG"
  local out; out=$("$fetch" move "$@")
  check "$name" '.state == "error"' "$out"
  check "$name: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
}
rejects "MV same list" --project group/app --board 7 --iid 3 --from 11 --to 11
rejects "MV same default list" --project group/app --board 7 --iid 3 --from closed --to closed
rejects "MV into assignee list" --project group/app --board 7 --iid 3 --from 11 --to 13
rejects "MV from assignee list" --project group/app --board 7 --iid 3 --from 13 --to 11
rejects "MV list not on board" --project group/app --board 7 --iid 3 --from 11 --to 99
rejects "MV label with comma" --project group/app --board 7 --iid 3 --from 11 --to 14
rejects "MV iid with ;" --project group/app --board 7 --iid '3;x' --from 11 --to 12
rejects "MV iid empty" --project group/app --board 7 --iid '' --from 11 --to 12
rejects "MV iid negative" --project group/app --board 7 --iid -3 --from 11 --to 12
rejects "MV iid zero" --project group/app --board 7 --iid 0 --from 11 --to 12
rejects "MV iid with newline" --project group/app --board 7 --iid $'3\n4' --from 11 --to 12
rejects "MV no board" --project group/app --iid 3 --from 11 --to 12
rejects "MV board not numeric" --project group/app --board '7&x=1' --iid 3 --from 11 --to 12
rejects "MV bad project" --project 'group/app/../x' --board 7 --iid 3 --from 11 --to 12
rejects "MV project with ?" --project 'group/app?x=1' --board 7 --iid 3 --from 11 --to 12
rejects "MV label name as list" --project group/app --board 7 --iid 3 --from 11 --to approved
rejects "MV label: prefix" --project group/app --board 7 --iid 3 --from 11 --to 'label:approved'
rejects "MV list injection" --project group/app --board 7 --iid 3 --from 11 --to '12,13'
# shellcheck disable=SC2016 # a literal $(id), on purpose
rejects "MV command substitution" --project group/app --board 7 --iid 3 --from 11 --to '$(id)'
rejects "MV @file" --project group/app --board 7 --iid 3 --from 11 --to '@/etc/passwd'
rejects "MV missing to" --project group/app --board 7 --iid 3 --from 11
check "MV injection never ran glab api" '.' "$(: >"$FAKE_LOG"; "$fetch" move --project group/app --board 7 --iid '3;x' --from 11 --to 12 >/dev/null
  grep -q '^api' "$FAKE_LOG" && echo false || echo true)"
check "MV assignee list message" '.message == "Only label lists can be moved between."' "$("$fetch" move --project group/app --board 7 --iid 3 --from 11 --to 13)"
check "MV list injection never ran glab api" '.' "$(: >"$FAKE_LOG"; "$fetch" move --project group/app --board 7 --iid 3 --from 11 --to '12,13' >/dev/null
  grep -q '^api' "$FAKE_LOG" && echo false || echo true)"
fx board <<<'{"id":7,"name":"Dev","hide_backlog_list":true,"hide_closed_list":true,"lists":[{"id":11,"label":{"name":"todo"}}]}'
rejects "MV hidden Closed list" --project group/app --board 7 --iid 3 --from 11 --to closed
rejects "MV hidden Open list" --project group/app --board 7 --iid 3 --from open --to 11
rm -f "$FAKE_DIR/board.json"
rejects "MV board fetch fails" --project group/app --board 7 --iid 3 --from 11 --to 12

# GitLab refuses or answers oddly.
fx board <<<'{"id":7,"name":"Dev","lists":[{"id":11,"label":{"name":"todo"}},{"id":12,"label":{"name":"approved"}}]}'
fx put-error <<<'{"message":"403 Forbidden glpat-LEAKLEAKLEAK Bearer abc.def"}'
out=$(FAKE_PUT=fail mv_ --from 11 --to 12)
check "MF refused" '.state == "error" and (.message | startswith("Move failed: 403 Forbidden"))' "$out"
check "MF refused: token redacted" '.' "$(grep -qiE 'glpat-|LEAK|abc\.def' <<<"$out" && echo false || echo true)"
fx put-error <<<'{"message":{"labels":["is invalid"]}}'
check "MF structured error" '.state == "error" and .message == "Move failed: {\"labels\":[\"is invalid\"]}"' "$(FAKE_PUT=fail mv_ --from 11 --to 12)"
fx put-error <<<'{"message":"two\nlines\u0007 and a bell"}'
check "MF control characters dropped" '.message == "Move failed: twolines and a bell"' "$(FAKE_PUT=fail mv_ --from 11 --to 12)"
rm -f "$FAKE_DIR/put-error.json"
check "MF no body" '.state == "error" and .message == "Move failed"' "$(FAKE_PUT=fail mv_ --from 11 --to 12)"
fx put <<<'{"iid":4,"state":"opened","labels":[]}'
check "MF wrong issue in answer" '.state == "error"' "$(mv_ --from 11 --to 12)"
fx put <<<'not json'
check "MF unreadable answer" '.state == "error"' "$(mv_ --from 11 --to 12)"
check "MF logged out: no write" '.state == "logged-out"' "$(: >"$FAKE_LOG"; FAKE_AUTH=no mv_ --from 11 --to 12)"

# --- N: notes (read) ----------------------------------------------------------
# GitLab answers newest first (sort=desc); system notes are dropped, the rest
# come back oldest first.
reset
fx notes <<'J'
[{"id":5,"body":"newest","system":false,"created_at":"2026-10-27T12:00:00Z","author":{"username":"ann","name":"Ann Lee","avatar_url":"https://gitlab.com/a.png"}},
 {"id":4,"body":"added ~approved label","system":true,"created_at":"2026-10-27T11:00:00Z","author":{"username":"bot"}},
 {"id":3,"body":"middle\nsecond line","system":false,"created_at":"2026-10-27T10:00:00Z","author":{"username":"cy","avatar_url":"http://insecure/c.png"}},
 {"id":2,"body":"changed the description","system":true,"created_at":"2026-10-27T09:00:00Z","author":{"username":"ann"}},
 {"id":1,"body":"oldest","created_at":"2026-10-27T08:00:00Z","author":{"username":"dee","name":"Dee","avatar_url":null}}]
J
out=$("$fetch" notes --project a/b --iid 45)
check "N ready" '.state == "ready" and .iid == 45 and .more == false' "$out"
check "N comments only, oldest first" '[.notes[].id] == [1,3,5]' "$out"
check "N fields" '.notes[2] == {"id":5,"body":"newest","createdAt":"2026-10-27T12:00:00Z","author":{"username":"ann","name":"Ann Lee","avatar":"https://gitlab.com/a.png"}}' "$out"
check "N body kept as is, https avatars only" '.notes[1].body == "middle\nsecond line" and .notes[1].author == {"username":"cy","name":"cy","avatar":""} and .notes[0].author.avatar == ""' "$out"
check "N endpoint" '.' "$(grep -qx 'api --hostname gitlab.com --method GET projects/a%2Fb/issues/45/notes?sort=desc&order_by=created_at&per_page=100' "$FAKE_LOG" && echo true || echo false)"
jq -c '[range(100) | {id: ., body: "n", system: false, created_at: "2026-10-27T08:00:00Z", author: {username: "x"}}]' -n | fx notes
check "N full page flags more" '.more == true and (.notes | length) == 100' "$("$fetch" notes --project a/b --iid 45)"
fx notes <<<'[]'
check "N no comments" '.state == "ready" and .notes == []' "$("$fetch" notes --project a/b --iid 45)"
fx notes <<<'{"message":"404 Not found"}'
check "N unreadable answer" '.state == "error"' "$("$fetch" notes --project a/b --iid 45)"
rm -f "$FAKE_DIR/notes.json"
check "N api failure" '.state == "error" and .message == "Could not load comments."' "$("$fetch" notes --project a/b --iid 45)"
check "N bad iid, no glab" '.state == "error"' "$(: >"$FAKE_LOG"; "$fetch" notes --project a/b --iid '45/../1')"
check "N bad iid ran nothing" '.' "$([[ -s $FAKE_LOG ]] && echo false || echo true)"

# --- P: comment (the POST) ---------------------------------------------------
reset
fx post <<<'{"id":901,"body":"x","system":false,"noteable_iid":45}'
say() { "$fetch" comment --project a/b --iid 45 "$@"; }
posts() { grep -c '^POST ' "$FAKE_LOG"; }
body=$'Looks good.\n\n- "quoted" & <b>\n$(id) `id` @/etc/passwd :id {placeholder} ünïcode\ttab\n'
out=$(printf '%s' "$body" | say)
check "P ready" '.state == "ready" and .message == "Comment posted." and .note == {"id":901}' "$out"
check "P one POST to the notes endpoint, nothing else" '.' "$(grep -c '^api ' "$FAKE_LOG" | grep -qx 1 &&
  grep -qx 'api --hostname gitlab.com --method POST --header Content-Type: application/json --input - projects/a%2Fb/issues/45/notes' "$FAKE_LOG" &&
  [[ $(posts) == 1 ]] && ! grep -q 'BAD-WRITE\|^PUT ' "$FAKE_LOG" && echo true || echo false)"
check "P body arrives on stdin, byte for byte" "(.body == $(jq -Rs . <<<"$body" | jq -c 'sub("\n$"; "")')) and (keys == [\"body\"])" \
  "$(sed -n 's/^POST projects\/a%2Fb\/issues\/45\/notes //p' "$FAKE_LOG")"
check "P body never on a glab command line" '.' "$(grep -v '^POST ' "$FAKE_LOG" | grep -q 'Looks good' && echo false || echo true)"
nothing_ran() { # name stdin args... (expects state error and no glab call at all)
  local name=$1 in=$2; shift 2; rm -f "$FAKE_LOG"
  local out; out=$(printf '%s' "$in" | say "$@")
  check "$name" '.state == "error"' "$out"
  check "$name: no glab call" '.' "$([[ -s $FAKE_LOG ]] && echo false || echo true)"
}
nothing_ran "P empty body" ''
nothing_ran "P whitespace body" $' \n\t \r\n  '
check "P empty message" '.message == "Comment is empty."' "$(say </dev/null)"
# Quick actions: GitLab runs a line starting with / (/close, /label ~x, /move)
# instead of posting it, so such a comment is never sent.
nothing_ran "P quick action" '/close'
nothing_ran "P quick action after text" $'Looks good\n/label ~review'
nothing_ran "P quick action, indented" $'ok\n  \t/unlabel ~"in progress"'
nothing_ran "P quick action after a carriage return" $'ok\r/close'
check "P quick action message" '.message | test("starts with /")' "$(printf '/close' | say)"
fx post <<<'{"id":901,"body":"x"}'
check "P a / inside a line or in backticks is fine" '.state == "ready"' "$(printf '%s\n%s' 'see a/b and /usr' "\`/close\`" | say)"
nothing_ran "P bad iid" 'hi' --iid '45;x'
nothing_ran "P bad project" 'hi' --project 'a/../b'
fx post-error <<<'{"message":"403 Forbidden glpat-LEAKLEAKLEAK Bearer abc.def"}'
out=$(echo hi | FAKE_POST=fail say)
check "PF refused" '.state == "error" and (.message | startswith("Comment failed: 403 Forbidden"))' "$out"
check "PF refused: token redacted" '.' "$(grep -qiE 'glpat-|LEAK|abc\.def' <<<"$out" && echo false || echo true)"
rm -f "$FAKE_DIR/post-error.json"
check "PF no body" '.message == "Comment failed"' "$(echo hi | FAKE_POST=fail say)"
fx post <<<'{"message":"odd"}'
check "PF unexpected answer" '.state == "error"' "$(echo hi | say)"
fx post <<<'{"commands_changes":{"state_event":"close"},"summary":["Closed this issue."]}'
check "PF quick actions ran anyway: said so" '.state == "commands" and (.message | test("quick actions"))' "$(echo hi | say)"
: >"$FAKE_LOG"
check "PF logged out: no write" '.state == "logged-out"' "$(echo hi | FAKE_AUTH=no say)"
check "PF logged out: no POST" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"

# --- W: one list of workflow labels on each side ----------------------------
check "W board-fetch and Logic.js list the same workflow labels" '.' "$(
  a=$(jq -cn "$(sed -n 's/^def workflow: \(.*\);$/\1/p' "$fetch") | sort")
  b=$(node -e 'console.log(JSON.stringify(require(process.argv[1]).workflowLabels.slice().sort()))' "$here/../Logic.js")
  [[ -n $a && $a == "$b" ]] && echo true || echo false)"

# --- R: reads are GET only ---------------------------------------------------
# Runtime: every read command, including a refresh with a board, issues only
# GETs. Structure: board-fetch reads only through get() and peek() (both
# --method GET), and has exactly four non-GET requests: the PUTs in
# write_issue() (move only), write_labels() (relabel only) and write_state()
# (close and reopen only), and the POST in write_note() (comment only).
reset
fx boards <<<'[{"id":7,"name":"Dev","lists":[{"id":11,"position":0,"label":{"name":"todo"}}]}]'
fx open <<<'[{"iid":1,"title":"a","state":"opened","labels":["todo"],"web_url":"u"}]'
fx closed <<<'[]'
fx projects <<<'[{"id":1,"path_with_namespace":"a/b"}]'
fx issue <<<'{"iid":1,"title":"a","state":"opened","labels":[],"web_url":"u"}'
fx notes <<<'[{"id":1,"body":"b","system":false,"author":{"username":"x"}}]'
reads=$("$fetch" --project group/app; "$fetch" board --project group/app --board 7; "$fetch" projects; "$fetch" boards --project a/b; "$fetch" issue --project a/b --iid 1; "$fetch" notes --project a/b --iid 1; "$fetch" whoami
  fx labels <<<'[{"name":"bug","color":"#ff0000"}]'; "$fetch" labels --project a/b)
check "R refresh has listId" '.columns[1] | .name == "todo" and .listId == 11' "$("$fetch" --project group/app)"
check "R reads ran" '.' "$(grep -c '^api ' "$FAKE_LOG" | grep -qxE '[0-9]{2,}' && echo true || echo false)"
check "R reads are GET only" '.' "$(grep -q 'NON-GET' "$FAKE_LOG" && echo false || echo true)"
check "R every api call says --method GET" '.' "$(grep '^api ' "$FAKE_LOG" | grep -qv -- '--method GET ' && echo false || echo true)"
src=$(grep -v '^ *#' "$fetch")
check "R non-GETs in the script: three PUTs, one POST" '.' "$(grep -oE -- '--method [A-Z]+' <<<"$src" | sort | tr '\n' ' ' | grep -qx -- '--method GET --method GET --method POST --method PUT --method PUT --method PUT ' && echo true || echo false)"
# shellcheck disable=SC2016  # the pattern is literal board-fetch source
check "R peek() is GET" '.' "$(grep -qxF 'peek() { bounded api --hostname "$hostname" --method GET "$@"; }' <<<"$src" && echo true || echo false)"
# shellcheck disable=SC2016  # the pattern is literal board-fetch source
check "R glab runs only in bounded(), under timeout" '.' "$(grep -E '(^|[^-])\<glab "' <<<"$src" | grep -qvF '  { timeout -k 5 30 glab "$@"; } 2>"${errors:-/dev/null}"' && echo false ||
  grep -c 'timeout -k 5 30 glab' <<<"$src" | grep -qx 1 && echo true || echo false)"
check "R glab api only in get(), peek(), write_issue(), write_labels(), write_state(), write_note() and the one GraphQL query" '.' "$(grep -c 'bounded api' <<<"$src" | grep -qx 7 && echo true || echo false)"
# shellcheck disable=SC2016  # the pattern is literal board-fetch source
check "R the GraphQL call sends a constant query, the project only as a variable" '.' "$(grep 'bounded api' <<<"$src" | grep -c ' graphql ' | grep -qx 1 &&
  grep -qF 'bounded api --hostname "$hostname" graphql -f "query=$q" "${pv[@]}"' <<<"$src" && ! grep -qiE 'mutation|subscription' <<<"$src" && echo true || echo false)"
check "R write_issue only inside move" '.' "$(awk '/^  move\)/{m=1} /^    exit 0 ;;/{if(m)m=2} /write_issue/{if(m!=1)bad=1} END{print bad?"false":"true"}' <<<"$src")"
check "R move: issue read, then stale exit, then the PUT" '.' "$(awk '/^  move\)/{m=1} /^    exit 0 ;;/{if(m==1)m=2}
  m==1 && /get "\$base\/issues\/\$iid"/{g=NR} m==1 && /emit stale/{st=NR} m==1 && /\| write_issue/{w=NR}
  END{print (g && st && w && g < st && st < w) ? "true" : "false"}' <<<"$src")"
check "R write_labels only inside relabel" '.' "$(awk '/^  relabel\)/{m=1} /^    exit 0 ;;/{if(m)m=2} /write_labels/{if(m!=1)bad=1} END{print bad?"false":"true"}' <<<"$src")"
check "R relabel: status guard, then the PUT" '.' "$(awk '/^  relabel\)/{m=1} /^    exit 0 ;;/{if(m==1)m=2}
  m==1 && /is a board list label/{g=NR} m==1 && /\| write_labels/{w=NR} END{print (g && w && g < w) ? "true" : "false"}' <<<"$src")"
check "R write_state only inside close|reopen" '.' "$(awk '/^  close\|reopen\)/{m=1} /^    exit 0 ;;/{if(m)m=2} /write_state/{if(m!=1)bad=1} END{print bad?"false":"true"}' <<<"$src")"
check "R write_note only inside comment" '.' "$(awk '/^  comment\)/{m=1} /^    exit 0 ;;/{if(m)m=2} /write_note/{if(m!=1)bad=1} END{print bad?"false":"true"}' <<<"$src")"
check "R stdin is read only for comment" '.' "$(: >"$FAKE_LOG"; echo '{"body":"x"}' | "$fetch" notes --project a/b --iid 1 >/dev/null; grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"

# --- T: a glab call that never answers ends with a clear message ------------
# FAKE_HANG: a glab call whose arguments contain it sleeps; FAKE_HANG_TERM=ignore
# makes it ignore the TERM, so only the KILL 1 s later ends it (exit 137).
reset
fx board <<<'{"id":7,"name":"Dev","lists":[{"id":11,"label":{"name":"todo"}},{"id":12,"label":{"name":"approved"}}]}'
at opened '["todo"]'
slow='.state == "error" and .message == "GitLab did not answer within 30 seconds."'
check "T auth hangs" "$slow" "$(FAKE_HANG='auth status' "$fetch" --project a/b)"
check "T board read hangs" "$slow" "$(FAKE_HANG='/boards?' "$fetch" --project a/b)"
check "T read ignores TERM, killed" "$slow" "$(FAKE_HANG='/boards?' FAKE_HANG_TERM=ignore "$fetch" --project a/b)"
check "T issue read hangs" "$slow" "$(FAKE_HANG='issues/45' "$fetch" issue --project a/b --iid 45)"
check "T move PUT hangs" '.state == "error" and (.message | test("move may have gone through"))' "$(FAKE_HANG='--method PUT' mv_ --from 11 --to 12)"
check "T comment POST hangs" '.state == "timeout" and (.message | test("may have been posted"))' "$(echo hi | FAKE_HANG='--method POST' say)"
check "T comment POST killed" '.state == "timeout"' "$(echo hi | FAKE_HANG='--method POST' FAKE_HANG_TERM=ignore say)"
check "T relabel PUT hangs" '.state == "error" and (.message | test("label change may have gone through"))' "$(fx labels <<<'[{"name":"bug"}]'; fx boards <<<'[]'; FAKE_HANG='--method PUT' "$fetch" relabel --project a/b --iid 3 --add bug)"
check "T close PUT hangs" '.state == "error" and .message == "GitLab did not answer within 30 seconds. The issue may have been closed."' "$(FAKE_HANG='--method PUT' "$fetch" close --project a/b --iid 3)"
check "T close PUT killed" '.state == "error" and (.message | test("may have been closed"))' "$(FAKE_HANG='--method PUT' FAKE_HANG_TERM=ignore "$fetch" close --project a/b --iid 3)"
check "T one JSON line each" '.' "$(n=$(echo hi | FAKE_HANG='--method POST' say | wc -l); m=$(FAKE_HANG='--method PUT' mv_ --from 11 --to 12 | wc -l)
  [[ $n == 1 && $m == 1 ]] && echo true || echo false)"

# --- D: one deadline per command (BOARD_FETCH_DEADLINE, default 40 s) ----------
# Each glab call gets at most what is left of it (the limits the timeout
# stand-in logs), and a write starts only with 15 s left: else nothing is sent.
reset
fx board <<<'{"id":7,"name":"Dev","lists":[{"id":11,"label":{"name":"todo"}},{"id":12,"label":{"name":"approved"}}]}'
at opened '["todo"]'
echo '{"iid":3,"state":"opened","labels":["approved"]}' | fx put
limits() { tr '\n' ' ' <"$FAKE_LOG.limits" 2>/dev/null; }
lim_ok() { # max min: every limit within [min, max]
  local l; while IFS= read -r l; do ((l <= $1 && l >= $2)) || return 1; done <"$FAKE_LOG.limits"; [[ -s $FAKE_LOG.limits ]]
}
rm -f "$FAKE_LOG" "$FAKE_LOG.limits"; out=$(mv_ --from 11 --to 12)
check "D default: the move goes through, every call at most 30 s" '.state == "ready"' "$out"
check "D default limits are 30 ($(limits))" '.' "$(lim_ok 30 30 && echo true || echo false)"
rm -f "$FAKE_LOG" "$FAKE_LOG.limits"; out=$(BOARD_FETCH_DEADLINE=25 mv_ --from 11 --to 12)
check "D a 25 s deadline: calls get what is left ($(limits))" '.' "$(lim_ok 25 22 && echo true || echo false)"
check "D a 25 s deadline: the write still starts (15 s left)" '.state == "ready"' "$out"
for bad in abc 5 500 -3 ''; do
  rm -f "$FAKE_LOG.limits"; BOARD_FETCH_DEADLINE=$bad "$fetch" --project group/app >/dev/null
  check "D deadline '$bad' ignored: 40 s ($(limits))" '.' "$(lim_ok 30 30 && echo true || echo false)"
done
refused='.state == "error" and (.message | test("Nothing was written"))'
nowrite() { [[ $(grep -c NON-GET "$FAKE_LOG") == 0 ]] && echo true || echo false; }
rm -f "$FAKE_LOG"; out=$(BOARD_FETCH_DEADLINE=10 mv_ --from 11 --to 12)
check "D move with under 15 s left: refused" "$refused" "$out"
check "D move refused: no write" '.' "$(nowrite)"
check "D move refused: the reads ran" '.' "$([[ $(grep -c -- '--method GET' "$FAKE_LOG") == 2 ]] && echo true || echo false)"
rm -f "$FAKE_LOG"; out=$(BOARD_FETCH_DEADLINE=10 "$fetch" close --project a/b --iid 3)
check "D close with under 15 s left: refused, no write" "$refused" "$out"; check "D close: no write" '.' "$(nowrite)"
rm -f "$FAKE_LOG"; out=$(echo hi | BOARD_FETCH_DEADLINE=10 say)
check "D comment with under 15 s left: refused" "$refused" "$out"; check "D comment: no write" '.' "$(nowrite)"
fx labels <<<'[{"name":"bug"}]'; fx boards <<<'[]'
rm -f "$FAKE_LOG"; out=$(BOARD_FETCH_DEADLINE=10 "$fetch" relabel --project a/b --iid 3 --add bug)
check "D relabel with under 15 s left: refused" "$refused" "$out"; check "D relabel: no write" '.' "$(nowrite)"

# --- R: the private temp dir --------------------------------------------------
# In XDG_RUNTIME_DIR when it is a usable absolute dir, else TMPDIR (or /tmp);
# gone when board-fetch ends, also when it is stopped with TERM.
reset
fx board <<<'{"id":7,"name":"Dev","lists":[]}'
mkdir -p "$work/rt" "$work/tmpd"
(FAKE_HANG='/boards?' XDG_RUNTIME_DIR="$work/rt" "$fetch" --project a/b >/dev/null) & rpid=$!
sleep 0.4; during=$(find "$work/rt" -maxdepth 1 -name 'board-fetch.*' -type d | wc -l)
mode=$(stat -c %a "$work"/rt/board-fetch.* 2>/dev/null)
wait $rpid
check "R temp dir in XDG_RUNTIME_DIR while it runs, mode 700" '.' "$([[ $during == 1 && $mode == 700 ]] && echo true || echo false)"
check "R gone after" '.' "$([[ -z $(find "$work/rt" -mindepth 1 -name "board-fetch.*") ]] && echo true || echo false)"
FAKE_HANG='/boards?' XDG_RUNTIME_DIR="$work/rt" "$fetch" --project a/b >/dev/null & rpid=$!
sleep 0.4; kill -TERM $rpid; wait $rpid; rc=$?
check "R stopped with TERM: exits 143, temp dir gone" '.' "$([[ $rc == 143 && -z $(find "$work/rt" -mindepth 1 -name "board-fetch.*") ]] && echo true || echo false)"
for rt in rel/dir "$work/missing" ''; do
  (FAKE_HANG='/boards?' XDG_RUNTIME_DIR=$rt TMPDIR="$work/tmpd" "$fetch" --project a/b >/dev/null) & rpid=$!
  sleep 0.4; n=$(find "$work/tmpd" -maxdepth 1 -name 'board-fetch.*' | wc -l); wait $rpid
  check "R XDG_RUNTIME_DIR '$rt' unusable: TMPDIR, cleaned" '.' "$([[ $n == 1 && -z $(ls -A "$work/tmpd") ]] && echo true || echo false)"
done

# --- U: GitLab values that must not pass through ------------------------------
# Issue links: https only, so no file:, javascript: or --flag reaches the
# browser. Board scope: a non-numeric assignee id adds no query parameter.
reset
fx boards <<<'[{"id":7,"name":"Dev","assignee":{"id":"1&x=y"},"lists":[]}]'
fx open <<'J'
[{"iid":1,"title":"a","state":"opened","labels":[],"web_url":"--gpu-launcher=touch /tmp/pwn"},
 {"iid":2,"title":"b","state":"opened","labels":[],"web_url":"file:///etc/passwd"},
 {"iid":3,"title":"c","state":"opened","labels":[],"web_url":"javascript:alert(1)"},
 {"iid":4,"title":"d","state":"opened","labels":[],"web_url":"http://gitlab.com/a/b/-/issues/4"},
 {"iid":5,"title":"e","state":"opened","labels":[],"web_url":"https://gitlab.com/a/b/-/issues/5"}]
J
fx closed <<<'[]'
out=$("$fetch" --project a/b)
check "U card links https only" '[.columns[0].issues[] | .url] == ["","","","","https://gitlab.com/a/b/-/issues/5"]' "$out"
check "U string assignee id dropped" '.' "$(grep 'state=opened' "$FAKE_LOG" | grep -q 'assignee_id\|x=y' && echo false || echo true)"
for u in '--gpu-launcher=touch /tmp/pwn' 'file:///etc/passwd' 'javascript:alert(1)'; do
  jq -cn --arg u "$u" '{iid: 9, title: "x", state: "opened", web_url: $u}' | fx issue
  check "U issue link dropped: $u" '.state == "ready" and .issue.url == ""' "$("$fetch" issue --project a/b --iid 9)"
done

# --- V: first run: no project, no glab, not signed in ---------------------------
reset
fx projects <<<'[{"id":1,"path_with_namespace":"a/b"}]'
check "V no project: board refused before glab" '.state == "error" and (.message | test("No project"))' "$(: >"$FAKE_LOG"; "$fetch")"
check "V no project: no glab call" '.' "$([[ -s $FAKE_LOG ]] && echo false || echo true)"
check "V projects needs no project" '.state == "ready" and .projects == [{"id":1,"path":"a/b"}]' "$("$fetch" projects)"
for a in no none 401; do
  check "V signed out ($a): logged-out" '.state == "logged-out" and (.message | test("glab auth login"))' "$(FAKE_AUTH=$a "$fetch" projects)"
done
check "V a 401 in the host name is not a sign-in prompt" '.state == "error"' "$(FAKE_AUTH=offline401 "$fetch" projects --hostname git401lab.example)"
check "V offline is an error, not a sign-in prompt" '.state == "error" and (.message | test("connection"))' "$(FAKE_AUTH=offline "$fetch" projects)"
check "V auth message never passed through" '.' "$(FAKE_AUTH=offline "$fetch" projects | grep -q 'dial tcp\|glpat' && echo false || echo true)"
: >"$FAKE_LOG"; FAKE_AUTH=no "$fetch" --project a/b >/dev/null
check "V signed out: only the auth check ran" '.' "$([[ $(grep -c . "$FAKE_LOG") == 1 ]] && grep -q '^auth status --hostname gitlab.com$' "$FAKE_LOG" && echo true || echo false)"
# glab missing: a PATH with only the tools board-fetch needs.
mkdir -p "$work/noglab"
for t in jq mktemp rm cat grep timeout mkdir chmod mv cp; do ln -sf "$(command -v "$t")" "$work/noglab/$t"; done
noglab() { PATH="$work/noglab" "$BASH" "$fetch" "$@"; }
check "V no glab: no-glab state" '.state == "no-glab" and (.message | test("not installed"))' "$(noglab projects)"
check "V no glab, board too" '.state == "no-glab"' "$(noglab --project a/b)"
check "V no glab: cached still reads" '.state == "none"' "$(noglab cached --project x/never)"

# --- A: account: who is signed in, and signing out ------------------------------
reset
fx user <<<'{"id":5,"username":"dev1","name":"Dev One","email":"dev1@example.com","private_token":"glpat-SECRET"}'
out=$(: >"$FAKE_LOG"; "$fetch" whoami)
check "A whoami: the username only" '. == {state: "ready", message: "", user: "dev1"}' "$out"
check "A whoami: one GET of /user after the auth check" '.' "$([[ $(sed -n 2p "$FAKE_LOG") == 'api --hostname gitlab.com --method GET user' && $(grep -c . "$FAKE_LOG") == 2 ]] && echo true || echo false)"

# --- E: the sign-in check (glab auth status, one GET /user) at most every 10 min
# A passed check leaves a mark in XDG_RUNTIME_DIR (the time, nothing else);
# while it is fresh the check is skipped; a failed read runs it again.
ert="$work/ert"; mkdir -p "$ert"; chmod 700 "$ert"; mark="$ert/odevvy.gitlab-board-auth-gitlab.com"
auths() { grep -c '^auth status' "$FAKE_LOG"; }
: >"$FAKE_LOG"; out=$(XDG_RUNTIME_DIR=$ert "$fetch" whoami)
check "E first run: checked, mark left" '.user == "dev1"' "$out"
check "E the mark holds only the time" '.' "$([[ $(auths) == 1 && $(<"$mark") =~ ^[0-9]+$ ]] && ! grep -q 'glpat\|FAKE\|dev1' "$mark" && echo true || echo false)"
: >"$FAKE_LOG"; out=$(XDG_RUNTIME_DIR=$ert "$fetch" whoami)
check "E fresh mark: no auth check, one GET" '.user == "dev1"' "$out"
check "E fresh mark: the log is the GET only" '.' "$([[ $(auths) == 0 && $(grep -c . "$FAKE_LOG") == 1 ]] && echo true || echo false)"
echo $((EPOCHSECONDS - 700)) >"$mark"; : >"$FAKE_LOG"; XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null
check "E mark older than 10 min: checked again, renewed" '.' "$([[ $(auths) == 1 && $(<"$mark") -ge $((EPOCHSECONDS - 5)) ]] && echo true || echo false)"
echo $((EPOCHSECONDS + 900)) >"$mark"; : >"$FAKE_LOG"; XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null
check "E mark from the future: checked" '.' "$([[ $(auths) == 1 ]] && echo true || echo false)"
rm -f "$mark"; echo "$EPOCHSECONDS" >"$work/elsewhere"; ln -s "$work/elsewhere" "$mark"; : >"$FAKE_LOG"; XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null
check "E a symlinked mark is ignored" '.' "$([[ $(auths) == 1 ]] && echo true || echo false)"
rm -f "$mark"; echo "x$EPOCHSECONDS" >"$mark"; : >"$FAKE_LOG"; XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null
check "E a garbled mark is ignored" '.' "$([[ $(auths) == 1 ]] && echo true || echo false)"
# Signed out in the terminal while the mark is fresh: the read fails, the check runs, logged-out.
XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null; mv "$FAKE_DIR/user.json" "$FAKE_DIR/user.off"; : >"$FAKE_LOG"
out=$(FAKE_AUTH=no XDG_RUNTIME_DIR=$ert "$fetch" whoami)
check "E fresh mark, read fails, signed out: logged-out" '.state == "logged-out"' "$out"
check "E ... the check ran once and the mark is gone" '.' "$([[ $(auths) == 1 && ! -e $mark ]] && echo true || echo false)"
XDG_RUNTIME_DIR=$ert "$fetch" whoami >/dev/null; : >"$FAKE_LOG"
out=$(XDG_RUNTIME_DIR=$ert "$fetch" whoami)
check "E fresh mark, read fails, still signed in: the read's own error" '.state == "error" and (.message | test("sign-in") | not)' "$out"
check "E ... checked once, mark renewed" '.' "$([[ $(auths) == 1 && -f $mark ]] && echo true || echo false)"
mv "$FAKE_DIR/user.off" "$FAKE_DIR/user.json"
XDG_RUNTIME_DIR=$ert "$fetch" logout >/dev/null
check "E sign out clears the mark" '.' "$([[ ! -e $mark ]] && echo true || echo false)"
: >"$FAKE_LOG"; "$fetch" whoami >/dev/null; "$fetch" whoami >/dev/null
check "E no XDG_RUNTIME_DIR: no mark, checked every run" '.' "$([[ $(auths) == 2 ]] && echo true || echo false)"
: >"$FAKE_LOG"; XDG_RUNTIME_DIR=$ert FAKE_AUTH=offline "$fetch" whoami >/dev/null
check "E a failed check leaves no mark" '.' "$([[ ! -e $mark ]] && echo true || echo false)"
check "A whoami: signed out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch" whoami)"
fx user <<<'{"message":"500 Internal Server Error"}'
check "A whoami: no username is an error" '.state == "error"' "$("$fetch" whoami)"
fx user <<<'{"username":"dev1"}'
rm -rf "$XDG_CACHE_HOME"; "$fetch" whoami >/dev/null
check "A whoami: nothing saved" '.' "$([[ -e $XDG_CACHE_HOME ]] && echo false || echo true)"
fx boards <<<'[{"id":7,"name":"Dev","lists":[]}]'; fx open <<<'[]'; fx closed <<<'[]'
"$fetch" --project group/app --board 7 >/dev/null
adir=$XDG_CACHE_HOME/odevvy.gitlab-board
check "A (a saved board exists)" '.' "$([[ -n $(find "$adir" -name '*.json') ]] && echo true || echo false)"
out=$(: >"$FAKE_LOG"; FAKE_LOGOUT=fail "$fetch" logout)
check "A logout failure: error, saved boards kept" '.state == "error"' "$out"
check "A logout failure: cache still there" '.' "$([[ -d $adir ]] && echo true || echo false)"
out=$(: >"$FAKE_LOG"; FAKE_AUTH=offline "$fetch" logout)
check "A logout: logged-out, works offline" '.state == "logged-out" and (.message | test("Signed out of gitlab.com"))' "$out"
check "A logout: exactly glab auth logout --hostname, no API call" '.' "$([[ $(cat "$FAKE_LOG") == 'auth logout --hostname gitlab.com' ]] && echo true || echo false)"
check "A logout: saved boards deleted" '.' "$([[ -e $adir ]] && echo false || echo true)"
: >"$FAKE_LOG"; "$fetch" logout --hostname gitlab.example.com >/dev/null
check "A logout: the given host" '.' "$(grep -qx 'auth logout --hostname gitlab.example.com' "$FAKE_LOG" && echo true || echo false)"
check "A logout: no glab" '.state == "no-glab"' "$(PATH="$work/noglab" "$BASH" "$fetch" logout)"
check "A logout: no cache dir known, still signs out" '.state == "logged-out"' "$(env -u XDG_CACHE_HOME HOME= "$fetch" logout)"
mkdir -p "$adir"; touch "$adir/x.json"
check "A logout: hung glab is an error, cache kept" '.state == "error"' "$(FAKE_HANG='auth logout' "$fetch" logout)"
check "A (cache kept after the hang)" '.' "$([[ -e $adir/x.json ]] && echo true || echo false)"

# --- K: saved board (cache) --------------------------------------------------
# Each board answer is saved per project and board; `cached` reads it back
# with no glab call. Unreadable or foreign copies read as state "none".
reset
fx boards <<<'[{"id":7,"name":"Dev","lists":[{"id":11,"position":0,"label":{"name":"todo"}}]},{"id":8,"name":"Ops","lists":[]}]'
fx open <<<'[{"iid":1,"title":"a","state":"opened","labels":["todo"],"web_url":"https://x/1"}]'
fx closed <<<'[]'
kdir=$XDG_CACHE_HOME/odevvy.gitlab-board; kfile=$kdir/group%2Fapp-7@me.json
rm -rf "$XDG_CACHE_HOME"
out=$("$fetch" --project group/app --board 7)
check "K saved as printed" '.' "$([[ -f $kfile && $(cat "$kfile") == "$out" ]] && echo true || echo false)"
check "K modes: dir 700, file 600, no temp left" '.' "$([[ $(stat -c %a "$kdir") == 700 && $(stat -c %a "$kfile") == 600 && $(find "$kdir" -mindepth 1 | wc -l) == 1 ]] && echo true || echo false)"
: >"$FAKE_LOG"
cached=$(FAKE_AUTH=no "$fetch" cached --project group/app --board 7)
check "K read back, marked cached" "(del(.cached) | tojson) == ($out | tojson) and .cached == true and .state == \"ready\"" "$cached"
check "K read: no GitLab call, even signed out; only glab's local account lookup" '.' "$([[ $(cat "$FAKE_LOG") == "config get user --host gitlab.com" ]] && echo true || echo false)"
check "K other board: none" '. == {"state":"none"}' "$("$fetch" cached --project group/app --board 8)"
check "K other project: none" '. == {"state":"none"}' "$("$fetch" cached --project group/other --board 7)"
"$fetch" --project group/app >/dev/null
check "K no board id: its own copy" '.cached == true and .board.id == 7' "$("$fetch" cached --project group/app)"
check "K first-board file" '.' "$([[ -f $kdir/group%2Fapp-first@me.json ]] && echo true || echo false)"
"$fetch" --project 12345 --board 8 >/dev/null
check "K numeric project" '.cached == true and .board.id == 8 and .project == "12345"' "$("$fetch" cached --project 12345 --board 8)"
cp "$kfile" "$kdir/group%2Fx-7@me.json"
check "K copy for another project: none" '. == {"state":"none"}' "$("$fetch" cached --project group/x --board 7)"
printf '{"state":"ready","proj' >"$kdir/group%2Fx-7@me.json"
check "K corrupt: none" '. == {"state":"none"}' "$("$fetch" cached --project group/x --board 7)"
printf '%s\n%s\n' "$out" "$out" >"$kdir/group%2Fx-7@me.json"
check "K two objects: none" '. == {"state":"none"}' "$("$fetch" cached --project group/x --board 7)"
echo '{"state":"error","message":"x","project":"group/x"}' >"$kdir/group%2Fx-7@me.json"
check "K error answer: none" '. == {"state":"none"}' "$("$fetch" cached --project group/x --board 7)"
chmod 000 "$kfile"
[[ -r $kfile ]] || check "K unreadable: none" '. == {"state":"none"}' "$("$fetch" cached --project group/app --board 7)"
chmod 600 "$kfile"
check "K bad project still refused" '.state == "error"' "$("$fetch" cached --project 'a/../b')"
before=$(cat "$kfile"); rm -f "$FAKE_DIR/open.json"
check "K failed fetch: error" '.state == "error"' "$("$fetch" --project group/app --board 7)"
check "K failed fetch keeps the old copy" '.' "$([[ $(cat "$kfile") == "$before" ]] && echo true || echo false)"
fx open <<<'[{"iid":2,"title":"b","state":"opened","labels":[],"web_url":"https://x/2"}]'
out=$("$fetch" --project group/app --board 7)
check "K fresh answer replaces the copy" '.columns[0].issues[0].iid == 2' "$(cat "$kfile")"
chmod 755 "$kdir"; "$fetch" --project group/app --board 7 >/dev/null
check "K dir mode restored to 700" '.' "$([[ $(stat -c %a "$kdir") == 700 ]] && echo true || echo false)"
rm -rf "$XDG_CACHE_HOME"; : >"$XDG_CACHE_HOME"  # a file where the dir should be
check "K cache not writable: board still ready" '.state == "ready" and .columns[0].issues[0].iid == 2' "$("$fetch" --project group/app --board 7)"
rm -f "$XDG_CACHE_HOME"
mkdir -p "$work/home"
check "K XDG_CACHE_HOME unset: ~/.cache" '.' "$(XDG_CACHE_HOME='' HOME="$work/home" "$fetch" --project group/app --board 7 >/dev/null
  [[ -f $work/home/.cache/odevvy.gitlab-board/group%2Fapp-7@me.json ]] && echo true || echo false)"
check "K relative XDG_CACHE_HOME ignored" '.' "$(cd "$work" && XDG_CACHE_HOME=rel HOME="$work/home2" "$fetch" --project group/app --board 7 >/dev/null
  [[ ! -e $work/rel && -f $work/home2/.cache/odevvy.gitlab-board/group%2Fapp-7@me.json ]] && echo true || echo false)"
# Saved per account (glab config get user): another account never sees it.
rm -rf "$XDG_CACHE_HOME"; out=$("$fetch" --project group/app --board 7)
check "K other account: none" '. == {"state":"none"}' "$(FAKE_USER=someone "$fetch" cached --project group/app --board 7)"
check "K same account: its copy" '.cached == true' "$("$fetch" cached --project group/app --board 7)"
FAKE_USER=none "$fetch" --project group/app --board 7 >/dev/null
check "K no saved account: its own 'unknown' copy" '.' "$([[ -f $kdir/group%2Fapp-7@unknown.json ]] && echo true || echo false)"
check "K unknown account doesn't read a named one" '.cached == true and (input | . == {"state":"none"})' "$(FAKE_USER=none "$fetch" cached --project group/app --board 7; FAKE_USER=x "$fetch" cached --project group/app --board 7)"
for odd in '../x' 'a b' 'ü'; do
  rm -f "$kdir/group%2Fapp-7@unknown.json"
  check "K odd account name ($odd): unknown" '.' "$(FAKE_USER=$odd "$fetch" --project group/app --board 7 >/dev/null; [[ -f $kdir/group%2Fapp-7@unknown.json && ! -e $kdir/../x.json && $(find "$kdir" -name '*x*' -o -name '* *' | wc -l) == 0 ]] && echo true || echo false)"
done
echo "$out" >"$kdir/group%2Fapp-7.json"
"$fetch" --project group/app --board 7 >/dev/null
check "K the copy from before accounts is removed, never read" '.' "$([[ ! -e $kdir/group%2Fapp-7.json ]] && echo true || echo false)"
saved=("$work"/home*/.cache/odevvy.gitlab-board/*)
check "K no token in any saved copy" '.' "$([[ ${#saved[@]} == 2 && -f ${saved[0]} ]] && ! grep -qiE 'glpat|bearer' "${saved[@]}" && echo true || echo false)"

# --- L: labels: read the editable ones, add or remove one at a time ------------
# Status labels never show and are never written: every board's list labels
# (here "Doing" on board 7, "Ready" on board 8) plus the workflow labels, in any
# case ("In Progress"). A write is one add_labels or remove_labels PUT.
reset
fx boards <<'J'
[{"id":7,"name":"Dev","lists":[{"id":1,"label":{"name":"Doing"}},{"id":2,"assignee":{"username":"a"}}]}]
[{"id":8,"name":"Ops","lists":[{"id":3,"label":{"name":"Ready"}}]}]
J
fx labels <<'J'
[{"name":"ux","color":"#00ff00","text_color":"#000000"},{"name":"Doing","color":"#111111"},{"name":"todo"},{"name":"In Progress"}]
[{"name":"Bug","color":"#ff0000","text_color":"#FFFFFF"},{"name":"Ready"},{"name":"api","color":"red; x","text_color":"#12345"}]
J
fx put <<<'{"iid":3,"state":"opened","labels":["Doing","api","ux"]}'
out=$("$fetch" labels --project a/b)
check "L editable labels: status ones filtered out, sorted" '.state == "ready" and [.labels[].name] == ["api","Bug","ux"]' "$out"
check "L colors kept" '.labels[2] == {"name":"ux","color":"#00ff00","textColor":"#000000"}' "$out"
check "L colors: only #rrggbb passes" '.labels[0] == {"name":"api","color":null,"textColor":null}' "$out"
check "L status list: every board's list labels + workflow labels" '.status == (["approved","doing","in progress","ready","research","review","todo"])' "$out"
check "L labels read is GET only, all pages" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || grep -qF -- '--method GET --paginate projects/a%2Fb/labels?per_page=100' "$FAKE_LOG" && echo true || echo false)"
rl() { : >"$FAKE_LOG"; "$fetch" relabel --project a/b --iid 3 "$@"; }
out=$(rl --add api)
check "L add: ready, new labels" '.state == "ready" and .message == "Added api." and .labels == ["Doing","api","ux"]' "$out"
check "L add: one PUT with add_labels only" '.' "$(grep '^PUT ' "$FAKE_LOG" | grep -qxF 'PUT projects/a%2Fb/issues/3 {"add_labels":"api"}' && [[ $(grep -c NON-GET "$FAKE_LOG") == 1 ]] && echo true || echo false)"
out=$(rl --remove ux)
check "L remove: one PUT with remove_labels only" '.' "$(grep '^PUT ' "$FAKE_LOG" | grep -qxF 'PUT projects/a%2Fb/issues/3 {"remove_labels":"ux"}' && echo true || echo false)"
check "L remove: message" '.state == "ready" and .message == "Removed ux."' "$out"
check "L a label with spaces goes through as one value" '.' "$(fx labels <<<'[{"name":"needs design"}]'; rl --add 'needs design' >/dev/null; grep -qxF 'PUT projects/a%2Fb/issues/3 {"add_labels":"needs design"}' "$FAKE_LOG" && echo true || echo false)"
fx labels <<'J'
[{"name":"ux"},{"name":"Doing"},{"name":"todo"},{"name":"api"}]
J
# The guard: each of these must fail before any write.
for l in Doing doing Ready todo TODO research approved review "in progress" "In Progress"; do
  for op in --add --remove; do
    out=$(rl "$op" "$l")
    check "L guard refuses $op '$l'" '.state == "error" and (.message | test("board list label. Drag the card"))' "$out"
    check "L guard: no write for $op '$l'" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
  done
done
for args in "--add a,b" "--add" "--remove" "" "--add api --remove ux"; do
  # shellcheck disable=SC2086  # split on purpose
  out=$(rl $args)
  check "L refuses '$args'" '.state == "error"' "$out"
  check "L no glab call for '$args'" '.' "$([[ ! -s $FAKE_LOG ]] && echo true || echo false)"
done
out=$(rl --add $'bug\nx')
check "L refuses a control character" '.state == "error" and .message == "Unsupported label name."' "$out"
out=$(rl --add nosuch)
check "L add: unknown label refused, nothing created" '.state == "error" and (.message | test("no label \"nosuch\""))' "$out"
check "L add unknown: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
out=$("$fetch" relabel --project a/b --iid 0 --add api)
check "L bad iid" '.state == "error" and .message == "Invalid issue number."' "$out"
fx put-error <<<'{"message":"403 Forbidden glpat-LEAKLEAK"}'
out=$(FAKE_PUT=fail rl --add api)
check "L GitLab refuses: friendly reason, redacted" '.state == "error" and (.message | startswith("Label change failed: 403 Forbidden")) and (.message | test("glpat") | not)' "$out"
fx put <<<'{"iid":99,"labels":[]}'
check "L answer for another issue" '.state == "error" and (.message | test("unexpected response"))' "$(rl --add api)"
fx put <<<'{"iid":3,"state":"opened","labels":["Doing","api","ux"]}'
check "L logged out: no write" '.state == "logged-out"' "$(FAKE_AUTH=no rl --add api)"
rm "$FAKE_DIR/boards.json"
check "L boards unreadable: refused" '.state == "error" and (.message | test("Could not load boards"))' "$(rl --add api)"
check "L boards unreadable: no write" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
fx boards <<<'{"not":"a list"}'
check "L boards odd: refused, no write" '.state == "error" and (.message | test("unreadable"))' "$(rl --add api)"
labels_out=$(rl --add api; "$fetch" labels --project a/b; FAKE_PUT=fail rl --remove api)

# --- G: group boards' list labels are status labels too (the guard) ---------------
reset
fx boards <<<'[{"id":7,"name":"Dev","lists":[{"id":1,"label":{"name":"Doing"}}]}]'
fx labels <<<'[{"name":"ux"},{"name":"Triage"},{"name":"Shipping"},{"name":"api"}]'
fx put <<<'{"iid":3,"state":"opened","labels":["api"]}'
fx project <<<'{"id":5,"namespace":{"kind":"group","full_path":"top/sub"}}'
fx group-boards-top%2Fsub <<<'[{"id":20,"name":"Team","lists":[{"id":21,"label":{"name":"Triage"}}]}]'
fx group-boards-top <<<'[{"id":30,"name":"Org","lists":[{"id":31,"label":{"name":"Shipping"}},{"id":32,"assignee":{"username":"a"}}]}]'
: >"$FAKE_LOG"; out=$("$fetch" labels --project top/sub/app)
check "G status: project, group and parent group list labels" '.status == (["approved","doing","in progress","research","review","shipping","todo","triage"]) and [.labels[].name] == ["api","ux"]' "$out"
check "G GETs: the project, then its group and each parent's boards" '.' "$([[ $(grep -c NON-GET "$FAKE_LOG") == 0 && $(grep -c -- '--method GET projects/top%2Fsub%2Fapp$' "$FAKE_LOG") == 1 ]] && grep -qF -- '--method GET groups/top%2Fsub/boards?per_page=100' "$FAKE_LOG" && grep -qF -- '--method GET groups/top/boards?per_page=100' "$FAKE_LOG" && echo true || echo false)"
for l in Triage shipping; do
  out=$(: >"$FAKE_LOG"; "$fetch" relabel --project top/sub/app --iid 3 --add "$l")
  check "G guard refuses a group board's list label '$l'" '.state == "error" and (.message | test("board list label"))' "$out"
  check "G no write for '$l'" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
done
check "G other labels still go through" '.state == "ready"' "$("$fetch" relabel --project top/sub/app --iid 3 --add ux)"
rm "$FAKE_DIR/group-boards-top.json"; fx group-boards-top%2Fsub <<<'{"message":"404 Group Not Found"}'
check "G unreadable group boards add nothing; the rest still guards" '.status == (["approved","doing","in progress","research","review","todo"])' "$("$fetch" labels --project top/sub/app)"
fx project <<<'{"id":5,"namespace":{"kind":"user","full_path":"someone"}}'
check "G a user namespace: no group calls" '.' "$(: >"$FAKE_LOG"; "$fetch" labels --project someone/app >/dev/null; grep -q 'groups/' "$FAKE_LOG" && echo false || echo true)"
rm "$FAKE_DIR/project.json"
check "G project unreadable: project boards only, still works" '.state == "ready"' "$("$fetch" labels --project top/sub/app)"

# --- X: close and reopen: one state_event, labels untouched ---------------------
reset
fx put <<<'{"iid":3,"state":"closed","labels":["review","app-ui"]}'
cl() { : >"$FAKE_LOG"; "$fetch" "$@"; }
out=$(cl close --project a/b --iid 3)
check "X close: ready, new state, labels as GitLab has them" '.state == "ready" and .message == "Closed #3." and .issueState == "closed" and .labels == ["review","app-ui"]' "$out"
check "X close: one PUT with only state_event close" '.' "$(grep '^PUT ' "$FAKE_LOG" | grep -qxF 'PUT projects/a%2Fb/issues/3 {"state_event":"close"}' && [[ $(grep -c NON-GET "$FAKE_LOG") == 1 ]] && echo true || echo false)"
check "X close: no other GitLab call but the sign-in check" '.' "$([[ $(grep -c '^api ' "$FAKE_LOG") == 1 ]] && echo true || echo false)"
check "X close: no label field in the body" '.' "$(grep '^PUT ' "$FAKE_LOG" | grep -q 'labels' && echo false || echo true)"
fx put <<<'{"iid":3,"state":"opened","labels":["todo"]}'
out=$(cl reopen --project a/b --iid 3)
check "X reopen: ready" '.state == "ready" and .message == "Reopened #3." and .issueState == "opened"' "$out"
check "X reopen: one PUT with only state_event reopen" '.' "$(grep -qxF 'PUT projects/a%2Fb/issues/3 {"state_event":"reopen"}' "$FAKE_LOG" && echo true || echo false)"
check "X close: answer still open is an error" '.state == "error" and (.message | test("unexpected response"))' "$(cl close --project a/b --iid 3)"
fx put <<<'{"iid":4,"state":"closed","labels":[]}'
check "X close: answer for another issue is an error" '.state == "error" and (.message | test("unexpected response"))' "$(cl close --project a/b --iid 3)"
fx put-error <<<'{"message":"403 Forbidden Bearer abc.def"}'
out=$(FAKE_PUT=fail cl close --project a/b --iid 3)
check "X close refused: friendly reason, redacted" '.state == "error" and (.message | startswith("Closing failed: 403 Forbidden")) and (.message | test("abc.def") | not)' "$out"
check "X reopen refused" '.state == "error" and (.message | startswith("Reopening failed"))' "$(FAKE_PUT=fail cl reopen --project a/b --iid 3)"
for bad in "--iid 0" "--iid x" "" "--iid 3 --project ../x"; do
  # shellcheck disable=SC2086  # split on purpose
  out=$(: >"$FAKE_LOG"; "$fetch" close --project a/b $bad)
  check "X close refuses '$bad' before any glab call" '.state == "error"' "$out"
  check "X close '$bad': no glab call" '.' "$([[ ! -s $FAKE_LOG ]] && echo true || echo false)"
done
check "X logged out: no write" '.state == "logged-out"' "$(FAKE_AUTH=no cl close --project a/b --iid 3)"
check "X logged out: no PUT" '.' "$(grep -q NON-GET "$FAKE_LOG" && echo false || echo true)"
close_out=$(fx put <<<'{"iid":3,"state":"closed"}'; cl close --project a/b --iid 3; FAKE_PUT=fail cl reopen --project a/b --iid 3)

# --- CL: Closed shows the latest 20; with more, it is capped (20+) and links to the rest
# It asks for 21 to know. Open and label columns read every open issue (--paginate): no cap, no link.
closed_n() { # n web-url-prefix
  jq -cn --argjson n "$1" --arg u "$2" '[range($n) | {iid: (100 + .), title: "c", state: "closed", labels: [], web_url: "\($u)\(100 + .)"}]'; }
reset
fx boards <<'J'
[{"id":7,"name":"Dev","hide_backlog_list":false,"hide_closed_list":false,"labels":[],"milestone":null,"assignee":null,"lists":[]},
 {"id":8,"name":"Scoped","hide_backlog_list":false,"hide_closed_list":false,"labels":[{"name":"team-a"},{"name":"a b"}],
  "milestone":{"title":"v1.0"},"assignee":{"id":42,"username":"alice"},"weight":3,"lists":[]}]
J
fx open <<<'[]'
closed_n 21 https://gitlab.com/group/app/-/issues/ | fx closed
out=$("$fetch" --project group/app)
check "CL closed asks for the latest 20 and one more" '.' "$(grep -q 'state=closed&scope=all&order_by=updated_at&sort=desc&per_page=21&' "$FAKE_LOG" && echo true || echo false)"
check "CL open issues are read in full (--paginate)" '.' "$(grep -q -- '--paginate projects/group%2Fapp/issues?state=opened' "$FAKE_LOG" && echo true || echo false)"
check "CL more than 20 closed: the latest 20, capped, a link to all closed issues" '(.columns[] | select(.kind == "closed") | (.issues | length) == 20 and .issues[0].iid == 100 and .issues[-1].iid == 119 and .capped == true
    and .seeAll == "https://gitlab.com/group/app/-/issues?state=closed")
  and ([.columns[] | select(.kind != "closed") | has("seeAll") or has("capped")] | any | not)' "$out"
out=$("$fetch" --project group/app --board 8)
check "CL scoped board: the link keeps its label, milestone, assignee and weight filters" '(.columns[] | select(.kind == "closed") | .seeAll)
  == "https://gitlab.com/group/app/-/issues?state=closed&label_name%5B%5D=team-a&label_name%5B%5D=a%20b&milestone_title=v1.0&assignee_username=alice&weight=3"' "$out"
closed_n 21 https://gitlab.com/group/app/-/work_items/ | fx closed
out=$("$fetch" --project group/app)
check "CL work-item issue URLs (GitLab.com today) give the same link" '(.columns[] | select(.kind == "closed") | .seeAll) == "https://gitlab.com/group/app/-/issues?state=closed"' "$out"
closed_n 19 https://gitlab.com/group/app/-/issues/ | fx closed
out=$("$fetch" --project group/app)
check "CL 19 closed: all of them, no cap, no link" '.columns[] | select(.kind == "closed") | (.issues | length) == 19 and (has("seeAll") or has("capped") | not)' "$out"
closed_n 20 https://gitlab.com/group/app/-/issues/ | fx closed
out=$("$fetch" --project group/app)
check "CL exactly 20 closed: all of them, no cap, no link" '.columns[] | select(.kind == "closed") | (.issues | length) == 20 and (has("seeAll") or has("capped") | not)' "$out"
closed_n 21 http://gitlab.com/group/app/-/issues/ | fx closed
out=$("$fetch" --project group/app)
check "CL a non-https issue URL gives no link, but still the cap" '.columns[] | select(.kind == "closed") | (has("seeAll") | not) and .capped == true' "$out"
closed_n 21 'https://gitlab.com/group/app/-/merge_requests/' | fx closed
out=$("$fetch" --project group/app)
check "CL an unexpected URL shape gives no link" '.columns[] | select(.kind == "closed") | has("seeAll") | not' "$out"
fx boards <<<'[]'
closed_n 21 https://gitlab.example.org/sub/group/app/-/issues/ | fx closed
out=$("$fetch" --project sub/group/app)
check "CL no board (workflow columns): the link too, unscoped" '(.columns[] | select(.kind == "closed") | .seeAll) == "https://gitlab.example.org/sub/group/app/-/issues?state=closed"' "$out"

# --- PL: pipeline status of Review cards (reads only) -----------------------------
reset
fx boards <<'J'
[{"id":7,"name":"Dev","lists":[{"id":1,"position":0,"label":{"name":"Doing"}},{"id":2,"position":1,"label":{"name":"Review"}}]}]
J
fx open <<'J'
[{"iid":3,"title":"a","state":"opened","labels":["Review","Doing"],"web_url":"u"},{"iid":4,"title":"b","state":"opened","labels":["Review"],"web_url":"u"},
 {"iid":5,"title":"c","state":"opened","labels":["Review"],"web_url":"u"},{"iid":6,"title":"d","state":"opened","labels":["Review"],"web_url":"u"},
 {"iid":7,"title":"e","state":"opened","labels":["Review"],"web_url":"u"},{"iid":8,"title":"f","state":"opened","labels":["Review"],"web_url":"u"},
 {"iid":9,"title":"g","state":"opened","labels":["Review"],"web_url":"u"},{"iid":10,"title":"h","state":"opened","labels":["Review"],"web_url":"u"},
 {"iid":11,"title":"i","state":"opened","labels":["Doing"],"web_url":"u"}]
J
fx closed <<<'[]'
mr() { # iid state updated status url [project_id]
  jq -cn --argjson i "$1" --arg s "$2" --arg u "$3" --arg st "$4" --arg w "$5" --argjson p "${6:-1}" \
    '{iid: $i, project_id: $p, state: $s, updated_at: $u, reference: "!\($i)", head_pipeline: (if $st == "" then null else {status: $st, web_url: $w} end)}'
}
# 3: an open MR wins over a newer merged one. 4: merged beats closed. 5: no MR.
# 6: no access (no fixture). 7: GitLab left head_pipeline out: one GET of MR 77.
# 8: MR without a pipeline. 9: a manual pipeline. 10: a non-https link.
printf '[%s,%s]' "$(mr 31 opened 2026-01-01 success https://gitlab.com/g/a/-/pipelines/31)" "$(mr 32 merged 2026-06-01 failed https://gitlab.com/g/a/-/pipelines/32)" | fx related-3
printf '[%s,%s]' "$(mr 41 closed 2026-06-01 success https://gitlab.com/x)" "$(mr 42 merged 2026-01-01 failed https://gitlab.com/g/a/-/pipelines/42)" | fx related-4
fx related-5 <<<'[]'
mr 77 opened 2026-01-01 "" "" 55 | jq -c '[del(.head_pipeline)]' | fx related-7
mr 77 opened 2026-01-01 running https://gitlab.com/g/a/-/pipelines/77 55 | fx mr-77
printf '[%s]' "$(mr 81 opened 2026-01-01 "" "")" | fx related-8
printf '[%s]' "$(mr 91 opened 2026-01-01 manual https://gitlab.com/g/a/-/pipelines/91)" | fx related-9
printf '[%s]' "$(mr 101 opened 2026-01-01 canceled http://gitlab.com/g/a/-/pipelines/101)" | fx related-10
: >"$FAKE_LOG"
out=$("$fetch" --project group/app)
pipes='[.columns[] | select(.name == "Review") | .issues[] | {(.iid | tostring): .pipeline}] | add'
check "PL board still ready" '.state == "ready" and ([.columns[].name] == ["Open","Doing","Review","Closed"])' "$out"
check "PL statuses" "$pipes"' == {"3": {"status":"passed","url":"https://gitlab.com/g/a/-/pipelines/31","mr":"!31"},
  "4": {"status":"failed","url":"https://gitlab.com/g/a/-/pipelines/42","mr":"!42"}, "5": null, "6": null,
  "7": {"status":"running","url":"https://gitlab.com/g/a/-/pipelines/77","mr":"!77"}, "8": null, "9": null,
  "10": {"status":"canceled","url":"","mr":"!101"}}' "$out"
check "PL only the Review column" '[.columns[] | select(.name != "Review") | .issues[] | select(has("pipeline"))] == []' "$out"
check "PL one related_merge_requests GET per Review card" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 8 ]] && ! grep -q 'issues/11/related' "$FAKE_LOG" && echo true || echo false)"
check "PL one MR GET, only where head_pipeline was left out" '.' "$([[ $(grep -c 'merge_requests/[0-9]' "$FAKE_LOG") == 1 ]] && grep -q '^api --hostname gitlab.com --method GET projects/55/merge_requests/77$' "$FAKE_LOG" && echo true || echo false)"
check "PL reads only" '.' "$(grep -qE 'NON-GET|BAD-WRITE' "$FAKE_LOG" && echo false || echo true)"
check "PL saved copy has them too" "$pipes"' | .["3"].status == "passed"' "$("$fetch" cached --project group/app)"
pl_out=$out
# Finished pipelines (passed, failed, canceled) are reused for 2 minutes: the
# next refresh asks only about the others (5: no MR, 6: no access, 7: running,
# 8: none, 9: manual), and a newer answer for 3 is not seen yet.
pf="$XDG_CACHE_HOME/odevvy.gitlab-board/group%2Fapp-first@me.pipes.json"
check "PC kept beside the board, 600, no token, finished and running with the time" '.' "$([[ -f $pf && $(stat -c %a "$pf") == 600 ]] && ! grep -qiE 'glpat|bearer' "$pf" &&
  jq -e 'keys == ["10","3","4","7"] and (.["3"] | .status == "passed" and (.at | type) == "number")' "$pf" >/dev/null && echo true || echo false)"
printf '[%s]' "$(mr 31 opened 2026-01-01 running https://gitlab.com/p/31)" | fx related-3
jq -c 'map_values(.at -= 60)' "$pf" >"$pf.t" && mv "$pf.t" "$pf"
: >"$FAKE_LOG"; out=$("$fetch" --project group/app)
check "PC second refresh: the same pipelines" "$pipes"' | .["3"].status == "passed" and .["4"].status == "failed" and .["10"].status == "canceled" and .["7"].status == "running"' "$out"
check "PC second refresh: only the unfinished asked" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 5 ]] && ! grep -qE 'issues/(3|4|10)/related' "$FAKE_LOG" && echo true || echo false)"
check "PC the reused ones keep their time, the asked ones get now" '.' "$(jq -e --argjson now "$EPOCHSECONDS" '.["3"].at <= $now - 55 and .["7"].at >= $now - 5' "$pf" >/dev/null && echo true || echo false)"
jq -c --argjson now "$EPOCHSECONDS" 'map_values(.at = $now)' "$pf" >"$work/pipes-elsewhere"; rm -f "$pf"; ln -s "$work/pipes-elsewhere" "$pf"
: >"$FAKE_LOG"; "$fetch" --project group/app >/dev/null
check "PC a symlinked pipelines file is not read" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 8 ]] && echo true || echo false)"
rm -f "$pf"; "$fetch" --project group/app >/dev/null
jq -c 'map_values(.at -= 130)' "$pf" >"$pf.t" && mv "$pf.t" "$pf"
: >"$FAKE_LOG"; out=$("$fetch" --project group/app)
check "PC after 2 minutes: asked again, the newer answer shows" "$pipes"' | .["3"].status == "running"' "$out"
check "PC after 2 minutes: all eight asked" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 8 ]] && echo true || echo false)"
: >"$FAKE_LOG"; FAKE_USER=other "$fetch" --project group/app >/dev/null
check "PC another account asks for its own" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 8 ]] && echo true || echo false)"
echo 'not json' >"$pf"; out=$("$fetch" --project group/app)
check "PC an unreadable pipelines file: asked, board fine" '.state == "ready" and ('"$pipes"' | .["3"].status == "running")' "$out"
fresh_pipes() { rm -f "$XDG_CACHE_HOME"/odevvy.gitlab-board/*.pipes.json; }
# Each status word GitLab uses.
for st in success:passed failed:failed running:running canceling:running pending:pending created:pending waiting_for_resource:pending preparing:pending scheduled:pending canceled:canceled skipped:null manual:null; do
  printf '[%s]' "$(mr 31 opened 2026-01-01 "${st%%:*}" https://gitlab.com/p/31)" | fx related-3; fresh_pipes
  check "PL ${st%%:*} -> ${st##*:}" '[.columns[] | select(.name == "Review") | .issues[] | select(.iid == 3) | .pipeline.status // null][0] == '"$(jq -n --arg s "${st##*:}" 'if $s == "null" then null else $s end')" "$("$fetch" --project group/app)"
done
# A hung call: the board still loads, without that pipeline.
printf '[%s]' "$(mr 31 opened 2026-01-01 success https://gitlab.com/p/31)" | fx related-3; fresh_pipes
out=$(FAKE_HANG=issues/4/related_merge_requests "$fetch" --project group/app)
check "PL a hung call costs only its card" '.state == "ready" and ('"$pipes"' | .["4"] == null and .["3"] != null)' "$out"
check "PL a hung call: still one JSON object" '. == 1' "$(jq -s length <<<"$out")"
# No Review column: no MR calls at all.
fx boards <<<'[{"id":7,"name":"Dev","lists":[{"id":1,"position":0,"label":{"name":"Doing"}}]}]'
: >"$FAKE_LOG"; out=$("$fetch" --project group/app)
check "PL no Review column, no MR calls" '.state == "ready"' "$out"
check "PL no Review column: log" '.' "$(grep -q 'merge_requests' "$FAKE_LOG" && echo false || echo true)"
# Workflow-label fallback (no boards): its review column counts; at most 15 cards.
fx boards <<<'[]'
jq -cn '[range(1; 21) | {iid: ., title: "r", state: "opened", labels: ["review"], web_url: "u"}]' | fx open
printf '[%s]' "$(mr 31 opened 2026-01-01 failed https://gitlab.com/p/31)" | fx related-3; fresh_pipes
: >"$FAKE_LOG"; out=$("$fetch" --project group/app)
check "PL workflow review column" '(.columns[] | select(.name == "review") | .issues[] | select(.iid == 3) | .pipeline.status) == "failed"' "$out"
check "PL at most 15 Review cards asked" '.' "$([[ $(grep -c '/related_merge_requests$' "$FAKE_LOG") == 15 ]] && echo true || echo false)"
check "PL four at a time, not one by one" '.' "$(rm -rf "$work/slow"*; fresh_pipes; FAKE_MR_PROBE=$work/slow "$fetch" --project group/app >/dev/null
  m=$(sort -n "$work/slow.n" | tail -1); ((m >= 2 && m <= 4)) && echo true || echo false)"
check "PL no token in output" '.' "$(grep -qiE 'glpat|bearer' <<<"$pl_out$out" && echo false || echo true)"

# --- MR: the Merge requests view's lists (reads only) ----------------------------
reset
mrl() { # iid project_id path draft status reviewers-json -> one list row
  jq -cn --argjson i "$1" --argjson p "$2" --arg path "$3" --argjson d "$4" --arg st "$5" --argjson rv "${6:-[]}" \
    '{iid: $i, project_id: $p, title: "MR \($i) <b>", web_url: "https://gitlab.com/\($path)/-/merge_requests/\($i)", draft: $d,
      references: {full: "\($path)!\($i)"}, source_branch: "b\($i)", updated_at: "2026-10-30T12:00:00Z", detailed_merge_status: $st,
      author: {username: "bot\($i)", name: "Bot \($i)", avatar_url: "https://x/a.png"}, reviewers: $rv}'
}
printf '[%s,%s,%s]' "$(mrl 88 5 g/p41 false ci_still_running)" "$(mrl 87 5 g/p41 true draft_status)" "$(mrl 86 5 g/p41 false mergeable '[{"username":"me","name":"Me"}]')" | fx mrs-review
printf '[%s,%s]' "$(mrl 35 6 o/board false checking)" "$(mrl 12 7 o/dots true draft_status '[{"username":"r1","name":"R One","avatar_url":"http://x/a.png"}]')" | fx mrs-mine
jq -cn '{project_id: 5, iid: 88, detailed_merge_status: "ci_still_running", head_pipeline: {status: "running", web_url: "https://gitlab.com/g/p41/-/pipelines/1"}}' | fx mr-88
jq -cn '{project_id: 6, iid: 35, detailed_merge_status: "mergeable", head_pipeline: null}' | fx mr-35
echo '[{"user":{"username":"me","name":"Me"},"state":"requested_changes"},{"user":{"username":"x","name":"X"},"state":"approved"}]' | fx reviewers-88
echo '[{"user":{"username":"r1","name":"R One"},"state":"bogus"}]' | fx reviewers-12
: >"$FAKE_LOG"; mr_out=$("$fetch" mrs)
check "MR ready, all projects" '.state == "ready" and .scope == "all"' "$mr_out"
check "MR review: drafts hidden, newest first kept" '[.review[].iid] == [88, 86]' "$mr_out"
check "MR mine: drafts kept" '[.mine[].iid] == [35, 12] and .mine[1].draft == true' "$mr_out"
check "MR row fields" '.review[0] | .project == "g/p41" and .branch == "b88" and .url == "https://gitlab.com/g/p41/-/merge_requests/88" and .author == {"username":"bot88","name":"Bot 88","avatar":"https://x/a.png"} and .title == "MR 88 <b>"' "$mr_out"
check "MR pipeline from the MR GET" '.review[0].pipeline == {"status":"running","url":"https://gitlab.com/g/p41/-/pipelines/1"} and .mine[0].pipeline == null' "$mr_out"
check "MR fresh merge status from the MR GET" '.mine[0].status == "mergeable" and .review[1].status == "mergeable"' "$mr_out"
check "MR reviewer state from the reviewers GET" '.review[0].reviewers == [{"username":"me","name":"Me","avatar":"","state":"requested_changes"},{"username":"x","name":"X","avatar":"","state":"approved"}]' "$mr_out"
check "MR unknown state: none; no reviewers GET: the list's, no state; http avatar dropped" '.mine[1].reviewers == [{"username":"r1","name":"R One","avatar":"","state":null}] and .review[1].reviewers == [{"username":"me","name":"Me","avatar":"","state":null}]' "$mr_out"
check "MR two list GETs, then MR + reviewers GETs per row (not the hidden draft)" '.' "$(
  grep -q '^api --hostname gitlab.com --method GET merge_requests?scope=reviews_for_me&draft=false&state=opened&order_by=updated_at&sort=desc&per_page=20$' "$FAKE_LOG" &&
  grep -q '^api --hostname gitlab.com --method GET merge_requests?scope=created_by_me&state=opened&order_by=updated_at&sort=desc&per_page=20$' "$FAKE_LOG" &&
  [[ $(grep -cE 'merge_requests/[0-9]+$' "$FAKE_LOG") == 4 && $(grep -c '/reviewers$' "$FAKE_LOG") == 4 ]] && ! grep -q 'merge_requests/87' "$FAKE_LOG" &&
  ! grep -q NON-GET "$FAKE_LOG" && echo true || echo false)"
: >"$FAKE_LOG"; out=$("$fetch" mrs --project g/p41)
check "MR this project: the project's lists" '.state == "ready" and .scope == "g/p41"' "$out"
check "MR this project: log" '.' "$(grep -q '^api --hostname gitlab.com --method GET projects/g%2Fp41/merge_requests?scope=reviews_for_me&' "$FAKE_LOG" && grep -q 'GET projects/g%2Fp41/merge_requests?scope=created_by_me&' "$FAKE_LOG" && echo true || echo false)"
check "MR bad project refused" '.state == "error" and (.message | test("Invalid project"))' "$("$fetch" mrs --project 'a/../b')"
check "MR signed out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch" mrs)"
rm -f "$FAKE_DIR/mrs-mine.json"
check "MR a failed list fails the answer" '.state == "error" and .message == "Could not load merge requests."' "$("$fetch" mrs)"
printf '[%s]' "$(mrl 35 6 o/board false checking)" | fx mrs-mine
echo '{"message":"x"}' | fx mrs-review
check "MR a non-list answer" '.state == "error"' "$("$fetch" mrs)"
printf '[%s]' "$(mrl 88 5 g/p41 false ci_still_running)" | fx mrs-review
out=$(FAKE_HANG=merge_requests/88/reviewers "$fetch" mrs)
check "MR a hung reviewers GET costs only its states" '.state == "ready" and .review[0].reviewers == [] and .review[0].pipeline.status == "running"' "$out"
jq -cn '[range(1; 16) | {iid: ., project_id: 9, title: "t", draft: false, references: {full: "a/b!\(.)"}}]' | fx mrs-review
jq -cn '[range(21; 36) | {iid: ., project_id: 9, title: "t", draft: false, references: {full: "a/b!\(.)"}, web_url: "http://gitlab.com/a/b/-/merge_requests/\(.)"}]' | fx mrs-mine
: >"$FAKE_LOG"; out=$("$fetch" mrs)
check "MR at most 10 per list" '(.review | length) == 10 and (.mine | length) == 10' "$out"
check "MR at most 10 rows asked about per list" '.' "$([[ $(grep -c '/reviewers$' "$FAKE_LOG") == 20 ]] && echo true || echo false)"
check "MR links only over https" '[.mine[].url] | unique == [""]' "$out"
check "MR no token in output" '.' "$(grep -qiE 'glpat|bearer' <<<"$mr_out$out" && echo false || echo true)"

# --- MG: the same view from one GraphQL query ---------------------------------------
# The fixture is the MR block's data as GraphQL answers it (enum values upper
# case, relative pipeline paths, reviewer states on each reviewer). 86 has a
# reviewer without a state and 12 an unknown one: those two go to REST.
gu() { jq -cn --arg u "$1" --arg n "$2" --arg a "${3:-}" --arg st "${4:-}" '{username: $u, name: $n, avatarUrl: (if $a == "" then null else $a end),
  mergeRequestInteraction: {reviewState: (if $st == "" then null else $st end)}}'; }
gm() { # iid project_id path draft status pipeline-json reviewers-json
  jq -cn --argjson i "$1" --argjson p "$2" --arg path "$3" --argjson d "$4" --arg st "$5" --argjson pl "$6" --argjson rv "$7" \
    '{projectId: $p, iid: "\($i)", title: "MR \($i) <b>", webUrl: "https://gitlab.com/\($path)/-/merge_requests/\($i)", draft: $d,
      reference: "\($path)!\($i)", sourceBranch: "b\($i)", updatedAt: "2026-10-30T12:00:00Z", detailedMergeStatus: $st,
      author: {username: "bot\($i)", name: "Bot \($i)", avatarUrl: "https://x/a.png"}, headPipeline: $pl, reviewers: {nodes: $rv}}'; }
gql() { jq -cn --argjson r "$1" --argjson m "$2" '{data: {currentUser: {review: {nodes: $r}, mine: {nodes: $m}}}}' | fx graphql; }
G88=$(gm 88 5 g/p41 false CI_STILL_RUNNING '{"status":"RUNNING","path":"/g/p41/-/pipelines/1"}' "[$(gu me Me "" REQUESTED_CHANGES),$(gu x X "" APPROVED)]")
G86=$(gm 86 5 g/p41 false MERGEABLE null "[$(gu me Me)]")
G35=$(gm 35 6 o/board false MERGEABLE null '[]')
G12=$(gm 12 7 o/dots true DRAFT_STATUS null "[$(gu r1 'R One' http://x/a.png BOGUS)]")
printf '[%s,%s,%s]' "$(mrl 88 5 g/p41 false ci_still_running)" "$(mrl 87 5 g/p41 true draft_status)" "$(mrl 86 5 g/p41 false mergeable '[{"username":"me","name":"Me"}]')" | fx mrs-review
printf '[%s,%s]' "$(mrl 35 6 o/board false checking)" "$(mrl 12 7 o/dots true draft_status '[{"username":"r1","name":"R One","avatar_url":"http://x/a.png"}]')" | fx mrs-mine
rest_out=$("$fetch" mrs)
gql "[$G88,$G86]" "[$G35,$G12]"
: >"$FAKE_LOG"; out=$("$fetch" mrs)
check "MG the same rows as REST" '(input | del(.updatedAt)) == del(.updatedAt)' "$(printf '%s\n%s' "$rest_out" "$out")"
check "MG one query, no list GETs; REST GETs only for 86 and 12" '.' "$([[ $(grep -c ' graphql -f query=query' "$FAKE_LOG") == 1 && $(grep -c 'scope=' "$FAKE_LOG") == 0 &&
  $(grep -cE 'merge_requests/(86|12)(/reviewers)?$' "$FAKE_LOG") == 4 && $(grep -cE 'merge_requests/[0-9]+(/reviewers)?$' "$FAKE_LOG") == 4 ]] && ! grep -qE 'NON-GET|BAD-GRAPHQL' "$FAKE_LOG" && echo true || echo false)"
check "MG the query: review requests without drafts, mine with them, newest 10 of each" '.' "$(grep ' graphql ' "$FAKE_LOG" | grep -qF 'review: reviewRequestedMergeRequests(state: opened, draft: false, sort: UPDATED_DESC, first: 10)' &&
  grep ' graphql ' "$FAKE_LOG" | grep -qF 'mine: authoredMergeRequests(state: opened, sort: UPDATED_DESC, first: 10)' && echo true || echo false)"
check "MG the query asks for all projects (no project argument)" '.' "$(grep ' graphql ' "$FAKE_LOG" | grep -qE 'projectPath|projectId:|-f (p|id)=' && echo false || echo true)"
gql "[$G88]" "[$G35]"
: >"$FAKE_LOG"; out=$("$fetch" mrs)
check "MG every state known: one call in all" '.' "$([[ $(grep -c . "$FAKE_LOG") == 2 ]] && grep -q '^auth status' "$FAKE_LOG" && echo true || echo false)"
check "MG pipeline link made absolute on this host; merge status lower case" '.review[0].pipeline == {"status":"running","url":"https://gitlab.com/g/p41/-/pipelines/1"} and .review[0].status == "ci_still_running" and .mine[0].status == "mergeable"' "$out"
check "MG reviewer states" '.review[0].reviewers == [{"username":"me","name":"Me","avatar":"","state":"requested_changes"},{"username":"x","name":"X","avatar":"","state":"approved"}]' "$out"
for st in APPROVED:approved REQUESTED_CHANGES:requested_changes REVIEWED:reviewed REVIEW_STARTED:review_started UNAPPROVED:unapproved UNREVIEWED:unreviewed; do
  gql "[$(gm 88 5 g/p41 false MERGEABLE null "[$(gu me Me "" "${st%%:*}")]")]" '[]'
  check "MG reviewState ${st%%:*} -> ${st##*:}" '.review[0].reviewers[0].state == "'"${st##*:}"'"' "$("$fetch" mrs)"
done
gql "[$(gm 88 5 g/p41 false MERGEABLE '{"status":"SUCCESS","path":"/p/1"}' '[]')]" "[$(jq -c '.author.avatarUrl = "/uploads/a.png"' <<<"$G35")]"
out=$("$fetch" mrs)
check "MG SUCCESS -> passed; a relative avatar gets this host" '.review[0].pipeline.status == "passed" and .mine[0].author.avatar == "https://gitlab.com/uploads/a.png"' "$out"
: >"$FAKE_LOG"; "$fetch" mrs --project g/p41 >/dev/null
# shellcheck disable=SC2016  # GraphQL variables in the pattern
check "MG this project: by path, as a variable" '.' "$(grep ' graphql ' "$FAKE_LOG" | grep -q 'query=query($p: String) .*projectPath: $p, .* -f p=g/p41$' && echo true || echo false)"
: >"$FAKE_LOG"; "$fetch" mrs --project 42 >/dev/null
# shellcheck disable=SC2016  # GraphQL variables in the pattern
check "MG this project: by numeric id, as a global id" '.' "$(grep ' graphql ' "$FAKE_LOG" | grep -q 'query=query($id: ProjectID) .*projectId: $id, .* -f id=gid://gitlab/Project/42$' && echo true || echo false)"
echo '{"errors":[{"message":"Field x does not exist"}],"data":null}' | fx graphql
: >"$FAKE_LOG"; out=$("$fetch" mrs)
check "MG GraphQL errors: the whole view from REST, same rows" '(input | del(.updatedAt)) == del(.updatedAt)' "$(printf '%s\n%s' "$rest_out" "$out")"
check "MG ... the REST lists were read" '.' "$([[ $(grep -c 'scope=' "$FAKE_LOG") == 2 ]] && echo true || echo false)"
gql "[$G88]" "[$G35]"; jq -c '. + {errors: [{message: "partial"}]}' "$FAKE_DIR/graphql.json" >"$FAKE_DIR/g.t" && mv "$FAKE_DIR/g.t" "$FAKE_DIR/graphql.json"
: >"$FAKE_LOG"; FAKE_GQL_EXIT0=1 "$fetch" mrs >/dev/null
check "MG data with errors (partial): REST, not half an answer" '.' "$([[ $(grep -c 'scope=' "$FAKE_LOG") == 2 ]] && echo true || echo false)"
echo '{"data":{"currentUser":null}}' | fx graphql
check "MG no current user: REST" '(input | del(.updatedAt)) == del(.updatedAt)' "$(printf '%s\n%s' "$rest_out" "$("$fetch" mrs)")"
gql "[$G88]" "[$G35]"
out=$(FAKE_HANG=' graphql ' "$fetch" mrs)
check "MG a hung query: REST answers" '.state == "ready" and (input | del(.updatedAt)) == del(.updatedAt)' "$(printf '%s\n%s' "$rest_out" "$out")"
check "MG no token in output" '.' "$(grep -qiE 'glpat|bearer' <<<"$out" && echo false || echo true)"
rm -f "$FAKE_DIR/graphql.json"

# --- AC: access level and token scopes (reads only) -------------------------------
reset
fx project <<<'{"id":5,"path_with_namespace":"group/app","permissions":{"project_access":{"access_level":10},"group_access":null}}'
fx token-self <<<'{"id":1,"name":"glab","scopes":["read_api","api","Bad Scope"],"token":"glpat-SECRET"}'
: >"$FAKE_LOG"; out=$("$fetch" access --project group/app)
check "AC guest: level 10, scopes kept (valid names only)" '. == {state: "ready", message: "", project: "group/app", level: 10, scopes: ["read_api", "api"]}' "$out"
check "AC GETs only: the project (full, not simple) and the token record" '.' "$([[ $(grep -c 'NON-GET' "$FAKE_LOG") == 0 && $(grep -c -- '--method GET projects/group%2Fapp$' "$FAKE_LOG") == 1 && $(grep -c -- '--method GET personal_access_tokens/self$' "$FAKE_LOG") == 1 ]] && echo true || echo false)"
check "AC no token in output" '.' "$(grep -qiE 'glpat|bearer|SECRET' <<<"$out" && echo false || echo true)"
fx project <<<'{"id":5,"permissions":{"project_access":{"access_level":20},"group_access":{"access_level":40}}}'
rm -f "$FAKE_DIR/token-self.json"
out=$("$fetch" access --project group/app)
check "AC the higher of project and group; no token record: scopes null" '.level == 40 and .scopes == null' "$out"
fx project <<<'{"id":5,"permissions":{"project_access":null,"group_access":null}}'
check "AC not a member: level 0" '.level == 0' "$("$fetch" access --project group/app)"
fx project <<<'{"message":"404 Project Not Found"}'
check "AC unreadable project: error" '.state == "error"' "$("$fetch" access --project group/app)"
rm -f "$FAKE_DIR/project.json"
check "AC refused: error, no level" '.state == "error" and (.level | not)' "$("$fetch" access --project group/app)"
check "AC needs a project" '.state == "error" and (.message | test("No project"))' "$("$fetch" access)"
check "AC signed out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch" access --project group/app)"

# --- safety: no token in any output --------------------------------------------
fx board <<<'{"id":7,"name":"Dev","lists":[{"id":11,"label":{"name":"todo"}},{"id":12,"label":{"name":"approved"}}]}'
fx put <<<'{"iid":3,"state":"opened","labels":["approved"]}'
at opened '["todo"]'
all=$(printf '%s\n' "$reads"; "$fetch" --project group/app; "$fetch" projects; "$fetch" issue --project a/b --iid 45; FAKE_AUTH=no "$fetch" --project a/b;
  FAKE_AUTH=401 "$fetch" --project a/b; FAKE_AUTH=offline "$fetch" --project a/b; mv_ --from 11 --to 12; FAKE_PUT=fail mv_ --from 11 --to 12; mv_ --iid x
  "$fetch" notes --project a/b --iid 1; fx post <<<'{"id":1}'; echo hi | say; echo hi | FAKE_POST=fail say;
  fx user <<<'{"username":"dev1","private_token":"glpat-SECRET"}'; "$fetch" whoami; "$fetch" logout; FAKE_LOGOUT=fail "$fetch" logout; printf '%s\n' "$labels_out" "$close_out")
check "no token leak" '.' "$(grep -qiE 'glpat|bearer' <<<"$all" && echo false || echo true)"

echo "passed $pass, failed $fail"
((fail == 0))
