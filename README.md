# GitLab Board for Omarchy

A bar icon that opens a GitLab issue board in a popup: the board's lists as
columns in their label colors, issue details with comments, and drag-to-move.

## Install

```bash
omarchy plugin add <this-repo-url> --enable
# or, from a local checkout:
omarchy plugin add "$PWD" --enable
```

Needs Omarchy 4.0.6 or later, `jq`, a Nerd Font (Omarchy ships one), and the
GitLab CLI `glab`.

## First run

The popup walks you through setup in its body:

1. **No `glab`:** it shows the install command, `sudo pacman -S glab`, with a
   **Copy** button. Run it in a terminal, then click **Try again**.
2. **Not signed in:** **Sign in to GitLab** opens a terminal running
   `glab auth login`; answer its questions there, then reopen the popup or
   click **Try again**. The plugin never sees your password or token: glab
   keeps the login.
3. **Signed in, no project yet:** the project picker opens. The first board
   you open becomes your default.

The popup checks again only when it opens or you click **Try again**; it
never polls. Offline or GitLab errors show the reason instead of a sign-in
prompt.

## Default board

Every shell start opens the default board; browsing other boards in the
picker doesn't change it. To change it, click the star on a board's row in
the picker's board step. The header shows a star on the default board and a
**Default** button that takes you back everywhere else.

## Popup

- The title, `group/project · Board ▾`, opens the picker: pick a project (type
  to filter your 100 most recently active projects), then one of its boards.
- Click a column header to collapse it to a narrow strip; click a chip under
  the header to hide or show that column.
- Click an issue for its details: state, labels, author, ages, assignees,
  milestone, the description, the comments and a box to add one, and an
  "Open in browser" link. A thin bar slides under the title while it loads.
- The gear opens the settings: who is signed in, which columns start
  collapsed, and the refresh interval.
- The issue view, the picker and the settings have a ✕ at the top right that
  goes back to the board, like `Escape`; it stays put while the view scrolls.
  In the picker's board step, ‹ goes back to the project list.

| Input | Action |
| --- | --- |
| Left-click the icon | Open or close the popup |
| Right- or middle-click the icon | Refresh |
| Refresh button | Refresh |

