# GitLab Board for Omarchy

A bar icon that opens a GitLab issue board in a popup. Out of the box it shows
the first board of `firelink21/phrase41`.

## Default board

Every shell start or restart opens the default board. Browsing other boards in
the picker doesn't change it. To make a board the default, click the star on
its row in the picker's board step; only one board can be the default. The
header shows a star while you're on the default board. On any other board it
shows a **Default** button that takes you back.

## Columns

The columns are the lists on the selected GitLab board, in the board's order:

- **Open**: open issues that are in none of the board's label lists. Not shown
  if the board hides it.
- **One column per label list**: open issues with that label, in the board's
  order. An issue with two list labels appears in both columns, as it does on
  GitLab.
- **Closed**: the 20 most recently updated closed issues. Not shown if the
  board hides it.
- **Assignee, milestone, and iteration lists**: shown with a "not supported
  yet" note.

If the board has a scope (labels, milestone, assignee, or weight), only issues
in that scope are shown.

If the project has no boards, the popup says so in its header. It then falls
back to workflow-label columns: research, todo, approved, in progress, review,
Closed, and Unlabeled. Unlabeled appears only when it has issues. Each issue
goes in the furthest-along label it has.

## Moving issues

Drag a card onto another column to move the issue. This writes to GitLab, the
same way dragging it on GitLab's own board does:

| From \ To | Open | Label list B | Closed |
| --- | --- | --- | --- |
| Open | - | add label B | close |
| Label list A | remove label A | remove A, add B | close (labels kept) |
| Closed | reopen | reopen, add label B | - |

Other labels on the issue are never touched. This follows GitLab's table in
[Dragging issues between lists](https://docs.gitlab.com/user/project/issue_board/#dragging-issues-between-lists).

- A drag starts after the pointer moves a few pixels, so a plain click still
  opens the issue. Collapsed columns accept drops too; the column under the
  card lights up in its color.
- The card moves right away. If GitLab refuses (no permission, network, a
  token without the `api` scope), it jumps back and the header shows why for
  a few seconds. When GitLab accepts, the board reloads.
- **Out-of-date cards are never moved.** Just before writing, the plugin reads
  the issue from GitLab and checks that it's still in the column you dragged
  it from (still open with that label; for Open, open with none of the board's
  list labels; for Closed, closed). If someone moved, closed or reopened it in
  the meantime, nothing is written: the card jumps back, the header says
  `#45 changed on GitLab. Board refreshed.`, and the board reloads so you see
  where the issue really is. An issue that's already in the column you
  dropped it on counts as changed too. A card that shows in two label columns
  (two list labels) can still be moved from either.
- That check and the write are two requests about a second apart, and GitLab
  has no "only if unchanged" option for issues, so a change made by someone
  else inside that second can still be overwritten.
- One move at a time: while a move is on its way, cards can't be dragged.
- You can't drop onto assignee, milestone or other unsupported lists, and
  nothing can be moved on the workflow-label fallback (a project without
  boards). Dropping a card on its own column does nothing.
- Only dropping a card and posting a comment write. Refreshes, opening issues
  and the picker only read.

**Moves can set off automations.** Anything that watches labels or issue state
(bots, webhooks, CI rules, GitLab triage policies) reacts to a move exactly as
it would to a change on the website. On phrase41, moving an issue into
approved or review wakes the bots.

## Comments

The issue view lists the issue's comments under the description, oldest first,
each with the author's avatar, name, age and text (shown as plain text, not
Markdown). System notes such as "added ~approved label" are left out. The
comments load each time you open the issue; a small spinning icon next to
**Comments** shows while they load.

Under the thread is a box for a new comment. Click **Post** or press
`Ctrl+Enter` to send it; `Shift+Enter` or `Enter` adds a line, and `Escape`
leaves the box (a second `Escape` goes back to the board).

- **Posting writes to GitLab as you.** The comment appears under your name,
  sends the usual notifications, and wakes anything that watches comments
  (webhooks, bots). It needs a `glab` token with the `api` scope; a
  read-only token gets a `403`.
- While a comment is on its way the box and button are disabled. When GitLab
  accepts it, the box clears and the thread reloads. When it fails, your text
  stays in the box and the reason shows in red under it.
- Empty or whitespace-only comments are never sent.
- Going back and reopening the same issue keeps an unsent draft; opening
  another issue clears it.
- The thread shows the newest 100 notes (one GitLab page, system notes
  included in that count). If there are more, it says so; open the issue in
  the browser for the rest.
- Edit, delete, replies to a thread, and Markdown preview are not supported;
  use GitLab for those.

### Trying it on a sandbox project first

1. Create a private throwaway project on GitLab, for example
   `you/board-sandbox`, and give it a few labels (say `todo`, `doing`,
   `review`).
2. In its **Plan > Issue boards**, add a list for each label, then create a
   handful of test issues.
3. In the popup, open the picker (click the title), choose the sandbox
   project and its board. Browsing doesn't change your default board.
4. Drag cards between columns, into Closed and back, and check each issue on
   GitLab: its labels and state should match the table above.
