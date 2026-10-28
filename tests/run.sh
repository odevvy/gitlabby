#!/usr/bin/env bash
# Offline tests for board-fetch against tests/fake-glab. No network, no token.
set -uo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fetch="$here/../board-fetch"
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"; cp "$here/fake-glab" "$work/bin/glab"
export PATH="$work/bin:$PATH" FAKE_LOG="$work/log" FAKE_DIR="$work/fx"
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
check "F projects query" '.' "$(grep -q '^api --hostname gitlab.com --method GET projects?membership=true&simple=true&order_by=last_activity_at&per_page=100$' "$FAKE_LOG" && echo true || echo false)"
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
check "G bad board" '.state == "error"' "$("$fetch" --board 1x)"
check "G bad iid" '.state == "error"' "$("$fetch" issue --iid '1;x')"
check "G logged out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch")"
rm -f "$FAKE_DIR/open.json"; fx boards <<<'[]'
check "G api failure" '.state == "error"' "$("$fetch")"

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
mv_() { "$fetch" move --project group/app --board 7 --iid 3 "$@"; }
put() { sed -n 's/^PUT projects\/group%2Fapp\/issues\/3 //p' "$FAKE_LOG" | tail -n1; }
puts() { grep -c '^PUT ' "$FAKE_LOG"; }
body_is() { # name expected-json args...
  local name=$1 want=$2; shift 2; : >"$FAKE_LOG"
  local out; out=$(mv_ "$@")
  check "$name ready" '.state == "ready"' "$out"
  check "$name body" "(. | tojson) == ($want | tojson)" "$(put | jq -cS . 2>/dev/null || echo null)"
}
body_is "M label->label" '{"add_labels":"approved","remove_labels":"todo"}' --from 11 --to 12
check "M label->label message" '.message == "Moved #3 to approved." and .issue == {"iid":3,"state":"opened","labels":["approved","app-ui"]}' "$(mv_ --from 11 --to 12)"
body_is "M open->label" '{"add_labels":"todo"}' --from open --to 11
body_is "M label->closed" '{"state_event":"close"}' --from 11 --to closed
body_is "M open->closed" '{"state_event":"close"}' --from open --to closed
body_is "M closed->label" '{"add_labels":"todo","state_event":"reopen"}' --from closed --to 11
body_is "M closed->open" '{"state_event":"reopen"}' --from closed --to open
body_is "M label->open" '{"remove_labels":"approved"}' --from 12 --to open
: >"$FAKE_LOG"; mv_ --from 11 --to 12 >/dev/null
check "M one PUT to the issue, after one GET of the board" '.' "$(grep -c '^api ' "$FAKE_LOG" | grep -qx 2 &&
  grep -q '^api --hostname gitlab.com --method GET projects/group%2Fapp/boards/7$' "$FAKE_LOG" &&
  grep -q '^api --hostname gitlab.com --method PUT --header Content-Type: application/json --input - projects/group%2Fapp/issues/3$' "$FAKE_LOG" &&
  [[ $(puts) == 1 ]] && ! grep -q BAD-WRITE "$FAKE_LOG" && echo true || echo false)"

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

# --- R: reads are GET only ---------------------------------------------------
# Runtime: every read command, including a refresh with a board, issues only
# GETs. Structure: board-fetch has exactly one non-GET request, in write_issue(),
# defined and called only inside the move branch.
reset
fx boards <<<'[{"id":7,"name":"Dev","lists":[{"id":11,"position":0,"label":{"name":"todo"}}]}]'
fx open <<<'[{"iid":1,"title":"a","state":"opened","labels":["todo"],"web_url":"u"}]'
fx closed <<<'[]'
fx projects <<<'[{"id":1,"path_with_namespace":"a/b"}]'
fx issue <<<'{"iid":1,"title":"a","state":"opened","labels":[],"web_url":"u"}'
reads=$("$fetch"; "$fetch" board --project group/app --board 7; "$fetch" projects; "$fetch" boards --project a/b; "$fetch" issue --project a/b --iid 1)
check "R refresh has listId" '.columns[1] | .name == "todo" and .listId == 11' "$("$fetch" --project group/app)"
check "R reads ran" '.' "$(grep -c '^api ' "$FAKE_LOG" | grep -qxE '[0-9]{2,}' && echo true || echo false)"
check "R reads are GET only" '.' "$(grep -q 'NON-GET' "$FAKE_LOG" && echo false || echo true)"
check "R every api call says --method GET" '.' "$(grep '^api ' "$FAKE_LOG" | grep -qv -- '--method GET ' && echo false || echo true)"
src=$(grep -v '^ *#' "$fetch")
check "R one non-GET in the script" '.' "$(grep -oE -- '--method [A-Z]+' <<<"$src" | sort | tr '\n' ' ' | grep -qx -- '--method GET --method PUT ' && echo true || echo false)"
check "R glab api only in get() and write_issue()" '.' "$(grep -c 'glab api' <<<"$src" | grep -qx 2 && echo true || echo false)"
check "R write_issue only inside move" '.' "$(awk '/^  move\)/{m=1} /^    exit 0 ;;/{if(m)m=2} /write_issue/{if(m!=1)bad=1} END{print bad?"false":"true"}' <<<"$src")"

# --- safety: no token in any output --------------------------------------------
fx board <<<'{"id":7,"name":"Dev","lists":[{"id":11,"label":{"name":"todo"}},{"id":12,"label":{"name":"approved"}}]}'
fx put <<<'{"iid":3,"state":"opened","labels":["approved"]}'
all=$(printf '%s\n' "$reads"; "$fetch"; "$fetch" projects; "$fetch" issue --iid 45; FAKE_AUTH=no "$fetch"; mv_ --from 11 --to 12; FAKE_PUT=fail mv_ --from 11 --to 12; mv_ --iid x)
check "no token leak" '.' "$(grep -qiE 'glpat|bearer' <<<"$all" && echo false || echo true)"

echo "passed $pass, failed $fail"
((fail == 0))
