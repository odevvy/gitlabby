# GitLabby for Omarchy

> The [GitHub repository](https://github.com/odevvy/gitlabby) is a read-only mirror. Please open issues and merge requests on [GitLab](https://gitlab.com/firelink21/gitlabby). GitHub pull requests are not accepted.

A bar icon (plugin id `odevvy.gitlabby`) that opens a GitLab issue board in a popup: the board's lists as
columns in their label colors, issue details with comments and labels, and
drag-to-move.

## Install

```bash
omarchy plugin add https://gitlab.com/firelink21/gitlabby.git --enable
# or over SSH:
omarchy plugin add git@gitlab.com:firelink21/gitlabby.git --enable
# or, from a local checkout:
omarchy plugin add "$PWD" --enable
```

Needs Omarchy 4.0.6 or later, `jq`, a Nerd Font (Omarchy ships one), and the
GitLab CLI `glab`.

The repository moved from `firelink21/omarchy-gitlab-board` to
`firelink21/gitlabby` (v0.1.113); the plugin id stays `odevvy.gitlabby`. An
existing install keeps working through GitLab's redirect; to point it at the
new path:

```bash
git -C ~/.config/omarchy/plugins/odevvy.gitlabby remote set-url origin https://gitlab.com/firelink21/gitlabby.git
omarchy plugin update odevvy.gitlabby
```

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

## Report a problem

Open an issue on GitLab (not GitHub):

- [Bug](https://gitlab.com/firelink21/gitlabby/-/issues/new?issuable_template=Bug)
- [Feature](https://gitlab.com/firelink21/gitlabby/-/issues/new?issuable_template=Feature)
- [Question](https://gitlab.com/firelink21/gitlabby/-/issues/new?issuable_template=Question)

See [CONTRIBUTING.md](CONTRIBUTING.md). **Never paste a token or password.** The project is private for now, so only members can file issues.

## Default board and starred boards

Every shell start opens the default board; browsing other boards doesn't
change it. The header shows a filled star on the default board. Everywhere
else, **☆ Default** opens a small menu: go to your default, or make the board
on screen the default.

The title (`group/project / Board ▾`) opens your **starred boards** jump list
(the default is always listed, marked Default). Pick a row to switch, or
**Browse all projects…** for the full picker. In the picker's board step, the
star adds or removes a board from that list (it no longer sets the default).
A long list scrolls inside the menu, with **Browse all projects…** pinned at
the bottom; the arrow keys keep the selected board in view.

## Popup

- The title, `group/project / Board ▾`, opens starred boards (or the picker when
  none are set). **Browse all projects…** still opens the picker: pick a project
  (type to filter, up to 500, most recently active first), then one of its boards.
  A filter that hides every project says `No projects match this filter.` with
  a **Clear filter** action; an account with no projects says `No projects
  found for this account.`
- After the title, the **Board**, **Merge requests** and **To-do** tabs switch
  between the three views (the current one is underlined; the Merge requests tab
  shows how many wait on your review, the To-do tab how many to-dos are pending). On the board, the columns and bots buttons come right after the
  tabs; on Merge requests and To-do the `read-only` chip sits there instead.
  On the right: `Updated`, then the refresh, keyboard and settings buttons,
  in the same place on every view. Buttons and tabs are 28-point targets, and
  every tip names its key. The icon buttons have no fill: a dim icon is off,
  an orange one is on (a shown row, Settings open), and hovering brightens it
  (an off icon to white, an on one to a lighter orange). Tabs get a faint fill
  on hover. Tips come after
  half a second of hovering, and never while a column folds, so a strip or
  header that slides under the cursor doesn't flash one. When the screen is
  too narrow for that, `Updated` shrinks first, then the tab reads `MRs`.
- Click a column header to collapse it to a narrow strip (count, colour dot,
  name). The columns button in the header (the columns icon right after the tabs, with
  a number when columns are hidden) opens a row of chips under the bots: click one to hide or show
  that column. The row stays closed until you open it.
- `y` copies the link of the focused card, the open issue or the focused
  merge request; a right-click on a card or a merge request does the same.
  It goes to the clipboard with `wl-copy` (Omarchy installs `wl-clipboard`),
  https links only, and `Updated` reads `Copied #12` (`Copied !34` for a merge
  request) for a moment. Only the left button drags, opens or picks a card.
- Click an issue for its details: state, labels, author, ages, assignees,
  milestone, the description, the comments and a box to add one, and an
  "Open in browser" link ("Open in app window" when Settings opens links in an
  app window; the "Truncated" link follows it too). A thin bar slides under the title while it loads.
- Board issues still open inside GitLabby. Merge requests, to-dos, and the
  issue's Open action leave the plugin; their rows show a quiet ↗ and a tip saying
  where they open. They open in a browser tab, or in an app window of their
  own (no tabs or address bar): Settings > **Open links in**. Browser tab runs
  `omarchy-launch-browser`, App window `omarchy-launch-webapp`, which needs a
  Chromium-based browser (Chrome, Brave, Edge, Opera, Vivaldi, Helium; with
  another default it uses Chromium). Either way only `https://` links open,
  and the popup closes. Alert notifications open theirs the same way.
- The gear opens the settings in four sections split by thin lines:
  General (the refresh interval, and which columns start collapsed), Bots
  (the bots of the project on screen, see [Who's busy](#whos-busy)), Alerts,
  and Account (who is signed in). A ticked box has an orange outline and tick.
- The popup keeps one size in every view: the board's width (at least 760
  points, at your Omarchy scale) and 640 points tall, or less when the screen
  has less room under the bar. The board, an issue, the merge requests,
  Settings and the keyboard shortcuts fit inside it or scroll inside it, so
  switching views never resizes the popup. Only folding or hiding columns
  changes its width. When Settings, the shortcuts or an issue go on below
  the popup's edge, that edge fades into the background; at the end the fade
  is gone.
- Every icon button says what it does when you point at it, with its key in
  brackets when it has one: `Refresh (r)`, `Settings (s)`,
  `Keyboard shortcuts (?)`, `Hide bots (b)` / `Show bots (b)` (only when
  the project has bots: it hides the bots row and the board moves up), `Switch project or board (p)`,
  `Back to the board (Esc)`; in an issue `Open in browser (o)` (or `Open in app window (o)`),
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
Pointing at `Updated 14:05` names your setting, then what the pace did to it
and why, e.g. `Every 2 min · slowed to 4 min, nothing changed lately` or
`Every 2 min · sped up to 1 min, cards moved recently`; at your setting it says
just `Every 2 min`. With a card or bot alert on it adds `also while closed, for alerts`.
Settings notes the slowdown under **Refresh every**. Refresh, `r` and a right-click
always fetch at once.
While a refresh runs, a small dot breathes in the header and the board stays
usable, in every view. For the timer's refresh in the background the dot is
grey and the status keeps `Updated 14:05`. For one you asked for (Refresh,
`r`, a right-click, or the merge-request list loading in its view) the dot is
orange, the refresh icon spins and the status says `Updating…`, for at least
half a second, then `Updated` with the new time. Opening the popup fetches the
board when its last fetch is older than your **Refresh every** setting (the
slowdown doesn't delay it) and looks the same: `Updating…` and the spinning
icon. When the board is newer than that, nothing is fetched and the status says
`Up to date · 14:05` for 2 seconds, then `Updated 14:05` (a refresh, another
view or closing the popup ends it sooner). Merge requests and To-do use the same
rule when you open them. The first load shows the skeleton
board and the spinning icon. A refresh
that comes due while you hold a card waits until you let go.

With several monitors, every bar has its own copy of the widget, but they
share one refresh (the plugin's service, `BoardService.qml`, which the shell
loads once). A board is fetched at most once at a time for the whole shell:
every screen showing it shows the dot and gets the same answer. The timer
reuses the last answer when that board was fetched less than an interval ago
on any screen, and opening the popup when it was fetched less than your
setting ago; Refresh, `r` and a right-click
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
  lists read the first 500 open issues, in board order. Below that their
  counts are exact. With more, a line at the top of the popup says "First 500
  open issues shown · View all on GitLab ↗", which opens the board on GitLab,
  and the counts cover only the issues shown. An issue shows in every list
  it has the label of, so the board's cards (Closed aside) also share one
  budget of 500: lists that fit stay whole, and the longest ones are cut to
  the same length. A cut list ends with "Showing 240 of 360 · See all on
  GitLab ↗" (its open issues on GitLab), and the top line reads "Board
  trimmed to 500 cards", or "First 500 open issues shown, trimmed to 500
  cards" when both limits apply.
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
website. On my-group/my-project, moving an issue into approved or review wakes the bots.

### Ask before moving

For boards where a move matters, list the project in `confirmMoves` (none by
default). A drop or `Shift+H`/`Shift+L` then waits under the header: "Move #112
from in progress to review?" with what it changes on GitLab ("This changes its
status label on GitLab."), and **Move** (`Enter`) or **Cancel** (`Escape`).
The card stays where it is until you confirm, and the board doesn't refresh
under the question.

```bash
omarchy bar set odevvy.gitlabby confirmMoves '["my-group/my-project"]' --json
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
left out. They reload each time you open the issue. The last 10 issues you
opened stay in memory: reopening one shows its description and comments at
once (the card's own title, labels and state win), while the fresh copies load;
editing, commenting and moving wait for those. Nothing is written to disk, and
signing out forgets them.

While an issue loads, its title, labels and age show at once from the card;
the state, Edit labels and Close issue keep their place and fade in once the
issue is in, so nothing jumps. A load that takes longer than a quarter
second shows one quiet line, the project picker's spinner and `Loading…`:
where the description goes, then under Comments until they are in. A
quicker one shows nothing in between.

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
- The thread shows the newest 100 notes (one GitLab page), at most 100,000
  characters of them, and says when there are more ("Older ones are on GitLab
  ↗" opens the issue). A comment longer than 4,000 characters shows its start,
  cut at a line break, and "Trimmed: first 4,000 of 25,310 characters · Read it
  all on GitLab ↗", which opens that comment. Editing, deleting, replies and
  Markdown preview: use GitLab.

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
under the header can show who is busy (10 points under the title and 10
above the columns, or above the column chips when they're open). It's off until you add a bot for the
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
check boxes under **Busy when its card is in**, above the list titled
**On** and the project, turn a column off or on (Open and Closed never count). The list reads
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
  "my-group/my-project": {
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
omarchy bar set odevvy.gitlabby bots '{"my-group/my-project":{"busyLists":["approved","in progress","review"],"bots":[{"name":"App UI","label":"app-ui"},{"name":"API Engineer","label":"api"},{"name":"Auth & Mail","label":"auth-mail"},{"name":"Product Lead","label":""},{"name":"Spec QA","list":"review"}]}}' --json
```

Remove it with `omarchy bar set odevvy.gitlabby bots '{}' --json`.

## Alerts

Settings > Alerts has three check boxes for the project on screen, all off by
default and saved per project (`alerts` in the widget's settings):

- **A card enters review**: a card appears in the board's `review` column.
  Several in one refresh make one notification (`3 cards entered review`).
- **A bot stops working**: a bot of [Who's busy](#whos-busy) had a card in a
  working column and now has none there.
- **A pipeline on my MR finishes**: the head pipeline of one of your open merge
  requests in this project was running or pending at the last look and has now
  passed or failed (`Pipeline passed on !42`, body `!42 <title> · <project>`),
  or it is another pipeline than last time (GitLab's pipeline id, so a re-run
  that ended the same way counts) that ended since. Canceled ones, and merge
  requests new to the list, say nothing. Several in one refresh make one
  (`2 pipelines finished`, `!42 passed, !44 failed · <project>`); a click opens
  the merge request, or the project's merge requests for several. Each
  background refresh asks for it with one small read-only GraphQL query
  (`board-fetch pipes`: your open merge requests in the project, newest 20,
  each with its head pipeline's id, status and link), only while the box is
  on; with only this box on, that query is all that runs, not the board.

They come as Omarchy notifications under the app name `GitLabby`, low
urgency, so Do Not Disturb holds them (they wait in the notification
history). Clicking one opens the issue or merge request, or the board for
several cards or a bot (the project's merge requests for several pipelines), as Settings > **Open links in** says: a browser tab
(`omarchy-launch-browser`) or an app window (`omarchy-launch-webapp`); https
links only. After one, the bar icon gets a small accent dot at its top right
(the tip adds `an alert came`), on every screen, until you open the popup on
any of them. An alert that comes while a popup shows the board doesn't light
it; one the popup's own opening refresh brings, or one that comes while it
shows another view, does. Settings >
General > **Keep the bar icon unlit** turns the dot off (the alerts still
come). Your own moves aren't announced back to you. Nothing is
announced on the first load after a shell start, after switching boards, or
for the first good refresh after a failed one (changes in between are only
compared from then on).

The icon's tip adds a second line with the last alert sent this shell
session, on any screen, such as `Last alert: #42 in review · 14:26`
(none before the first). Settings > Alerts says the same under the check boxes
while one is on: `Checking every 1 min. Last alert: …`, or `Checking every
1 min. No alerts since the shell started.` Signing out forgets it.

While a card or bot alert is on, the board also refreshes with the popup
closed, once its last fetch is older than your interval: never at the slowed
adaptive pace (see [Popup](#popup)), as a short stay in review between two slow
looks would be missed. The pipeline alert's query runs at the same interval, popup open
or not. With all three off there is no background refresh. However many monitors,
there is one refresh and one notification per event (the plugin's service).

## Merge requests

The **Merge requests** tab in the header (after the title), or `m`,
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
branch, and the author (or how many reviewers yours have). The `All projects`
(the default) and `This project` (the board's) tabs pick the scope; the
current one is underlined. A quiet `read-only` chip follows the header's
tabs, and the header's `Updated 14:05` says when the lists were read
(`Updating…` while they load). The focused row has
a faint fill and a short orange bar on its left edge.

It is read-only: `Enter`, `o` or a click opens the merge request in the
browser; `y` or a right-click copies its link. The lists load when you open the view, switch its scope, or press
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

## To-do

Lists are capped (Waiting on your review and Yours at 10, To-dos at 30,
Assigned to you at 20). When a section is full, its header reads `Latest N`
instead of a count and shows **View all on GitLab** at the right, which opens
the matching GitLab list (filtered to the current project scope; to-dos always
open your dashboard to-do list). Tab reaches it; Enter or Space opens it.

The **To-do** tab in the header (after Merge requests), or `t`, shows two
lists:

- **To-dos**: your pending GitLab to-dos, newest first, up to 30. Each row
  says why in a few words: `mentioned you`, `review requested`, `pipeline
  failed`, `assigned you`, `can't merge`, `approval required`, ... (a failed
  pipeline or a conflict in red), then `#issue` or `!MR`, the title, the
  project and who did it, and how long ago.
- **Assigned to you**: open issues assigned to you, most recently changed
  first, up to 20. On the right, the issue's column on this board when it is
  in this board's project and one of its labels is a column here; else `open`.

`All projects` (the default) and `This project` pick the scope, as on Merge
requests. The first load is one spinner row; an error stays on that row with
`Press r to try again.` The header's `Updated 14:05` says when the lists were
read, and a quiet `read-only` chip follows the tabs.

It is read-only: nothing is marked done. `Enter`, `o` or a click opens the
issue or merge request as **Open links in** says (https links only); `y` or a
right-click copies its link. The lists load when you open the view, switch its
scope, or press `r`; never when the popup opens and never in the background.
An answer under a minute old is reused, so a second monitor shows the same
lists. The badge on the tab is how many to-dos were pending at the last look;
nothing is fetched for it. A load is one GraphQL query (`glab api graphql`, a
read-only `query`) for both lists, with your username (glab's) and the project
as variables. Without a username, or if the query fails, times out or answers
something unexpected, it is two REST GETs instead (`todos?state=pending`,
`issues?scope=assigned_to_me`). It needs no more glab scopes than reading the
board.

## Cards and colors

- Label chips use each label's GitLab colors. Column headers have a dot in the
  label's color (the accent for Open, muted for Closed), the name as GitLab
  writes it, and the count as a quiet number; columns and cards have no outline
  at rest. Secondary text ("Updated", counts, ages, "No issues") is quieter
  than the titles.
- Cards show the title first, then one quiet line: the issue number, up to
  three assignee avatars (two plus `+N`), the comment count, and the age (`45m`, `3h`, `4d`, `2w`, `6mo`, `1y`). Avatars show initials
  until the picture is in, or if it never comes. Only pictures on your GitLab
  server are shown (others, Gravatar's too, stay initials). board-fetch fetches
  them with curl, never following a redirect, at most 64 KB each, and keeps
  them in memory only; Qt never loads an avatar URL itself.
  General > **Show avatars** (on by default) turns them off: every
  avatar is then its initials circle and no picture is requested.
  Every avatar is cut round by one shared mask, so a full board keeps a
  single mask texture instead of one per avatar.
- Collapsing or hiding a column animates in 150 ms: the column, the popup's
  edge and its height move together, the cards fade out before the strip
  fades in (and the other way round), and a refresh that lands meanwhile
  waits for it. Switching boards or views stays instant. Cards lift slightly
  on hover.
- A refresh redraws only the cards that changed (a new comment count, a card
  that moved); the rest of the board stays as it is, hover included.
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
o.bind("SUPER + CTRL + G", "GitLabby", "omarchy-shell shell toggle odevvy.gitlabby")
```

Omarchy's own `SUPER + CTRL + 1`…`9` also open the right section's bar panels by
position. In the popup the keyboard cursor shows after the first move.
`Tab` and `Shift+Tab` move an outline across the popup's buttons, tabs, the
title, the list scopes and the picker's stars; `Enter` or `Space` presses the outlined one and `Esc` drops the
outline. `Ctrl+Tab` and `Ctrl+Shift+Tab` go to the next or previous bar panel.

The keyboard button in the header (between refresh and the gear), or `?`,
shows these in the popup, laid out like Settings: each group in a soft card,
each shortcut on one line, with a quiet note after some (`asks first`).

`Open in browser` below reads `Open in app window` in the popup's own key list
when Settings opens links in an app window.

**Board**

| Key | Action |
| --- | --- |
| `h j k l` / `← ↓ ↑ →` | Move between cards |
| `Enter` / `Space` | Open the issue |
| `o` | Open in browser |
| `y` | Copy the link · or right-click |
| `Shift+H` / `L` | Move left / right · asks first |
| `v` | Pick for bulk · or Ctrl+click |
| `b` | Show or hide the bots |
| `r` | Refresh |

**Picked cards**

| Key | Action |
| --- | --- |
| `Shift+H` / `L` | Move them left / right |
| `x` | Close, or reopen if all closed |
| `e` | Add a label |
| `Enter` / `Space` | Run the action shown · or its key |
| `Esc` | Step back or stop · else unpick |

**Confirm a move or a close**

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Yes |
| `Esc` | Cancel |

**Setup panel**

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Its main button |
| `r` | Try again |

**Header menus**

| Key | Action |
| --- | --- |
| `j k` / `↓ ↑` | Move the selection |
| `Enter` / `Space` | Choose it |
| `Esc` | Close the menu |

While a header menu is open (starred boards, Default), other keys stay with
the menu and do not reach the board. Hovering a row selects it too.

**Anywhere**

| Key | Action |
| --- | --- |
| `p` | Project and board |
| `s` | Settings |
| `m` | Merge requests |
| `t` | To-do |
| `?` | These shortcuts |
| `Tab` / `Shift+Tab` | Next / previous control |
| `Ctrl+Tab` | Next bar panel |
| `Ctrl+Shift+Tab` | Previous bar panel |
| `Esc` | Back to the board, then close |

**Issue**

| Key | Action |
| --- | --- |
| `o` | Open in browser |
| `y` | Copy the link |
| `c` | Write a comment |
| `e` | Edit labels |
| `x` | Close or reopen · asks first |

**Comment box**

| Key | Action |
| --- | --- |
| `Ctrl+Enter` | Post |
| `Esc` | Leave the box |

**Merge requests**

| Key | Action |
| --- | --- |
| `j k` / `↓ ↑` | Move between them |
| `Enter` / `o` | Open in browser |
| `y` | Copy the link · or right-click |
| `r` | Refresh the lists |

**To-do**

| Key | Action |
| --- | --- |
| `j k` / `↓ ↑` | Move between them |
| `Enter` / `o` | Open in browser |
| `y` | Copy the link · or right-click |
| `r` | Refresh the lists |

**Scrolling**

| Key | Action |
| --- | --- |
| `j k` / `↓ ↑` | Scroll · settings, shortcuts, an issue |

**Pickers and filters**

| Key | Action |
| --- | --- |
| `j k` / `↓ ↑` | Move up / down |
| `Ctrl+j` / `k` | The same while typing a filter · or Ctrl+n / p |
| `Enter` | Pick the row or first match |
| `Esc` | Close the picker or form |

**Outlined control**

| Key | Action |
| --- | --- |
| `Enter` / `Space` | Press it, or tick the box |
| `h l` / `← →` | Pick a segment in Settings |
| `Esc` | Drop the outline |

In Settings, `Tab` stops on Refresh every, Open links in and each check box,
and scrolls the page to the one it outlines.

## Saved state

Settings live on the widget's entry in `~/.config/omarchy/shell.json`:

| Key | Meaning |
| --- | --- |
| `gitlabHost` | The GitLab server, by its bare name (default `gitlab.com`; `https://` and a trailing `/` are dropped). `http://`, a port or a path aren't accepted here (the server is then `gitlab.com`, and Settings shows the value with its error until you fix it): set those in glab's own config for the host (`api_protocol`, `api_host`, `subfolder`). Every `board-fetch` call gets it as `--hostname` |
| `defaultProject` | Default project: path or numeric id. Empty (the default): the first board you open |
| `defaultBoardId`, `defaultBoardName` | Default board; empty means the project's first board |
| `favorites` | Starred boards on gitlab.com: `[{ "project", "id", "name" }, …]` (jump list). Default `[]` |
| `serverFavorites` | Starred boards on each other server: `{ "host": [{ "project", "id", "name" }, …] }`. Default `{}` |
| `refreshIntervalSec` | Refresh interval in seconds |
| `botsHidden` | `true`: the bots row under the header is hidden (header bots button or `b`). Default `false` |
| `iconUnlit` | `true`: no dot on the bar icon after an alert (Settings > Keep the bar icon unlit). Default `false` |
| `openLinks` | Where links open: `browser` (the default; a tab, `omarchy-launch-browser`) or `app` (its own window, `omarchy-launch-webapp`; needs a Chromium-based browser). Anything else is `browser` |
| `defaultCollapsed` | Columns that start collapsed on a board you have not changed yet. Default `["closed","research","open"]`; matched case-insensitively |
| `boardStates` | Collapsed and hidden columns for each project and board, keyed `project#boardId`. Saved when the popup closes, or 2 s after the last fold |
| `confirmMoves` | Projects whose card moves ask first (see [Ask before moving](#ask-before-moving)). Default `[]` |
| `bots` | Busy markers per project (see [Who's busy](#whos-busy)). Default `{}`: no row |
| `serverDefaults` | The default board on each other server: `{ "host": { "project", "id", "name" } }`. gitlab.com's stays in `defaultProject`, `defaultBoardId` and `defaultBoardName` |
| `settingsRevision` | Set to `2` by v0.1.3 after its one-time update |

On another server than gitlab.com, the per-project keys (`bots`, `alerts`,
`confirmMoves`, `accessHintDismissed`, `boardStates`) use `host:project`
(for example `gitlab.example.com:group/app`), so each server keeps its own
and switching back finds gitlab.com's as they were. Switching server clears
the board, the project list, the account and the merge requests on screen,
and loads that server's default board (or the picker).

```bash
omarchy bar set odevvy.gitlabby defaultProject group/project
omarchy bar set odevvy.gitlabby refreshIntervalSec 120
omarchy bar set odevvy.gitlabby openLinks app
omarchy bar set odevvy.gitlabby gitlabHost gitlab.example.com   # then: glab auth login --hostname gitlab.example.com
```

The board you're browsing isn't saved. v0.1.2 drops older keys (`project`,
`boardId`, `boardName`, `collapsedColumns`, `hiddenColumns`). v0.1.3 adds Open
to `defaultCollapsed` and to every board in `boardStates`, once; expanding
Open afterwards sticks.

After each board load, `board-fetch` saves a copy of the board (the JSON the
popup shows; never anything from glab's login) in
`~/.cache/odevvy.gitlabby/` (or `$XDG_CACHE_HOME`), one file per project
and board, saved per glab account (from `glab config get user`, a local
read; no saved account gives `unknown`), so after switching accounts the
popup never starts on the other account's board. Another server's copies
start with its name (`gitlab.example.com~group%2Fapp-7@me.json`), so the same
project path on two servers never shares one. It is readable only by you.
Clear it with
`rm -rf ~/.cache/odevvy.gitlabby`.

## Your own GitLab

Settings > General starts with **GitLab server**: `gitlab.com`, or your
company's own GitLab by its bare name (`gitlab.example.com`). Typing changes
nothing yet: when the name differs from the server in use, **Use** appears
(Enter does the same) and the line under the field says where you'll go.
`https://` and a trailing `/` are dropped. `http://`, a port or a path get an
error under the field instead, and no Use: the board talks https only, and
glab keeps those details for the host (`ca_cert`, `api_host`, `subfolder`).
Esc puts the server in use back. Each server keeps its own default board,
bots, alerts and folds, so switching back finds them as they were.

When glab isn't signed in to that server, the popup says so and shows the
exact command, `glab auth login --hostname gitlab.example.com`, with
**Copy**. **Sign in** opens a terminal with it, **Try again** reloads after
you've signed in elsewhere, and **Change server** opens Settings with the
field focused. Your token stays with glab; the board never sees it.

## GitLab access

`glab` handles all authentication; the plugin never reads, stores, or prints
a token, and never shows glab's own messages. Every read is a
`glab api --method GET` request, except the Merge requests and To-do views' and the pipeline alert's
GraphQL `query` (sent as a POST, as GraphQL requires; each reads only). The writes are one `PUT` to the issue when
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
computer.` and, on the next line, `This also deletes this server's saved board
cache on this computer.` (the server's name in place of gitlab.com on another
one), with Yes, sign out and Cancel under it. Sign out itself is a 32 point
target that Tab reaches (Enter or Space asks). Yes runs
`glab auth logout --hostname gitlab.com` (that server's). That is glab's own sign-out, so glab
in your terminal is signed out too (a `GITLAB_TOKEN` in your environment still
works; glab doesn't touch it). The token stays valid on GitLab; revoke it in
your GitLab user settings if you need to. The saved boards in
`~/.cache/odevvy.gitlabby` are deleted with it, and the popup shows the
sign-in panel.

### Permissions

| What | glab token scope |
|---|---|
| Board, issues, comments, labels, Merge requests, To-do, alerts | `read_api` is enough |
| Moving cards, bulk moves, adding or removing labels, close and reopen, posting a comment | `api` |

With a `read_api` token everything reads as usual, and each write stops with
GitLab's refusal in the header (nothing changes on GitLab). `glab auth login`
asks for `api` by default; create a `read_api` personal access token and paste
it there if you only want to look.

The **Sign in** button runs `glab auth login` (with `--hostname` and your
server's name on your own GitLab) in Omarchy's floating terminal. The server
name is checked first (letters, digits, dots and dashes only), so nothing else
reaches that terminal's shell.

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
`glab auth login --hostname gitlab.com` (or your server's name) in a terminal and paste it into
glab, never into this plugin or a chat. glab keeps one token per host, so
glab in your terminal becomes read-only too. **Not now** hides the note for
that project (saved in `accessHintDismissed`); writes stay off.

If glab's token has no `api` scope, the note says so instead (no token page:
you already have a read-only token), and writes are off on every project.

## board-fetch

`board-fetch` is the helper the widget runs. It prints one JSON object whose
`state` is `ready`, `error`, `stale`, `no-glab` (glab isn't installed) or
`logged-out` (`glab auth status` says no login for the host, or GitLab
answers `401`). `glab auth status` asks GitLab (one `GET /user`), so reads
don't wait for it: it runs only after a read fails, so a sign-out or a revoked
token still shows the sign-in panel, and a network error stays an error.
Writes (move, labels, close, reopen, comment, bulk) run it first, every time,
so nothing is sent while signed out. On a public project, reads work without a
login, so a sign-out in the terminal shows there only at the next write or
failed read. (Up to 0.1.58 a passed check left a mark holding only the time in
`$XDG_RUNTIME_DIR/odevvy.gitlabby-auth-<host>`; none is written now, and
one left behind is removed at sign-out or after a failed read.)

```bash
./board-fetch [board] --project P [--board ID]   # board columns (the default), also saved
./board-fetch cached --project P [--board ID]    # that saved copy, no GitLab call
./board-fetch projects                          # projects you are a member of (up to 500)
./board-fetch whoami                            # your username (not saved)
./board-fetch mrs [--project P]                 # open MRs for your review and yours, with reviewer state
./board-fetch pipes --project P                 # your open MRs in P with their head pipelines (the pipeline alert)
./board-fetch todos [--project P]               # your pending to-dos and open issues assigned to you (To-do)
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
# all of them accept --hostname HOST (default gitlab.com): a bare name;
# https://, a path or a port is refused before glab runs
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
page was full or the thread budget ran out (then also `budgeted: true`, and
the view adds ", up to 100,000 characters"). An answer over 8 MiB is not read
but asked again with 20, 5, then 1 note per page. Each body keeps its first
4,000 characters, cut at the last line break there, with `fullLength` when cut;
the newest comments are kept up to 100,000 characters in all. `comment` refuses empty text before any glab call and sends
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
know whether there are more), skipped when the board hides Closed. The open and
closed requests run at the same time. Issues come
with label details, so colors need no extra request.

One fetch serves every monitor (see above), so a second screen adds no
requests. Cards in a Review column (at most 15) each add one
`GET /projects/:id/issues/:iid/related_merge_requests`, eight at a time; those
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
(`tests/harness/stubs`; set `OGB_SCALE=1.5` for 1.5x) into PySide6,
answers its board-fetch calls with fixtures, and checks what is on screen.
`tests/mutations/` lists deliberate bugs in eight files (one per line: name,
file, from, to, sh|qml|node, test). The test column names what must fail:
`run.sh`, `logic.test.js` or a view test such as `harness/tests/run144.py`.
They need a Python with
PySide6, kept out of the system Python:

```bash
python -m venv ~/.cache/ogb-tests && ~/.cache/ogb-tests/bin/pip install PySide6-Essentials==6.12.0
export PYTHON=~/.cache/ogb-tests/bin/python
tests/harness/all.sh                                  # every view test, 4 at a time (about 1.5 min)
$PYTHON tests/harness/tests/run144.py .               # one of them
tests/mutate.sh --changed origin/main . tests/mutations/*.tsv   # per release: rows the change can affect
tests/mutate.sh --check . tests/mutations/*.tsv       # rows whose pattern or test is gone (no tests run)
ls tests/mutations/*.tsv | xargs -P 4 -n 1 bash tests/mutate.sh .   # the full sweep, weekly and before a milestone
```

`--changed` picks a row when the row itself is new or changed, when its
`from` text sits on a changed line of its file (or is gone), or when its test
changed (for sh rows: the run.sh sections it is tied to), plus the canaries
(`tests/mutate-pick.py`). A change that shifts a row's behavior from another
file is not seen there, so run the full sweep by hand weekly and before a
milestone; nothing schedules it. `HARNESS_JOBS` sets how many view tests run at once. The tests on two
screens (one service, two boards) share `tests/harness/two.py`; waits on
an animation use `Harness.until`, not a fixed sleep. A view test removes its temp copy
even when it stops early, and `all.sh` runs them in a TMPDIR of its own that
it deletes at the end. CI fails
when a mutation row no longer matches its file or names no existing test
(`tests/mutate.sh --check`). An sh row listed in `tests/mutations/sh-sections.map`
runs only the `tests/run.sh` sections named there (`RUN_ONLY`, about 3 s
instead of the whole file); mutate.sh first runs those sections on clean code,
and a row whose sections fail there, or that is not listed, runs the whole
file. A wrong section shows up as SURVIVED, so rebuild the row's entry from
the first failing check of a full run (`RUN_FAILFAST=1` names it). The rows in
`tests/mutations/canary.tsv` reword a comment and must survive; mutate.sh runs
them with every selection, and an sh row counts as killed only when run.sh
names the check that failed. A check that fails for every mutant (as the row
check inside run.sh did until 0.1.126) then shows up at once. In `board-fetch`, merge
requests and to-dos read the same way: `mrs_graphql || mrs_rest`,
`todos_graphql || todos_rest`.

`run136.py` and `run136b.py` use Omarchy's own notification script and
`NotificationLogic.js` from `~/.local/share/omarchy` (`OMARCHY_PATH` to
change it). Fonts come from the system; `OGB_FONTS` adds a font directory.

The QML files hold the views; logic that needs no Qt (where a moved card
lands, ages, label text colors, the Markdown renderer) is in `logic/`, one
file per concern (core, labels, bots, markdown, board, alerts, mrs, bulk,
access). The Node tests load them through `logic/index.js`; the QML files
import `Logic.js`, which imports each module, hands each the others it uses
and re-exports every name, as Omarchy's panels do with their `Model.js`
(one `var` per name: a QML JavaScript import can't add names in a loop).
Every settings write goes through `Board.persist(patch)`: the keys in `patch`
are set, `patch.board` replaces the default board, the rest stay as saved.
`BoardService.qml` holds what every screen shares (the board fetches, alerts, access); the Merge requests and To-do lists are each a `ScopedFetch.qml` there (fetched per scope on demand, an answer under a minute old reused). Both lists are drawn by `components/ScopedList.qml` (scope tabs, sections, cursor, open and copy); each view gives only its sections and row look, and `Board.qml` reaches them through its `lists` table. `Board.qml` keeps the board's state and its views; which key goes to which
view is in `BoardKeys.qml`. `IssueView.qml` keeps an issue's state and its
GitLab calls; `IssueLabels.qml` draws its label editor and `IssueComments.qml`
its comments. CI runs both suites on merge requests and on `main` (not on every branch push), and `tests/run.sh` checks that reads never
send anything but GET. Saving a file under `~/.config/omarchy/plugins/`
reloads the plugin.

## Update, roll back, remove

```bash
omarchy plugin update odevvy.gitlabby   # after checking out the version you want
omarchy-restart-shell
omarchy plugin remove odevvy.gitlabby
```

Moves and comments already made stay on GitLab.
