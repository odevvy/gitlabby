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

# --- G: validation, auth, failures ------------------------------------------
check "G bad project" '.state == "error"' "$("$fetch" --project 'a/../b')"
check "G bad project 2" '.state == "error"' "$("$fetch" --project 'a b;rm')"
check "G bad board" '.state == "error"' "$("$fetch" --board 1x)"
check "G bad iid" '.state == "error"' "$("$fetch" issue --iid '1;x')"
check "G logged out" '.state == "logged-out"' "$(FAKE_AUTH=no "$fetch")"
rm -f "$FAKE_DIR/open.json"; fx boards <<<'[]'
check "G api failure" '.state == "error"' "$("$fetch")"

# --- safety: only GET, no token in any output -------------------------------
check "only GET" '.' "$(grep -q 'NON-GET' "$FAKE_LOG" && echo false || echo true)"
all=$("$fetch"; "$fetch" projects; "$fetch" issue --iid 45; FAKE_AUTH=no "$fetch")
check "no token leak" '.' "$(grep -qiE 'glpat|bearer' <<<"$all" && echo false || echo true)"

echo "passed $pass, failed $fail"
((fail == 0))
