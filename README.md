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

## Popup

- The title, `group/project · Board ▾`, opens the picker. Pick a project (type
  to filter your 100 most recently active projects), then one of its boards.
- Click an issue to see its details: state, labels, assignees, author,
  milestone, and created and updated times (in your local time). Below that is
  the description, rendered as Markdown. The view also has an "Open in browser"
  link.
- The gear opens the settings: which columns start collapsed, and the refresh
  interval.
- Click a column header to collapse it to a narrow strip. Click a chip under
  the header to hide or show that column.

| Input | Action |
| --- | --- |
| Left-click the icon | Open or close the popup |
| Right- or middle-click the icon | Refresh |
| Refresh button, or `r` on the board | Refresh |
| `Escape` | Go back to the board; on the board, close |

The board refreshes every 60 seconds (configurable) and each time the popup
opens. A wide board scrolls sideways.

## Saved state

Everything is saved on the widget's entry in `~/.config/omarchy/shell.json`:

| Key | Meaning |
| --- | --- |
| `defaultProject` | Default project: path or numeric id |
| `defaultBoardId`, `defaultBoardName` | Default board; empty means the project's first board |
| `refreshIntervalSec` | Refresh interval in seconds |
| `defaultCollapsed` | Columns that start collapsed on a board you have not changed yet. Default `["closed","research"]`; matched case-insensitively |
| `boardStates` | Collapsed and hidden columns for each project and board, keyed `project#boardId` |

The board you're browsing isn't saved. Older keys (`project`, `boardId`,
`boardName`, `collapsedColumns`, `hiddenColumns`) are dropped the first time
v0.1.2 saves.

## Requirements

- Omarchy 4.0.6 or later
- `glab`, signed in with `glab auth login` (check with `glab auth status`)
- `jq`
- A Nerd Font (Omarchy ships one)

`glab` handles all authentication. The plugin only makes read-only
`glab api --method GET` requests. It never reads, stores, or prints a token,
and it discards glab's stderr.

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
./board-fetch [board] [--project P] [--board ID]   # board columns (the default)
./board-fetch projects                            # projects you are a member of
./board-fetch boards --project P                  # boards of a project
./board-fetch issue --project P --iid N           # one issue with its description
# all of them accept --hostname HOST (default gitlab.com)
```

Requests per board refresh: one for the boards (which include their lists),
the open issues (paginated), and one for the last 20 closed issues. The closed
request is skipped when the board hides Closed.

## Tests and debugging

```bash
tests/run.sh                            # board-fetch fixture tests with a fake glab
./board-fetch | jq                      # what the widget sees
journalctl --user -t omarchy-shell -f   # shell log (QML errors)
omarchy plugin validate .
```

Saving a file under `~/.config/omarchy/plugins/` reloads the plugin.

## Remove

```bash
omarchy plugin remove odevvy.gitlab-board
```
