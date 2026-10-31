# GitLab Board for Omarchy

A bar icon that opens a GitLab issue board in a popup: the board's lists as
columns in their label colors, issue details with comments and labels, and
drag-to-move.

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

The popup checks again only when it opens or you click **Try again** (or press `r`); it
never polls. Offline or GitLab errors show the reason instead of a sign-in
prompt.

## Default board

Every shell start opens the default board; browsing other boards in the
picker doesn't change it. To change it, click the star on a board's row in
the picker's board step. The header shows a star on the default board and a
**Default** button that takes you back everywhere else.

## Popup

- The title, `group/project / Board ▾`, opens the picker: pick a project (type
  to filter your projects, up to 500, most recently active first), then one of its boards.
- Click a column header to collapse it to a narrow strip (count, colour dot,
  name). The columns button in the header (the columns icon left of refresh, with
  a number when columns are hidden) opens a row of chips under the bots: click one to hide or show
  that column. The row stays closed until you open it.
- Click an issue for its details: state, labels, author, ages, assignees,
  milestone, the description, the comments and a box to add one, and an
  "Open in browser" link. A thin bar slides under the title while it loads.
- The gear opens the settings, in this order: the refresh interval, which
  columns start collapsed (a row of check boxes), the bots of the project on
  screen (see [Who's busy](#whos-busy)), and who is signed in.
- The popup is as tall as the board needs, up to 640 points (at your Omarchy
  scale). Settings and the keyboard shortcuts aren't held to that: they grow
  to their full height when the screen has room under the bar, and scroll
  only when it doesn't, as on a short laptop screen. Going back to the board
  returns the popup to the board's height.
- Every icon button says what it does when you point at it, with its key in
  brackets when it has one: `Refresh (r)`, `Settings (s)`,
  `Keyboard shortcuts (?)`, `Switch project or board (p)`,
  `Back to the board (Esc)`; in an issue `Open in browser (o)`,
  `Edit labels (e)` and `Close issue (x)`.
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
The pace adapts to the board: after a card moves, comes, goes or changes
labels, it refreshes twice as often (never under 30 s); once two refreshes in
a row bring no change it is back at your setting, and after every two more
quiet ones it waits twice as long, up to 4x your setting. While cards sit in
an `in progress` (or `doing`) column it never slows past your setting.
Pointing at `Updated 14:05` says the current pace and why, e.g.
`Refreshes every 30 s while open · cards moved recently`. Refresh, `r` and a
right-click always fetch at once.
While any refresh runs (yours or the timer's, or the merge-request list
loading in its view), a thin bar slides along under the header and the
refresh icon spins, in every view; the header says `Refreshing…` (instead
of `Updated 14:05`) and the board stays usable. A refresh
that comes due while you hold a card waits until you let go.

With several monitors, every bar has its own copy of the widget, but they
share one refresh (the plugin's service, `BoardService.qml`, which the shell
loads once). A board is fetched at most once at a time for the whole shell:
every screen showing it says `Refreshing…` and gets the same answer. Opening
the popup or the timer reuses the last answer when that board was fetched
less than an interval ago on any screen; Refresh, `r` and a right-click
always fetch, unless a fetch of that board is already running, which they
join. Under a replacement bar (no plugin services), each copy fetches on its
own as before. After a shell
start, the popup first shows the board as you last saw it ("Saved 3h ago ·
updating…"; cards can't be dragged until the fresh board arrives), or a
pulsing placeholder when nothing is saved (as wide as that board, or the last
one, was earlier in the session).

A refresh that fails (offline, GitLab down, a timeout) keeps the board on
screen and the header says `Couldn't refresh · showing 14:05`, the time of the
board you're looking at; the next refresh tries again. The full error takes
the board's place only when nothing was loaded yet. Not being signed in still
shows the sign-in panel.

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
- **Closed**: the 20 most recently updated closed issues. When there are
  more, its count reads `20+` (on the column and in the summary row) and a
  quiet line at its bottom says "Showing the latest 20 · See all on
  GitLab ↗", which opens the project's closed issues on GitLab, with the
  board's label, milestone, assignee and weight filters. Open and the label
  lists are not capped: they read every open issue, so their counts are exact.
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
- One move at a time (a move still finishing on GitLab says so). No drops on unsupported lists, on the workflow-label
  fallback, or on the card's own column.
- From the keyboard: select a card with `h j k l`, then `Shift+H` or
  `Shift+L` moves it to the nearest column on that side it can go to.

**Moves can set off automations.** Bots, webhooks, CI rules or triage
policies that watch labels or state react as they would to a change on the
website. On phrase41, moving an issue into approved or review wakes the bots.

### Ask before moving

For boards where a move matters, list the project in `confirmMoves` (none by
default). A drop or `Shift+H`/`Shift+L` then waits under the header: "Move #112
from in progress to review?" with what it changes on GitLab ("This changes its
status label on GitLab."), and **Move** (`Enter`) or **Cancel** (`Escape`).
The card stays where it is until you confirm, and the board doesn't refresh
under the question.

```bash
omarchy bar set odevvy.gitlab-board confirmMoves '["firelink21/phrase41"]' --json
```

The value is the whole list (project paths, any case); `'[]'` turns it off.

To try moves safely, make a private throwaway project with a few labels and a
board list for each, pick it in the picker, drag cards around, and check the
issues on GitLab against the table. Click **Default** to go back.

## Bulk actions

Pick several cards, then change them all with one of the single-card
actions: move to a column, add or remove a label, close or reopen.

- **Pick**: `v` picks the card under the keyboard cursor, `Ctrl+click` picks
  with the mouse; the same again unpicks. Picked cards get an accent border
  and a check. Up to 20 at a time. A bar under the header lists them with
  **Move to**, **Add label**, **Remove label**, **Close N** (or **Reopen N**)
  and **Clear**.
- **Arm**: a button, or `Shift+H`/`Shift+L` (the next column on that side of
  the cursor's), `x` (close) or `e` (add a label). Nothing is written yet. The
  bar says what will happen to which cards, grouped by where they are ("todo →
  review #20 #21"), and which are skipped and why ("already in review").
- **Confirm**: the main button, `Enter`, or the arming key again. `Esc` goes
  back to picking.
- **Run**: one card at a time, each with the same `board-fetch` write as a
  single card, so the same checks apply (an out-of-date card is not moved).
  The whole run is one `board-fetch bulk` process: the next card goes in
  after the last one answered, each with its own 40 s deadline. The sign-in
  check runs once per run, and adding or removing a label reads the board
  lists and the project's labels once, not once per card.
  The bar shows what is done and each failure with GitLab's reason. A failure
  on one card doesn't stop the rest; being signed out, glab missing, or no
  answer in time does (no answer means the write may have gone through).
  `Esc` stops after the current card.
- **Results**: "Moved 2 of 3 cards to review. 1 failed." with a line per card
  that wasn't done. **Keep it selected** picks just those again; **Done** or
  `Esc` closes the bar. The board reloads after the last write. Your own bulk
  changes don't raise desktop alerts.

Bulk actions always ask first, whatever `confirmMoves` says, and the board
doesn't refresh under the question or during the run.

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
- **Lines starting with `/` are never sent.** GitLab would run them as quick
  actions (`/close`, `/label ~review`, `/move ...`), which would bypass the
  rules above, so the box says so and Post stays off. A `/` inside a line, or
  in `backticks` at the start, is fine. Should GitLab still answer a comment
  with quick-action changes, the view says so and reloads.
- Empty comments are never sent. An unsent draft survives going back to the
  same issue; opening another issue clears it.
- The thread shows the newest 100 notes (one GitLab page) and says when there
  are more. Editing, deleting, replies and Markdown preview: use GitLab.

## Labels

**Edit labels** (right after the issue's labels, or `e`) adds and removes the
issue's other labels: `×` on a label removes it, a `+` label adds it, and the
filter narrows the list (`Enter` adds the first match, `Escape` closes it).
The filter turns on once the labels have loaded. **Done** or **Done editing**
closes it.

- **Status labels are never edited here.** A label that is a list on any of
  the project's boards or its groups' boards, or one of the workflow labels (`research`, `todo`,
  `approved`, `in progress`, `review`), in any case, is neither offered nor
  removable; it changes by dragging the card. board-fetch refuses it too.
- Each click is one write to GitLab as you (`add_labels` or `remove_labels`,
  so no other label changes) and needs the `api` scope. Only labels the
  project already has are offered, so nothing new is created.
- One change at a time. On success the issue and the board update; on failure
  the reason shows in red and the issue reloads.

## Close and reopen

**Close issue** (at the right of the labels row, or `x`) asks first ("Close #N? This closes it on
GitLab.", with **Close** and **Cancel**), then closes the issue as you. Only
its state changes: every label stays, including a status label such as
`review`, and the question names it. A closed issue shows **Reopen issue**,
which reopens it at once. On success the issue and the board update; on
failure the reason shows in red and the issue reloads. Bots, webhooks or
automations that watch the project see the close like any other.

## Who's busy

If a team of bots (or people) works the board through owner labels, a row
under the header can show who is busy. It's off until you add a bot for the
project, and it reads only the board already on screen: no extra GitLab
calls, no polling.

**In Settings** (gear, or `s`), under Bots, for the project on screen: click
**Show bot status for this board**. The new-bot form asks, one labelled row
at a time, for the bot's **Name** and what it is **Busy with**: cards with
one of the project's labels (pick it under **Label**; board columns and
labels another bot has aren't offered), every card in a column (pick it
under **Column**), or cards no bot owns (only one bot can have that; once
one does, the choice is shown but off). While **Add** is dim, the line
beside it says why: a name to give, a label or column to choose, or a name
another bot already has. The first bot turns on every label column; the
check boxes under **Count a bot as busy when its card is in**, above the
list, turn a column off or on (Open and Closed never count). The list reads
"cards labelled", "every card in" or "cards no other bot owns" per bot; ✕
removes one at once. Every change is saved right away to the same `bots`
setting, and the row under the header follows at once. A bot whose label the
project no longer has, or whose column isn't on this board, stays and is
marked. If the setting isn't a JSON object (for example set without
`--json`), Settings says so and adding a bot replaces it.

The setting itself, for a board where each builder has an owner label and a
reviewer takes everything in review:

```json
"bots": {
  "firelink21/phrase41": {
    "busyLists": ["approved", "in progress", "review"],
    "bots": [
      { "name": "App UI", "label": "app-ui" },
      { "name": "API Engineer", "label": "api" },
      { "name": "Auth & Mail", "label": "auth-mail" },
      { "name": "Product Lead", "label": "" },
      { "name": "Spec QA", "list": "review" }
    ]
  }
}
```

- `busyLists`: the label columns that count. Open, Closed and other lists
  never count.
- `{ "label": "app-ui" }`: issues in a busy list with that label. An issue
  with two owner labels counts for both bots.
- `{ "label": "" }`: issues in a busy list with none of the bots' labels.
- `{ "list": "review" }`: every issue in that list, owner or not, and only
  for this bot: an issue in review with `auth-mail` counts for Spec QA, not
  for Auth & Mail.
- `workingLists` (optional, default `["in progress"]`): where an issue makes
  its bot working rather than waiting.

Each bot gets a filled dot when it has an issue in a working list (a `list`
bot whenever its list has any), a ring when it only has issues waiting in
other busy lists (approved or review), and a dim hollow dot and a dim name
when it has none (pointing at it says `idle, nothing in a busy column`). It
keeps its place in the row. A busy dot takes the color of its column: the furthest along (rightmost
on the board) of the issues that set its state, so the working ones when any
are working. If that color is hard to see on your theme, it uses the accent.
Two issue numbers follow (hover one for its title, click it to open the
issue), then `+N` (hover for the rest). When they are all in one column it is
said once: `#8 · #9 +3 in research`, `#125 in progress`. Labels and lists match in any case.

Settings keeps every other key and project as it is (including
`workingLists`), so a hand-written value keeps working. Or set it from a
terminal (this replaces the whole `bots` value, so include every project you
use it for):

```bash
omarchy bar set odevvy.gitlab-board bots '{"firelink21/phrase41":{"busyLists":["approved","in progress","review"],"bots":[{"name":"App UI","label":"app-ui"},{"name":"API Engineer","label":"api"},{"name":"Auth & Mail","label":"auth-mail"},{"name":"Product Lead","label":""},{"name":"Spec QA","list":"review"}]}}' --json
```

Remove it with `omarchy bar set odevvy.gitlab-board bots '{}' --json`.

## Alerts

Settings > Alerts has two check boxes for the project on screen, both off by
default and saved per project (`alerts` in the widget's settings):

- **A card enters review**: a card appears in the board's `review` column.
  Several in one refresh make one notification (`3 cards entered review`).
- **A bot stops working**: a bot of [Who's busy](#whos-busy) had a card in a
  working column and now has none there.

They come as Omarchy notifications under the app name `GitLab board`, low
urgency, so Do Not Disturb holds them (they wait in the notification
history). Clicking one opens the issue, or the board for several cards or a
bot, in the browser. Your own moves aren't announced back to you. Nothing is
announced on the first load after a shell start, after switching boards, or
for the first good refresh after a failed one (changes in between are only
compared from then on).

While an alert is on, the board also refreshes with the popup closed, at its
adaptive pace (see [Popup](#popup)): up to 4x your interval when nothing
changes. With both off there is no background refresh. However many monitors,
there is one refresh and one notification per event (the plugin's service).

## Merge requests

The merge-request button in the header (left of the keyboard button), or `m`,
shows your open merge requests in two lists, newest change first, up to 10
each:

- **Waiting on your review**: merge requests where you are a reviewer.
  Drafts are left out.
- **Yours**: the ones you opened, drafts included.

Each row shows the pipeline (the same mark as on Review cards), `!number` and
title, GitLab's merge status (`Ready`, `Pipeline running`, `Changes
requested`, `Conflicts`, `Needs approval`, `Draft`, ...), every reviewer's
avatar with their review state (a check for approved, `!` for changes
requested, a speech bubble for reviewed, a pencil while reviewing; hover for
the words), and how long ago it changed. The second line has the project, the
branch, and the author (or how many reviewers yours have). `All projects` (the
default) or `This project` (the board's) picks the scope.

It is read-only: `Enter`, `o` or a click opens the merge request in the
browser. The lists load when you open the view, switch its scope, or press
`r`; nothing loads them in the background. An answer under a minute old is
reused, so a second monitor shows the same lists without asking GitLab again.
The badge on the button is how many waited on your review at the last look.
A load is one GraphQL query (`glab api graphql`, a read-only `query`; the
project goes in as a variable) for both lists, each MR's pipeline, merge
status and reviewer states. A reviewer state GitLab's docs don't list
(`MergeRequestReviewState`: approved, requested changes, reviewed, review
started, unapproved, unreviewed) sends that one MR to the REST GETs below. If
the query fails, times out or answers something unexpected, the view loads
the REST way: two list GETs plus, per row, one GET of the merge request
(pipeline and status) and one of its reviewers (their states). Either way the
rows are the same.

## Cards and colors

- Label chips use each label's GitLab colors. Column headers have a dot in the
  label's color (the accent for Open, muted for Closed), the name as GitLab
  writes it, and the count as a quiet number; columns and cards have no outline
  at rest. Secondary text ("Updated", counts, ages, "No issues") is quieter
  than the titles.
- Cards show the title first, then one quiet line: the issue number, up to
  three assignee avatars (two plus `+N`), the comment count, and the age (`45m`, `3h`, `4d`, `2w`, `6mo`, `1y`). Avatars show initials
  until the image loads from GitLab's `https` URL, or if it doesn't.
- Columns slide when they collapse, and cards lift slightly on hover.
- Cards in a column named Review (any case) show the pipeline of their merge
  request beside the age: ✓ passed (green), ✕ failed (red), ◉ running (blue),
  a clock for pending (amber), ⊘ canceled (grey). Hovering says which and on
  which MR (`Pipeline failed on !42: open it on GitLab`); clicking opens the
  pipeline in the browser, not the issue. The MR is the issue's open related
  merge request, else its latest merged one. No MR, no pipeline, a skipped or
  manual one, or one you can't see: no mark. It comes with each refresh, never
  on its own timer; a finished one (passed, failed, canceled) is reused for up
  to 2 minutes, so a new push can take that long to show.

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

The keyboard button in the header (between refresh and the gear), or `?`,
shows these in the popup.

**Board**

| Key | Action |
| --- | --- |
| `h` `j` `k` `l` or `←` `↓` `↑` `→` | Move between cards |
| `Enter` or `Space` | Open the selected issue |
| `o` | Open the selected issue in the browser |
| `Shift+H` or `Shift+L` | Move the selected card to the column on the left or right, after a confirm |
| `v` | Pick the selected card for a bulk action (Ctrl+click picks with the mouse) |
| `r` | Refresh the board |

**Confirm a move or a close**

| Key | Action |
| --- | --- |
| `Enter` or `Space` | Yes |
| `Esc` | Cancel |

**Picked cards**

| Key | Action |
| --- | --- |
| `Shift+H` or `Shift+L` | Move them to the column on the left or right |
| `x` | Close them, or reopen them when all are closed |
| `e` | Add a label to them |
| `Enter` or `Space` | Confirm the action shown (the same key again works too) |
| `Esc` | Back one step; while it runs, stop after the current card; else clear the picks |

**Anywhere**

| Key | Action |
| --- | --- |
| `p` | Choose a project and board |
| `s` | Settings |
| `m` | Merge requests waiting on your review, and yours |
| `?` | These shortcuts (or the keyboard button in the header) |
| `Tab` or `Shift+Tab` | Next or previous bar panel |
| `Esc` | Back to the board; on the board, close |

**Issue**

| Key | Action |
| --- | --- |
| `o` | Open the issue in the browser |
| `c` | Write a comment |
| `e` | Edit labels |
| `x` | Close the issue, after a confirm, or reopen it |

**Merge requests**

| Key | Action |
| --- | --- |
| `j` `k` or `↓` `↑` | Move between merge requests |
| `Enter` or `o` | Open the selected one in the browser |
| `r` | Refresh the lists |

**Comment box**

| Key | Action |
| --- | --- |
| `Ctrl+Enter` | Post the comment |
| `Esc` | Leave the box |

**Pickers and filters**

| Key | Action |
| --- | --- |
| `↑` `↓` | Move in the list (j and k too, once you're choosing a board) |
| `Enter` | Pick the selected row, or the first match |
| `Esc` | Close the picker, the label editor or the new-bot form |

**Setup panel**

| Key | Action |
| --- | --- |
| `Enter` or `Space` | Its main button |
| `r` | Try again |

Letters go to the comment box, the label filter or the picker's filter while
you type in them. While the label editor waits for the labels, letters do
nothing.

## Saved state

Settings live on the widget's entry in `~/.config/omarchy/shell.json`:

| Key | Meaning |
| --- | --- |
| `defaultProject` | Default project: path or numeric id. Empty (the default): the first board you open |
| `defaultBoardId`, `defaultBoardName` | Default board; empty means the project's first board |
| `refreshIntervalSec` | Refresh interval in seconds |
| `defaultCollapsed` | Columns that start collapsed on a board you have not changed yet. Default `["closed","research","open"]`; matched case-insensitively |
| `boardStates` | Collapsed and hidden columns for each project and board, keyed `project#boardId` |
| `confirmMoves` | Projects whose card moves ask first (see [Ask before moving](#ask-before-moving)). Default `[]` |
| `bots` | Busy markers per project (see [Who's busy](#whos-busy)). Default `{}`: no row |
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
and board, saved per glab account (from `glab config get user`, a local
read; no saved account gives `unknown`), so after switching accounts the
popup never starts on the other account's board. It is readable only by you.
Clear it with
`rm -rf ~/.cache/odevvy.gitlab-board`.

## GitLab access

`glab` handles all authentication; the plugin never reads, stores, or prints
a token, and never shows glab's own messages. Every read is a
`glab api --method GET` request, except the Merge requests view's one
GraphQL `query` (sent as a POST, as GraphQL requires; it reads only). The writes are one `PUT` to the issue when
you drop a card, add or remove a label, or close or reopen it, and one `POST`
to its notes when you comment; they need the `api` scope (what `glab auth login` asks for by
default). Each `board-fetch` run ends within 40 seconds: no single glab call
gets more than 30, and a write only starts with at least 15 seconds left
(otherwise nothing is sent and the header says GitLab is answering slowly). A
write that times out may still have reached GitLab, so the view reloads. The
popup gives up waiting after 50 seconds; should that write still be running,
the next move or bulk action says `The last change is still finishing on
GitLab. Try again in a moment.` instead of starting another. While a fetch
runs, its answers wait in a private folder in `$XDG_RUNTIME_DIR` (cleared at
logout), removed when it ends or is stopped.

**Sign out** (in the settings, beside your username) asks `Sign out of glab
on gitlab.com? This also signs glab out in your terminal and scripts on this
computer.`, then runs
`glab auth logout --hostname gitlab.com`. That is glab's own sign-out, so glab
in your terminal is signed out too (a `GITLAB_TOKEN` in your environment still
works; glab doesn't touch it). The token stays valid on GitLab; revoke it in
your GitLab user settings if you need to. The saved boards in
`~/.cache/odevvy.gitlab-board` are deleted with it, and the popup shows the
sign-in panel.

### View-only projects

The first time a project's board loads in a session, the plugin asks GitLab
once for your role there (`board-fetch access`: a `GET` of the project, and of
`personal_access_tokens/self` for the token's scopes, never the token
itself). Below Planner (Guest, Minimal or no membership), or once GitLab
refuses a change with 403, the board is view-only: dragging, bulk actions,
labels and close/reopen are off, the header says **View-only**, and a note
under the header says why. Comments stay on (Guests may comment).

The note suggests a token that can only read: **Open GitLab's token page**
opens GitLab's own page over https with the name and the `read_api` scope
filled in; you create the token there, then run
`glab auth login --hostname gitlab.com` in a terminal and paste it into
glab, never into this plugin or a chat. glab keeps one token per host, so
glab in your terminal becomes read-only too. **Not now** hides the note for
that project (saved in `accessHintDismissed`); writes stay off.

If glab's token has no `api` scope, the note says so instead (no token page:
you already have a read-only token), and writes are off on every project.

## board-fetch

`board-fetch` is the helper the widget runs. It prints one JSON object whose
`state` is `ready`, `error`, `stale`, `no-glab` (glab isn't installed) or
`logged-out` (`glab auth status` says no login for the host, or GitLab
answers `401`). `glab auth status` asks GitLab (one `GET /user`), so after it
passes it is skipped for 10 minutes: a mark holding only the time, in
`$XDG_RUNTIME_DIR/odevvy.gitlab-board-auth-<host>`. While the mark is fresh,
any failed read runs the check again, so a sign-out or a revoked token still
shows the sign-in panel; signing out from the settings removes the mark. On a
public project, reads work without a login, so a sign-out in the terminal can
take up to 10 minutes to show there.

```bash
./board-fetch [board] --project P [--board ID]   # board columns (the default), also saved
./board-fetch cached --project P [--board ID]    # that saved copy, no GitLab call
./board-fetch projects                          # projects you are a member of (up to 500)
./board-fetch whoami                            # your username (not saved)
./board-fetch mrs [--project P]                 # open MRs for your review and yours, with reviewer state
./board-fetch logout                            # glab auth logout, then delete the saved boards
./board-fetch boards --project P                # boards of a project
./board-fetch issue --project P --iid N         # one issue with its description
./board-fetch notes --project P --iid N         # its comments, oldest first
./board-fetch move --project P --board ID --iid N --from L --to L
                                                # move an issue (a write)
./board-fetch comment --project P --iid N <file # post stdin as a comment (a write)
./board-fetch labels --project P                # the labels you may edit, and the status ones
./board-fetch access --project P                # your role there (level) and the token's scopes
./board-fetch relabel --project P --iid N --add L    # add one label (a write)
./board-fetch relabel --project P --iid N --remove L # remove one label (a write)
./board-fetch close --project P --iid N         # close an issue (a write)
./board-fetch reopen --project P --iid N        # reopen it (a write)
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

`relabel` takes exactly one `--add` or `--remove`. It loads every board of
the project and, best effort, of its group and each parent group (group
boards show the project's issues too), and refuses a status label (a list
label of any of those boards, or a workflow label, in any case); `--add` also needs a label the project has. Only
then does it send one `PUT /projects/:id/issues/:iid` with just `add_labels`
or `remove_labels`, as JSON on stdin like `move`. `labels` returns the
project's labels without the status ones, plus the status list.

`close` and `reopen` send one `PUT /projects/:id/issues/:iid` with only
`state_event`, as JSON on stdin, and answer `ready` only if GitLab returns
that issue in the new state.

A board refresh makes one request for the boards (with their lists), the open
issues (paginated), and one for the last 20 closed issues (it asks for 21, to
know whether there are more), skipped when the board hides Closed. Issues come
with label details, so colors need no extra request.

One fetch serves every monitor (see above), so a second screen adds no
requests. Cards in a Review column (at most 15) each add one
`GET /projects/:id/issues/:iid/related_merge_requests`, four at a time; those
MRs carry their `head_pipeline`. Only if GitLab leaves it out, one
`GET /projects/:id/merge_requests/:iid` for that MR. These never fail the
board: a refusal, a timeout or no MR just leaves the card without a mark.
Finished pipelines are kept for 2 minutes beside the saved board
(`<board file>.pipes.json`: status, link, MR and when it was asked) and not
asked again in that time; running and pending ones are asked every refresh.

The issue view's label editor reads the project's labels once and reuses them
for every issue of that project for 5 minutes.

## Tests and debugging

```bash
tests/run.sh                            # board-fetch tests with a fake glab
node --test tests/logic.test.js         # logic/: move maths, ages, labels, Markdown
./board-fetch --project group/app | jq  # what the widget sees
journalctl --user -t omarchy-shell -f   # shell log (QML errors)
omarchy plugin validate .
```

The QML views have offscreen tests too: `tests/harness/` loads a copy of
the plugin with stand-ins for Quickshell and Omarchy's `qs.Commons`/`qs.Ui`
(`tests/harness/stubs`, and `tests/harness15` at 1.5x scale) into PySide6,
answers its board-fetch calls with fixtures, and checks what is on screen.
`tests/mutations/` lists deliberate bugs (one per line: name, file, from,
to, sh|qml|node); each must make its test fail. They need a Python with
PySide6, kept out of the system Python:

```bash
python -m venv ~/.cache/ogb-tests && ~/.cache/ogb-tests/bin/pip install PySide6-Essentials==6.12.0
export PYTHON=~/.cache/ogb-tests/bin/python
tests/harness/all.sh                                  # every view test (about 3 min)
$PYTHON tests/harness/tests/run144.py .               # one of them
tests/mutate.sh . tests/mutations/v144.tsv tests/harness/tests/run144.py
```

`run136.py` and `run136b.py` use Omarchy's own notification script and
`NotificationLogic.js` from `~/.local/share/omarchy` (`OMARCHY_PATH` to
change it). Fonts come from the system; `OGB_FONTS` adds a font directory.

The QML files hold the views; logic that needs no Qt (where a moved card
lands, ages, label text colors, the Markdown renderer) is in `logic/`, one
file per concern (core, labels, bots, markdown, board, alerts, mrs, bulk,
access). The Node tests load them through `logic/index.js`; the QML files
import `Logic.js`, which imports each module, hands each the others it uses
and re-exports every name, as Omarchy's panels do with their `Model.js`.
`Board.qml` keeps the board's state and its views; which key goes to which
view is in `BoardKeys.qml`. `IssueView.qml` keeps an issue's state and its
GitLab calls; `IssueLabels.qml` draws its label editor and `IssueComments.qml`
its comments. CI runs both suites, and `tests/run.sh` checks that reads never
send anything but GET. Saving a file under `~/.config/omarchy/plugins/`
reloads the plugin.

## Update, roll back, remove

```bash
omarchy plugin update odevvy.gitlab-board   # after checking out the version you want
omarchy-restart-shell
omarchy plugin remove odevvy.gitlab-board
```

Moves and comments already made stay on GitLab.
