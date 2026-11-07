import QtQuick
import QtQuick.Controls
import qs.Commons

// The read-only lists of Merge requests and To-do: the scope tabs (All projects,
// This project), then each section's heading and count, its rows or a quiet
// empty line. The focused row has a faint fill and a short accent bar on its
// left edge; a click opens its link, a right-click copies it (Board.openUrl,
// Board.copyLink). The lists come from a ScopedFetch on the shared service
// (fetch), asked for when the view opens, its scope changes, or r. A view
// gives its sections, its row's lines (rowContent, with row, section and
// current on its Loader) and the line shown above the lists (message), and the
// object names its tests know its parts by.
Item {
  id: view
  required property var host
  required property var fetch          // a ScopedFetch: answers, loading, request()
  // answer -> [[section, title, rows, empty text], ...], in order.
  required property var sections
  property Component rowContent
  property Component message
  property bool messageShown: false
  property var copySign: function(row) { return "#" }
  property var names: ({ tab: "", underline: "", count: "", row: "", bar: "" })

  // "all" projects (the default), or "project": the board's project.
  property string mode: "all"
  readonly property string scope: mode === "project" && host.project !== "" ? host.project : "all"
  readonly property var entry: fetch.answers[scope] || null
  readonly property var answer: entry ? entry.data : null
  readonly property bool loading: fetch.loading === scope
  // A load the header shows (its bar and refresh icon): any, unless the view says.
  property bool busy: loading
  readonly property var parts: answer && answer.state === "ready" ? sections(answer) : []
  readonly property var rows: parts.reduce(function(all, s) { return all.concat(s[2]) }, [])
  property int cursor: 0
  // One flat list: headings, rows, and a line for an empty section.
  readonly property var items: {
    var out = [], n = 0
    parts.forEach(function(s, i) {
      out.push({ kind: "head", title: s[1], count: s[2].length, later: i > 0 })
      if (s[2].length === 0) out.push({ kind: "empty", text: s[3] })
      s[2].forEach(function(r) { out.push({ kind: "row", section: s[0], row: r, index: n++ }) })
    })
    return out
  }

  function open() { cursor = 0; fetch.request(scope, false) }
  function refresh() { fetch.request(scope, true) }
  function setMode(next) { if (next !== mode) { mode = next; cursor = 0 } }
  onScopeChanged: if (visible) fetch.request(scope, false)
  onRowsChanged: cursor = Math.max(0, Math.min(cursor, rows.length - 1))
  function moveCursor(dy) {
    if (rows.length === 0) return
    cursor = Math.max(0, Math.min(rows.length - 1, cursor + dy))
    for (var i = 0; i < list.count; i++) {
      var it = list.itemAt(i)
      if (it && it.rowIndex === cursor) {
        if (it.y < flick.contentY) flick.contentY = it.y
        else if (it.y + it.height > flick.contentY + flick.height) flick.contentY = it.y + it.height - flick.height
      }
    }
  }
  function activate() { if (rows[cursor]) host.openUrl(rows[cursor].url) }
  function copyCurrent() { var r = rows[cursor], sign = copySign; return r ? host.copyLink(r, sign(r)) : false }

  implicitHeight: top.implicitHeight + Style.space(10) + body.implicitHeight

  Item {
    id: top
    width: parent.width
    implicitHeight: tabs.implicitHeight
    // The scope: two text tabs, the current one underlined in the accent.
    // Each is a 32 point target with side padding and a quiet hover fill (v0.1.105).
    Row {
      id: tabs
      anchors { right: parent.right; verticalCenter: parent.verticalCenter }
      spacing: Style.space(4)
      Repeater {
        model: [{ mode: "all", label: "All projects" }, { mode: "project", label: "This project" }]
        delegate: Item {
          id: tab
          objectName: view.names.tab
          required property var modelData
          readonly property string label: modelData.label
          readonly property bool on: view.mode === modelData.mode
          visible: modelData.mode === "all" || view.host.project !== ""
          implicitWidth: tabText.implicitWidth + Style.space(20)
          implicitHeight: Style.space(32)
          function kbActivate() { view.setMode(tab.modelData.mode) }
          Rectangle {
            objectName: "scopeHover"
            anchors.fill: parent
            radius: Style.space(6)
            color: tabMouse.containsMouse && !tab.on ? Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, 0.06) : "transparent"
          }
          BoardText {
            id: tabText
            anchors.centerIn: parent
            text: tab.label
            color: tab.on ? view.host.foreground : tabMouse.containsMouse ? view.host.dim : view.host.quiet
            font.pixelSize: Style.font.bodySmall
          }
          Rectangle {
            objectName: view.names.underline
            visible: tab.on
            anchors { left: tabText.left; right: tabText.right; top: tabText.bottom; topMargin: Style.space(3) }
            height: 2; radius: 1
            color: view.host.accent
          }
          MouseArea { id: tabMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: tab.kbActivate() }
          FocusRing { host: view.host }
          Accessible.role: Accessible.PageTab
          Accessible.name: tab.label
          Accessible.selected: tab.on
          Accessible.onPressAction: tab.kbActivate()
        }
      }
    }
  }

  Flickable {
    id: flick
    anchors { top: top.bottom; topMargin: Style.space(10); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentHeight: body.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: body
      width: flick.width
      spacing: Style.space(2)
      Loader { width: parent.width; sourceComponent: view.message; visible: view.messageShown }
      Repeater {
        id: list
        model: view.items
        delegate: Item {
          id: item
          required property var modelData
          readonly property int rowIndex: modelData.kind === "row" ? modelData.index : -1
          width: body.width
          implicitHeight: modelData.kind === "head" ? headRow.implicitHeight + (modelData.later ? Style.space(14) : 0)
            : modelData.kind === "empty" ? emptyText.implicitHeight + Style.space(6)
            : rowBox.implicitHeight

          Row {
            id: headRow
            visible: item.modelData.kind === "head"
            anchors.bottom: parent.bottom
            spacing: Style.space(6)
            BoardText { text: item.modelData.title || ""; color: view.host.dim; font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 } }
            BoardText { objectName: view.names.count; text: String(item.modelData.count || 0); color: view.host.quiet; font.pixelSize: Style.font.caption }
          }
          BoardText {
            id: emptyText
            visible: item.modelData.kind === "empty"
            anchors.verticalCenter: parent.verticalCenter
            text: item.modelData.text || ""
            color: view.host.quiet
            font.pixelSize: Style.font.bodySmall
          }
          Rectangle {
            id: rowBox
            objectName: view.names.row
            visible: item.modelData.kind === "row"
            readonly property var row: item.modelData.row || ({})
            readonly property bool current: item.rowIndex === view.cursor
            anchors { left: parent.left; right: parent.right }
            implicitHeight: lines.implicitHeight + Style.space(10)
            radius: Style.space(6)
            color: current ? Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, 0.05) : "transparent"
            border.width: 0
            // The focused row: a short accent bar on its left edge.
            Rectangle {
              objectName: view.names.bar
              visible: rowBox.current
              anchors { left: parent.left; verticalCenter: parent.verticalCenter }
              width: 2; height: parent.height - Style.space(12); radius: 1
              color: view.host.accent
            }
            MouseArea {
              id: rowMouse
              anchors.fill: parent
              hoverEnabled: true
              cursorShape: rowBox.row.url ? Qt.PointingHandCursor : Qt.ArrowCursor
              onEntered: view.cursor = item.rowIndex
              // A right-click copies its link (Board.copyLink); a click opens it.
              acceptedButtons: Qt.LeftButton | Qt.RightButton
              onClicked: function(mouse) { if (mouse.button === Qt.RightButton) view.host.copyLink(rowBox.row, view.copySign(rowBox.row)); else view.host.openUrl(rowBox.row.url) }
            }
            Loader {
              id: lines
              active: item.modelData.kind === "row"
              anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: Style.space(8); rightMargin: Style.space(8) }
              readonly property var row: rowBox.row
              readonly property string section: item.modelData.section || ""
              readonly property bool current: rowBox.current
              sourceComponent: view.rowContent
            }
            // Leaves the plugin: a quiet arrow at the right, accent on hover,
            // and a tip that says where the link opens (Settings > Open links in).
            BoardText {
              objectName: "openHint"
              visible: item.modelData.kind === "row" && !!rowBox.row.url
              anchors { right: parent.right; rightMargin: Style.space(8); bottom: parent.bottom; bottomMargin: Style.space(5) }
              text: "\u2197"
              color: rowMouse.containsMouse ? view.host.accent : view.host.dim
              font.pixelSize: Style.font.bodySmall
              IconTip {
                objectName: "openHintTip"
                host: view.host
                shown: rowMouse.containsMouse
                text: view.host.linkMode === "app" ? "Opens in an app window" : "Opens in a browser tab"
              }
            }
          }
        }
      }
    }
  }
}
