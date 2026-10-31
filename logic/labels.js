// Labels: chip colors, status (list) labels, what the label editor offers. Part of Logic.js (the QML entry, which re-exports it);
// no Qt here, so tests/logic.test.js loads it under node.

// From core.js: required under node; in QML, Logic.js hands them over through use().
var Core = typeof module !== "undefined" ? require("./core.js") : null
function use(m) { Core = m.Core; }
function lowerList(value) { return Core.lowerList(value) }
function has(list, name) { return Core.has(list, name) }

// A label's colors ({ color, textColor }, validated #rrggbb from board-fetch).
// Text: the label's own text color, else dark or white by luminance.
function labelStyle(entry) {
  if (!entry || !entry.color) return null
  var n = parseInt(entry.color.slice(1), 16)
  var light = (0.299 * (n >> 16 & 255) + 0.587 * (n >> 8 & 255) + 0.114 * (n & 255)) / 255 > 0.6
  return { bg: entry.color, fg: entry.textColor || (light ? "#1f1e24" : "#ffffff") }
}
// Status labels: the board's list labels and the workflow labels of the
// no-board fallback. They change only by dragging a card, so the label editor
// never offers them. board-fetch guards the same set (any board's list label);
// its `def workflow` is this list (tests/run.sh checks they match).
var workflowLabels = ["research", "todo", "approved", "in progress", "review"]
function statusLabels(fetched, columns) {
  var names = (columns || []).filter(function(c) { return c.kind === "label" }).map(function(c) { return c.name })
  return lowerList(workflowLabels.concat(fetched || [], names))
}
// Project labels ({ name, color, textColor }) the issue could take: not on it,
// not status, matching the filter (any case, anywhere in the name).
function addableLabels(all, current, status, filter) {
  var needle = String(filter || "").trim().toLowerCase()
  return (all || []).filter(function(l) {
    return (current || []).indexOf(l.name) === -1 && !has(status, l.name) && l.name.toLowerCase().indexOf(needle) !== -1
  })
}
// The issue's status labels, in its own order: closing keeps them.
function statusOn(labels, status) {
  return (labels || []).map(String).filter(function(name) { return has(status, name) })
}
// The board's label colors plus those from board-fetch labels.
function withColors(colors, labels) {
  var out = {}
  Object.keys(colors || {}).forEach(function(k) { out[k] = colors[k] })
  ;(labels || []).forEach(function(l) { if (l.color && !out[l.name]) out[l.name] = { color: l.color, textColor: l.textColor } })
  return out
}
// A busy dot's color: the column's own (#rrggbb), unless it is hard to see on
// the popup's background (WCAG contrast under 2:1) or unknown; then "" and the
// dot keeps the theme accent. background may be #rrggbb or #aarrggbb.
function luminance(hex) {
  var n = parseInt(String(hex).slice(-6), 16)
  return [n >> 16 & 255, n >> 8 & 255, n & 255].map(function(v) {
    v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
  }).reduce(function(sum, v, i) { return sum + v * [0.2126, 0.7152, 0.0722][i] }, 0)
}
function dotColor(color, background) {
  if (!/^#[0-9a-fA-F]{6}$/.test(String(color || "")) || !/^#([0-9a-fA-F]{2})?[0-9a-fA-F]{6}$/.test(String(background || ""))) return ""
  var a = luminance(color), b = luminance(background)
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) >= 2 ? color : ""
}

if (typeof module !== "undefined") module.exports = { labelStyle: labelStyle, workflowLabels: workflowLabels, statusLabels: statusLabels, addableLabels: addableLabels, statusOn: statusOn, withColors: withColors, luminance: luminance, dotColor: dotColor }