5. Click the title again and go back to your real board, or click **Default**.

## Cards and colors

- Label chips use each label's GitLab color and text color.
- Each column header has a dot and underline in its color: the label's color
  for label lists, the theme accent for Open, and the theme's muted color for
  Closed.
- Each card shows up to three assignee avatars (two plus `+N` when there are
  more), the comment count, and the issue's age (`45m`, `3h`, `4d`, `2w`,
  `6mo`, `1y`). An avatar shows the person's initials until its image loads,
  or if it doesn't load. Avatar images are loaded straight from GitLab's
  `https` avatar URLs.
- Columns slide when they collapse or expand, and cards lift slightly on hover.

The popup card itself is drawn by Omarchy in your theme's
`popups.background`. The plugin adds translucent panes and a soft light on
top of it. To make every popup see-through, including this one, set an alpha
in `~/.config/omarchy/shell.toml` (it applies live):

```toml
[popups]
background-alpha = 0.88
```

Omarchy 4.0.6 has blur turned off and no blur rule for its popups, so what's
behind the popup shows through without blur.

## Popup

- The title, `group/project · Board ▾`, opens the picker. Pick a project (type
  to filter your 100 most recently active projects), then one of its boards.
- Click an issue to see its details. Its number and title show at once, with a
  thin bar sliding under the title until the issue and its comments have
  loaded. Under the state and labels is one line with the author and how long
  ago it was created and updated, plus a second line with the assignees and
  milestone when it has any. Below that is the description, then the comments
  and a box to add one (see "Comments"). The view also has an "Open in
  browser" link.
- The description is GitLab Markdown drawn by the plugin: headings,
  paragraphs, bold, italic, strikethrough, links, inline code and code blocks,
  lists (including task lists), quotes, tables and rules. Raw HTML shows as
  text, and images show as links, so nothing is loaded from the web. Anything
  fancier (diagrams, math, references like `#62`) shows as plain text; open
  the issue in the browser for those. Hovering a link shows where it goes, and
  only `https` links open. A description over 20,000 characters is cut at a
  line break, with a link to the rest.
- The gear opens the settings: which columns start collapsed, and the refresh
  interval. It stays lit while they're open; click it again to go back.
- The issue view, the picker and the settings each have a ✕ at the top right
  that goes back to the board, like `Escape`. In the picker's board step, ‹
  goes back to the project list.
- Click a column header to collapse it to a narrow strip. Click a chip under
  the header to hide or show that column.
- Drag a card to another column to move the issue (see "Moving issues").

| Input | Action |
| --- | --- |
| Left-click the icon | Open or close the popup |
| Right- or middle-click the icon | Refresh |
| Refresh button | Refresh |

The first time the popup opens after a shell start, it shows the board as
you last saw it (see "Saved board"), with "Saved 3h ago · updating…" in the
header, until the fresh board arrives. Cards can't be dragged until then.

The board refreshes each time the popup opens and every 60 seconds
(configurable) while it's open; while it's closed, only a right- or
middle-click refreshes. While it loads, the refresh icon in the header spins;
it finishes its turn and stops when the new data is in. The board stays
usable during a refresh. A refresh that comes due while you're holding or dragging a card
waits until you let go, so the card can't change under the pointer. A wide
board scrolls sideways. A tall one scrolls down, and every column, collapsed
strips too, stretches to the tallest so they end together.

## Keyboard

To open the popup with a key, add this to `~/.config/hypr/bindings.lua`,
then run `hyprctl reload`:

```lua
o.bind("SUPER + CTRL + G", "GitLab board", "omarchy-shell shell toggle odevvy.gitlab-board")
```

Omarchy's own `SUPER + CTRL + 1`…`9` also open the right section's bar panels by
position. In the popup the keyboard cursor shows after the first move.

| Key | Action |
| --- | --- |
| `h j k l` or arrows | Move between cards; up and down in the picker |
| `Enter` or `Space` | Open the selected issue; pick the selected row |
| `o` | Open the issue in the browser |
| `c` | Write a comment (issue view) |
| `Ctrl+Enter` | Post the comment |
| `r` | Refresh the board |
| `p` | Choose a project and board |
| `s` | Settings |
| `?` | This list of keys |
| `Tab` or `Shift+Tab` | Next or previous bar panel |
| `Escape` | Leave the comment box; otherwise back to the board; on the board, close |

Letters go to the comment box or the picker's filter while you type in them.

## Saved state

Everything is saved on the widget's entry in `~/.config/omarchy/shell.json`:

| Key | Meaning |
| --- | --- |
| `defaultProject` | Default project: path or numeric id |
| `defaultBoardId`, `defaultBoardName` | Default board; empty means the project's first board |
| `refreshIntervalSec` | Refresh interval in seconds |
| `defaultCollapsed` | Columns that start collapsed on a board you have not changed yet. Default `["closed","research","open"]`; matched case-insensitively |
| `boardStates` | Collapsed and hidden columns for each project and board, keyed `project#boardId` |
| `settingsRevision` | Set to `2` by v0.1.3 after its one-time update |

