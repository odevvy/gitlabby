// Favorited boards for the header jump list. Pure: no Qt. Each entry is
// { project, id, name }; empty id is a workflow-label board. The default board
// is separate (defaultProject / defaultBoardId / defaultBoardName) and is always
// merged into the jump list even when it is not in the favorites array.
function favoriteKey(entry) {
  var e = entry || {}
  return String(e.project || "").trim() + "#" + String(e.id || "")
}

// Short label for a workflow-label board (empty id): "Workflow labels (no boards)"
// and similar become "Workflow labels".
function boardLabel(name, id) {
  if (String(id || "") !== "") return String(name || "")
  var n = String(name || "").trim()
  if (n === "") return "Workflow labels"
  var cut = n.indexOf(" (")
  return cut > 0 ? n.slice(0, cut) : n
}

function jumpLabel(entry) {
  var e = entry || {}
  var project = String(e.project || "").trim()
  var name = boardLabel(e.name, e.id)
  return name !== "" ? project + " / " + name : project
}

// Favorites stored for this host: gitlab.com uses `favorites`; others use
// serverFavorites[host], matching how default boards are stored.
function hostFavorites(favorites, serverFavorites, host, onGitlabCom) {
  var raw = onGitlabCom ? favorites : (Object(serverFavorites || {})[host] || [])
  if (!Array.isArray(raw)) return []
  var out = []
  for (var i = 0; i < raw.length; i++) {
    var e = raw[i] || {}
    var project = String(e.project || "").trim()
    if (project === "") continue
    out.push({ project: project, id: String(e.id || ""), name: String(e.name || "") })
  }
  return out
}

// Jump list: default first (marked), then other favorites. One row per board.
function jumpBoards(favorites, defProject, defId, defName) {
  var out = [], seen = {}
  function add(entry, isDefault) {
    var e = {
      project: String(entry.project || "").trim(),
      id: String(entry.id || ""),
      name: String(entry.name || ""),
      isDefault: !!isDefault
    }
    if (e.project === "") return
    var k = favoriteKey(e)
    if (Object.prototype.hasOwnProperty.call(seen, k)) {
      if (isDefault) out[seen[k]].isDefault = true
      return
    }
    seen[k] = out.length
    out.push(e)
  }
  var dp = String(defProject || "").trim()
  if (dp !== "") add({ project: dp, id: defId, name: defName }, true)
  var list = Array.isArray(favorites) ? favorites : []
  for (var i = 0; i < list.length; i++) add(list[i], false)
  return out
}

function isFavorite(favorites, project, id) {
  var k = favoriteKey({ project: project, id: id })
  var list = Array.isArray(favorites) ? favorites : []
  for (var i = 0; i < list.length; i++) if (favoriteKey(list[i]) === k) return true
  return false
}

// Toggle membership. Returns the next favorites array (copy). Does not touch
// the default. Passing the same project+id again removes it.
function toggledFavorite(favorites, entry) {
  var e = {
    project: String((entry || {}).project || "").trim(),
    id: String((entry || {}).id || ""),
    name: String((entry || {}).name || "")
  }
  if (e.project === "") return Array.isArray(favorites) ? favorites.slice() : []
  var k = favoriteKey(e)
  var list = Array.isArray(favorites) ? favorites : []
  var out = [], found = false
  for (var i = 0; i < list.length; i++) {
    if (favoriteKey(list[i]) === k) { found = true; continue }
    out.push({
      project: String(list[i].project || "").trim(),
      id: String(list[i].id || ""),
      name: String(list[i].name || "")
    })
  }
  if (!found) out.push(e)
  return out
}

if (typeof module !== "undefined") module.exports = {
  favoriteKey: favoriteKey,
  boardLabel: boardLabel,
  jumpLabel: jumpLabel,
  hostFavorites: hostFavorites,
  jumpBoards: jumpBoards,
  isFavorite: isFavorite,
  toggledFavorite: toggledFavorite
}