The board refreshes when the popup opens and every 60 seconds (configurable)
while it's open; while it's closed, only a right- or middle-click refreshes.
The refresh icon spins while it loads, and the board stays usable. A refresh
that comes due while you hold a card waits until you let go. After a shell
start, the popup first shows the board as you last saw it ("Saved 3h ago ·
updating…"; cards can't be dragged until the fresh board arrives), or a
pulsing placeholder when nothing is saved.

The description is GitLab Markdown drawn by the plugin: headings, bold,
italic, strikethrough, links, code, lists (including task lists), quotes,
tables and rules. Raw HTML shows as text and images as links, so nothing is
loaded from the web; anything fancier (diagrams, math, `#62` references)
shows as plain text. Links use the theme's accent color, hovering one shows
where it goes, and only `https` links open. A description over 20,000
characters is cut at a line break, with a link to the rest.

## Columns

The columns are the lists on the selected GitLab board, in its order:

- **Open**: open issues in none of the board's label lists.
- **One column per label list**: open issues with that label. An issue with
  two list labels appears in both, as on GitLab.
- **Closed**: the 20 most recently updated closed issues.
- **Assignee, milestone, and iteration lists**: a "not supported yet" note.

Open and Closed are left out when the board hides them, and a board's scope
(labels, milestone, assignee, weight) limits the issues shown. A project
without boards falls back to workflow-label columns (research, todo,
approved, in progress, review, Closed, and Unlabeled when it has issues),
with each issue in the furthest-along label it has; the header says so.

## Moving issues

Drag a card onto another column to move the issue. This writes to GitLab the
same way GitLab's own board does
([Dragging issues between lists](https://docs.gitlab.com/user/project/issue_board/#dragging-issues-between-lists)):

| From \ To | Open | Label list B | Closed |
| --- | --- | --- | --- |
| Open | - | add label B | close |
| Label list A | remove label A | remove A, add B | close (labels kept) |
| Closed | reopen | reopen, add label B | - |

Other labels are never touched.

- A drag starts after a few pixels, so a click still opens the issue.
  Collapsed columns accept drops; the target lights up in its color.
- The card moves at once. If GitLab refuses (permission, network, a token
  without the `api` scope), it jumps back and the header says why.
- **Out-of-date cards are never moved.** Just before writing, the plugin
  rereads the issue and checks it's still in the column you dragged it from.
  If not (including when it's already in the target), nothing is written, the
  header says `#45 changed on GitLab. Board refreshed.`, and the board
  reloads. The check and the write are about a second apart and GitLab has no
  "only if unchanged" option, so a change inside that second can still be
  overwritten.
- One move at a time. No drops on unsupported lists, on the workflow-label
  fallback, or on the card's own column.

**Moves can set off automations.** Bots, webhooks, CI rules or triage
policies that watch labels or state react as they would to a change on the
website. On phrase41, moving an issue into approved or review wakes the bots.

To try moves safely, make a private throwaway project with a few labels and a
board list for each, pick it in the picker, drag cards around, and check the
issues on GitLab against the table. Click **Default** to go back.

## Comments

The issue view lists the comments under the description, oldest first, with
avatar, name, age and plain text; system notes ("added ~approved label") are
left out. They reload each time you open the issue.

Under the thread is a box for a new comment: **Post** or `Ctrl+Enter` sends
it, `Enter` or `Shift+Enter` adds a line, and `Escape` leaves the box.

- **Posting writes to GitLab as you**, with the usual notifications and
  anything that watches comments. It needs a token with the `api` scope; a
  read-only token gets a `403`.
- While it's on its way the box is disabled. On success the box clears and
  the thread reloads; on failure your text stays and the reason shows in red.
- Empty comments are never sent. An unsent draft survives going back to the
  same issue; opening another issue clears it.
- The thread shows the newest 100 notes (one GitLab page) and says when there
  are more. Editing, deleting, replies and Markdown preview: use GitLab.

## Cards and colors

- Label chips use each label's GitLab colors. Column headers have a dot and
  underline in the label's color (the accent for Open, muted for Closed).
- Cards show up to three assignee avatars (two plus `+N`), the comment count,
  and the age (`45m`, `3h`, `4d`, `2w`, `6mo`, `1y`). Avatars show initials
  until the image loads from GitLab's `https` URL, or if it doesn't.
- Columns slide when they collapse, and cards lift slightly on hover.

The popup card is Omarchy's, in your theme's `popups.background`. To make
every popup see-through, set an alpha in `~/.config/omarchy/shell.toml` (it
applies live; Omarchy 4.0.6 doesn't blur popups):

```toml
[popups]
background-alpha = 0.88
```

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

Settings live on the widget's entry in `~/.config/omarchy/shell.json`:

| Key | Meaning |
| --- | --- |
| `defaultProject` | Default project: path or numeric id. Empty (the default): the first board you open |
| `defaultBoardId`, `defaultBoardName` | Default board; empty means the project's first board |
| `refreshIntervalSec` | Refresh interval in seconds |
| `defaultCollapsed` | Columns that start collapsed on a board you have not changed yet. Default `["closed","research","open"]`; matched case-insensitively |
| `boardStates` | Collapsed and hidden columns for each project and board, keyed `project#boardId` |
| `settingsRevision` | Set to `2` by v0.1.3 after its one-time update |

```bash
omarchy bar set odevvy.gitlab-board defaultProject group/project
omarchy bar set odevvy.gitlab-board refreshIntervalSec 120
```

The board you're browsing isn't saved. v0.1.2 drops older keys (`project`,
`boardId`, `boardName`, `collapsedColumns`, `hiddenColumns`). v0.1.3 adds Open
to `defaultCollapsed` and to every board in `boardStates`, once; expanding
Open afterwards sticks.

After each board load, `board-fetch` saves a copy of the board (the JSON the
popup shows; never anything from glab's login) in
`~/.cache/odevvy.gitlab-board/` (or `$XDG_CACHE_HOME`), one file per project
and board, readable only by you. Clear it with
`rm -rf ~/.cache/odevvy.gitlab-board`.

## GitLab access

`glab` handles all authentication; the plugin never reads, stores, or prints
a token, and never shows glab's own messages. Every read is a
`glab api --method GET` request. The two writes are one `PUT` to the issue
when you drop a card and one `POST` to its notes when you comment; both need
the `api` scope (what `glab auth login` asks for by default). A glab call that
hasn't answered after 30 seconds is stopped; a move or comment that times out
may still have reached GitLab, so the board reloads.

**Sign out** in the settings asks first, then runs
`glab auth logout --hostname gitlab.com`. That is glab's own sign-out, so glab
in your terminal is signed out too (a `GITLAB_TOKEN` in your environment still
works; glab doesn't touch it). The token stays valid on GitLab; revoke it in
your GitLab user settings if you need to. The saved boards in
`~/.cache/odevvy.gitlab-board` are deleted with it, and the popup shows the
sign-in panel.

## board-fetch

`board-fetch` is the helper the widget runs. It prints one JSON object whose
`state` is `ready`, `error`, `stale`, `no-glab` (glab isn't installed) or
`logged-out` (`glab auth status` says no login for the host, or GitLab
answers `401`).

```bash
./board-fetch [board] --project P [--board ID]   # board columns (the default), also saved
./board-fetch cached --project P [--board ID]    # that saved copy, no GitLab call
./board-fetch projects                          # projects you are a member of
./board-fetch whoami                            # your username (not saved)
./board-fetch logout                            # glab auth logout, then delete the saved boards
./board-fetch boards --project P                # boards of a project
./board-fetch issue --project P --iid N         # one issue with its description
./board-fetch notes --project P --iid N         # its comments, oldest first
./board-fetch move --project P --board ID --iid N --from L --to L
                                                # move an issue (a write)
./board-fetch comment --project P --iid N <file # post stdin as a comment (a write)
# all of them accept --hostname HOST (default gitlab.com)
```

`move` takes list ids: `L` is `open`, `closed`, or the `listId` of a label
column in the board output. It loads the board and the issue (two GETs),
refuses anything else (unknown or non-label lists, a hidden Open or Closed,
labels with commas, a non-numeric issue), answers `{"state": "stale"}`
without writing when the issue is no longer in `--from`, and only then sends
one `PUT /projects/:id/issues/:iid` with `add_labels`, `remove_labels` and/or
`state_event`, as JSON on glab's stdin so glab never expands `@file` or
`:placeholder`.

`notes` asks for the newest 100 notes (`sort=desc`, `per_page=100`), drops
system notes, and returns the rest oldest first, with `more: true` when the
page was full. `comment` refuses empty text before any glab call and sends
one `POST /projects/:id/issues/:iid/notes`; the text never goes on a command
line or into a log.

A board refresh makes one request for the boards (with their lists), the open
issues (paginated), and one for the last 20 closed issues, skipped when the
board hides Closed. Issues come with label details, so colors need no extra
request.

## Tests and debugging

```bash
tests/run.sh                            # board-fetch tests with a fake glab
node --test tests/logic.test.js         # Logic.js: move maths, ages, labels, Markdown
./board-fetch --project group/app | jq  # what the widget sees
journalctl --user -t omarchy-shell -f   # shell log (QML errors)
omarchy plugin validate .
```

The QML files hold the views; logic that needs no Qt (where a moved card
lands, ages, label text colors, the Markdown renderer) is in `Logic.js`,
which the Node tests load, as Omarchy's panels do with their `Model.js`. CI
runs both suites, and `tests/run.sh` checks that reads never send anything but
GET. Saving a file under `~/.config/omarchy/plugins/` reloads the plugin.

## Update, roll back, remove

```bash
omarchy plugin update odevvy.gitlab-board   # after checking out the version you want
omarchy-restart-shell
omarchy plugin remove odevvy.gitlab-board
```

Moves and comments already made stay on GitLab.