The board you're browsing isn't saved. Older keys (`project`, `boardId`,
`boardName`, `collapsedColumns`, `hiddenColumns`) are dropped the first time
v0.1.2 saves.

v0.1.3 adds Open to `defaultCollapsed` and to the collapsed columns of every
board in `boardStates`, once. It changes nothing else, and if you expand Open
afterwards, it stays expanded.

### Saved board

After each board load, `board-fetch` saves a copy of the board (the same JSON
the popup shows: titles, labels, assignee names; never anything from glab's
login) in `~/.cache/odevvy.gitlab-board/` (or `$XDG_CACHE_HOME`), one file
per project and board, readable only by you. To clear it:

```bash
rm -rf ~/.cache/odevvy.gitlab-board
```

## Requirements

- Omarchy 4.0.6 or later
- `glab`, signed in with `glab auth login` (check with `glab auth status`)
- `jq`
- A Nerd Font (Omarchy ships one)

`glab` handles all authentication. Every read is a `glab api --method GET`
request. There are two writes: a single `PUT` to the issue when you drop a card
on another column, and a single `POST` to the issue's notes when you post a
comment. Both need a token with the `api` scope (what `glab auth login` asks
for by default). The plugin never reads, stores, or prints a token, and
it discards glab's stderr. A glab call that hasn't answered after 30 seconds is
stopped; a comment or move that times out may still have reached GitLab, so
the plugin reloads to show what happened.

## Install

```bash
omarchy plugin add <this-repo-url> --enable
# or, from a local checkout:
omarchy plugin add "$PWD" --enable
```

## Settings from the command line

```bash
omarchy bar set odevvy.gitlab-board defaultProject group/project
omarchy bar set odevvy.gitlab-board refreshIntervalSec 120
```

## board-fetch

`board-fetch` is the helper the widget runs. It prints one JSON object.

```bash
./board-fetch [board] [--project P] [--board ID]   # board columns (the default), also saved
./board-fetch cached [--project P] [--board ID]    # that saved copy, no GitLab call
./board-fetch projects                            # projects you are a member of
./board-fetch boards --project P                  # boards of a project
./board-fetch issue --project P --iid N           # one issue with its description
./board-fetch notes --project P --iid N           # its comments, oldest first
./board-fetch move --project P --board ID --iid N --from L --to L
                                                  # move an issue (a write)
./board-fetch comment --project P --iid N <file   # post stdin as a comment (a write)
# all of them accept --hostname HOST (default gitlab.com)
```

`move` takes list ids, not label names: `L` is `open`, `closed`, or the
numeric id of a label list on that board (the board output gives each label
column a `listId`). It loads the board and the issue from GitLab (two GETs),
looks the label names up on the board, refuses anything else (unknown or
non-label lists, a hidden Open or Closed list, labels with commas, a
non-numeric issue), answers `{"state": "stale"}` without writing when the
issue is no longer in `--from`, and only then sends one
`PUT /projects/:id/issues/:iid` with `add_labels`, `remove_labels` and/or
`state_event`. The body goes to glab on stdin as JSON, so glab never expands
`@file` or `:placeholder` in it. All reads go through one GET-only function;
`tests/run.sh` checks that no read command ever sends anything else.

`notes` asks for the newest 100 notes (`sort=desc`, `per_page=100`, GitLab's
page maximum), drops system notes, and returns the rest oldest first with
`more: true` when the page was full. That's enough for v0.1.5; longer threads
would need pagination.

`comment` reads the comment from stdin, refuses it if it's empty or only
whitespace (before any glab call), and sends one
`POST /projects/:id/issues/:iid/notes` with `{"body": ...}` as JSON on glab's
stdin. The text never goes on a command line or into a log.

Requests per board refresh: one for the boards (which include their lists),
the open issues (paginated), and one for the last 20 closed issues. The closed
request is skipped when the board hides Closed. The issue requests ask for
label details, so label colors don't need an extra request.

## Tests and debugging

```bash
tests/run.sh                            # board-fetch fixture tests with a fake glab
node --test tests/logic.test.js         # Logic.js: move maths, ages, labels, Markdown
./board-fetch | jq                      # what the widget sees
journalctl --user -t omarchy-shell -f   # shell log (QML errors)
omarchy plugin validate .
```

The QML files hold the views. The logic they share that needs no Qt (where a
moved card lands, age labels, label text colors, the Markdown renderer) lives
in `Logic.js`, which `tests/logic.test.js` loads under Node, as Omarchy's own
panels do with their `Model.js`. CI runs both test suites.

Saving a file under `~/.config/omarchy/plugins/` reloads the plugin.

## Roll back

To go back to v0.1.4 (no comments), check out the previous version and update:

```bash
git checkout main   # or the v0.1.4 commit
omarchy plugin update odevvy.gitlab-board
omarchy-restart-shell
```

Comments you already posted stay on GitLab; delete them there if needed.

## Remove

```bash
omarchy plugin remove odevvy.gitlab-board
```
