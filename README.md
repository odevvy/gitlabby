# GitLab Board for Omarchy

A bar icon that opens a GitLab issue board for one project (default
`firelink21/phrase41`).

Columns: **research, todo, approved, in progress, review, closed**, plus
**unlabeled** (open issues with none of the workflow labels), shown only when
it has issues.

- An open issue goes in the furthest-along workflow label it has:
  `review` > `in progress` > `approved` > `todo` > `research`. Label names must
  match exactly (lowercase).
- **closed** shows the 20 most recently updated closed issues.
- Each row shows `#iid`, the title, and label chips. Click a row to open the
  issue in your default browser.

## Controls

| Input | Action |
| --- | --- |
| Left click icon | Open or close the board |
| Right or middle click icon | Refresh |
| Refresh button in the popup header, or `r` | Refresh |
| Click a column header | Collapse it to a narrow strip (click again to expand) |
| Click a chip in the popup header | Show or hide that column |
| `Escape` | Close |

It refreshes every 60 seconds and each time the popup opens. Collapsed and
hidden columns are saved on the widget's entry in `~/.config/omarchy/shell.json`
(`collapsedColumns`, `hiddenColumns`). The popup never grows wider than the
screen; a wide board scrolls sideways.

## Requirements

- Omarchy (quattro) with shell plugin support
- `glab`, signed in: `glab auth login` (check with `glab auth status`)
- `jq`
- A Nerd Font (Omarchy ships one)

Auth is handled entirely by `glab`. The plugin makes read-only `glab api`
GET requests, never reads or stores a token, and discards glab's stderr.

## Install

```bash
omarchy plugin add <this-repo-url> --enable
# or, from a local checkout:
omarchy plugin add "$PWD" --enable
```

## Settings

```bash
omarchy bar set odevvy.gitlab-board project group/project
omarchy bar set odevvy.gitlab-board refreshIntervalSec 120
```

## Debugging

```bash
./board-fetch | jq                       # what the widget sees
./board-fetch --map open.json closed.json  # map saved API responses offline
journalctl --user -t omarchy-shell -f    # shell log (QML errors)
omarchy plugin validate .
```

Saving a file under `~/.config/omarchy/plugins/` reloads the plugin.

## Remove

```bash
omarchy plugin remove odevvy.gitlab-board
```
