import QtQuick
import qs.Commons
import "Logic.js" as Logic
import "components"

// The board's top row (Board.qml): project and board name (opens the picker),
// the default star, the status ("Updated …"), then refresh, merge requests,
// keyboard shortcuts and settings.
Item {
  id: header
  required property var host
  // The merge-request list the badge counts (MrsView.scope).
  property string mrsScope: ""
  // For the harness (Board.qml reaches them as header.status and so on).
  readonly property alias status: status
  readonly property alias refreshButton: refreshButton
  readonly property alias mrsButton: mrsButton
  readonly property alias keysButton: keysButton
  readonly property alias gear: gear
  readonly property alias chevron: chevron
  readonly property alias defaultMark: defaultMark
  readonly property alias columnsButton: columnsButton
  implicitHeight: Math.max(title.implicitHeight, status.implicitHeight)
  // The title gets all the room the rest of the row doesn't need; the
  // status gets at most 40% of it, and elides from the left.
  readonly property real titleRoom: width - mrsButton.implicitWidth - Style.space(10) - chevron.implicitWidth - defaultMark.implicitWidth - refreshButton.implicitWidth - keysButton.implicitWidth - gear.implicitWidth
    - (columnsButton.visible ? columnsButton.implicitWidth + Style.space(10) : 0) - Style.space(8 + 12 + 8 + 10 + 10) - Math.min(status.implicitWidth, width * 0.4)

  // Elides at the end, so the board name goes before the project.
  BoardText {
    id: title
    anchors.verticalCenter: parent.verticalCenter
    width: Math.max(0, Math.min(implicitWidth, header.titleRoom))
    elide: Text.ElideRight
    text: host.project === "" ? "GitLab board" : host.project + (host.boardName !== "" ? " / " + host.boardName : "")
    color: titleMouse.containsMouse ? host.accent : host.foreground
    font { pixelSize: Style.font.title; bold: true }
  }
  BoardText {
    id: chevron
    anchors { left: title.right; verticalCenter: parent.verticalCenter }
    text: " ▾"
    color: titleMouse.containsMouse ? host.accent : host.quiet
    font: title.font
  }
  MouseArea {
    id: titleMouse
    x: title.x; width: chevron.x + chevron.width - title.x; height: parent.height
    hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.openPicker()
    IconTip { host: header.host; shown: titleMouse.containsMouse; text: "Switch project or board (p)" }
  }
  BoardText {
    id: defaultMark
    anchors { left: chevron.right; leftMargin: Style.space(8); verticalCenter: parent.verticalCenter }
    text: host.project === "" ? "" : host.onDefault ? "\uf005" : "\uf006 Default"
    color: defaultMouse.containsMouse ? host.accent : host.dim
    font.pixelSize: Style.font.bodySmall
    MouseArea {
      id: defaultMouse; anchors.fill: parent; anchors.margins: -Style.space(4)
      enabled: host.project !== ""; hoverEnabled: true; cursorShape: host.onDefault ? Qt.ArrowCursor : Qt.PointingHandCursor
      onClicked: if (!host.onDefault) host.openDefault()
    }
    IconTip { host: header.host; shown: defaultMouse.containsMouse; text: host.onDefault ? "Your default board" : "Go to your default board" }
  }
  BoardText {
    id: status
    anchors { left: defaultMark.right; leftMargin: Style.space(12); right: columnsButton.visible ? columnsButton.left : refreshButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
    horizontalAlignment: Text.AlignRight
    elide: Text.ElideLeft
    text: host.statusText()
    color: host.moveError !== "" || (host.refreshError !== "" && host.boardState === "ready" && !host.refreshing) ? host.urgent : host.boardState === "ready" && host.message === "" && !host.move && !host.cached ? host.dim : host.accent
    font.pixelSize: Style.font.bodySmall
    // Over the words only: how often the board refreshes now, and why.
    MouseArea {
      id: statusMouse
      anchors { right: parent.right; verticalCenter: parent.verticalCenter }
      width: Math.min(parent.width, parent.paintedWidth); height: parent.height
      enabled: host.boardState === "ready" && !host.cached; hoverEnabled: true
    }
    IconTip { host: header.host; shown: statusMouse.containsMouse; text: host.cadenceText() }
  }
  // Show or hide columns: opens the column row under the bots (board only).
  // Shows how many are hidden, so a hidden column is never forgotten.
  BoardText {
    id: columnsButton
    readonly property int hiddenCount: host.availableColumns.length - host.shownColumns.length
    visible: host.view === "board" && host.boardState === "ready" && host.setup === ""
    anchors { right: refreshButton.left; rightMargin: visible ? Style.space(10) : 0; verticalCenter: parent.verticalCenter }
    text: "\uf0db" + (hiddenCount > 0 ? " " + hiddenCount : "")
    color: columnsMouse.containsMouse || host.columnChips ? host.accent : host.dim
    font.pixelSize: Style.font.body
    MouseArea { id: columnsMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.columnChips = !host.columnChips }
    IconTip { host: header.host; shown: columnsMouse.containsMouse; text: columnsButton.hiddenCount > 0 ? "Show or hide columns (" + columnsButton.hiddenCount + " hidden)" : "Show or hide columns" }
  }
  BoardText {
    id: refreshButton
    anchors { right: mrsButton.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    text: "\uf021"
    color: refreshMouse.containsMouse ? host.accent : host.dim
    font.pixelSize: Style.font.body
    // Spins while any refresh runs with the popup open (host.refreshActive:
    // the board, or the MR list on screen), as Omarchy's Ui/Button.qml spins
    // its icon, and finishes the turn it is on, so it always stops upright.
    RotationAnimation on rotation { running: host.refreshActive; alwaysRunToEnd: true; loops: Animation.Infinite; from: 0; to: 360; duration: 900 }
    MouseArea { id: refreshMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.refresh() }
    IconTip { host: header.host; shown: refreshMouse.containsMouse; text: "Refresh (r)" }
  }
  // Merge requests (MrsView), like m does. The badge: how many waited on his
  // review at the last look (no fetch for it; it shows what the view loaded).
  BoardText {
    id: mrsButton
    anchors { right: keysButton.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    text: "\uf407"
    color: mrsMouse.containsMouse || host.view === "mrs" ? host.accent : host.dim
    font.pixelSize: Style.font.body
    readonly property string badge: Logic.mrBadge((host.feed.mrAnswers[mrsScope] || {}).data)
    Rectangle {
      objectName: "mrsBadge"
      visible: mrsButton.badge !== "" && host.view !== "mrs"
      anchors { right: parent.right; top: parent.top; rightMargin: -Style.space(7); topMargin: -Style.space(4) }
      width: Math.max(height, badgeText.implicitWidth + Style.space(6)); height: badgeText.implicitHeight + Style.space(1)
      radius: height / 2
      color: host.accent
      BoardText { id: badgeText; anchors.centerIn: parent; text: mrsButton.badge; color: host.background; font { pixelSize: Style.font.caption * 0.85; bold: true } }
    }
    MouseArea { id: mrsMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.toggleView("mrs") }
    IconTip { host: header.host; shown: mrsMouse.containsMouse; text: "Merge requests (m)" }
  }
  // The keyboard shortcuts (KeysView), like ? does.
  BoardText {
    id: keysButton
    anchors { right: gear.left; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    text: "\uf11c"
    color: keysMouse.containsMouse || host.view === "keys" ? host.accent : host.dim
    font.pixelSize: Style.font.body
    MouseArea { id: keysMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.toggleView("keys") }
    IconTip { host: header.host; shown: keysMouse.containsMouse; text: "Keyboard shortcuts (?)" }
  }
  BoardText {
    id: gear
    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
    text: "\uf013"
    color: gearMouse.containsMouse || host.view === "settings" ? host.accent : host.dim
    font.pixelSize: Style.font.body
    MouseArea { id: gearMouse; anchors.fill: parent; anchors.margins: -Style.space(4); hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.toggleView("settings") }
    IconTip { host: header.host; shown: gearMouse.containsMouse; text: "Settings (s)" }
  }
}
