import QtQuick
import qs.Commons
import "Logic.js" as Logic
import "components"

// The board's top row (Board.qml): project and board name (opens the picker),
// the default star, the Board and Merge requests tabs (on Merge requests a
// quiet "read-only" chip after them, v0.1.71), the status ("Updated
// …"), then the icon buttons: refresh, columns (board only), keyboard
// shortcuts and settings (v0.1.69: refresh first, next to the status). Buttons and tabs are 28 px targets with a faint fill
// on hover (v155 design B), so they are easy to hit with a mouse.
Item {
  id: header
  required property var host
  // The merge-request list the badge counts (MrsView.scope).
  property string mrsScope: ""
  property string todoScope: ""  // TodoView.scope: the To-do tab's badge reads its last answer
  // For the harness (Board.qml reaches them as header.status and so on).
  readonly property alias status: status
  readonly property alias refreshButton: refreshButton
  readonly property alias mrsButton: mrsButton
  readonly property alias keysButton: keysButton
  readonly property alias gear: gear
  readonly property alias chevron: chevron
  readonly property alias defaultMark: defaultMark
  readonly property alias columnsButton: columnsButton
  readonly property alias botsButton: botsButton
  readonly property alias boardTab: boardTab
  readonly property alias tabs: tabs
  readonly property alias readOnlyChip: readOnlyChip
  // The row keeps the title's height: the 28 px buttons and tabs reach a few
  // points into the gap above and below it, so nothing under the header moves.
  implicitHeight: Math.max(title.implicitHeight, status.implicitHeight)
  // A faint fill: a hovered button or tab; the accent tint: an open view's button.
  // Starred-board list cap: the card below the header, less Browse and margins.
  readonly property real jumpListMax: Math.max(Style.space(56) * 3, (parent ? parent.height : 0) - height - Style.space(10) - Style.space(29) - Style.space(24))
  readonly property color hoverFill: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.08)
  // Board · Merge requests · To-do show on those three views; the others have
  // their own heading and ✕. Short of room, the Merge requests tab reads "MRs".
  readonly property bool tabsShown: host.view === "board" || host.view === "mrs" || host.view === "todos"
  TextMetrics { id: mrsLong; font { pixelSize: Style.font.body; bold: true } text: "Merge requests" }
  TextMetrics { id: mrsShort; font { pixelSize: Style.font.body; bold: true } text: "MRs" }
  TextMetrics { id: todoLong; font { pixelSize: Style.font.body; bold: true } text: "To-do" }
  // Everything but the title and the status.
  // Merge requests and to-dos are read-only here: a quiet chip after the tabs
  // (v0.1.71), the first thing to go when the row is short (with the long tab name).
  readonly property bool readOnlyView: host.view === "mrs" || host.view === "todos"
  readonly property real chipRoom: readOnlyView ? readOnlyChip.implicitWidth + Style.space(10) : 0
  readonly property real fixedWidth: chipRoom + chevron.implicitWidth + defaultMark.implicitWidth + Style.space(8 + 12 + 8)
    + (tabsShown ? 1 + Style.space(12 + 6) + boardTab.implicitWidth + mrsLong.advanceWidth + Style.space(20) + mrsButton.badgeRoom
      + todoLong.advanceWidth + Style.space(20) + todoTab.badgeRoom : 0)
    + (columnsButton.visible ? columnsButton.implicitWidth + Style.space(4) : 0)
    + (botsButton.visible ? botsButton.implicitWidth + Style.space(4) : 0) + refreshButton.implicitWidth + keysButton.implicitWidth + gear.implicitWidth + Style.space(4 + 4)
  readonly property bool compactTabs: tabsShown && width - fixedWidth - title.implicitWidth - Style.space(48) < 0
  // The status gets what the full title leaves (at least 48 points, so a
  // message still shows its end; at most 40%), and elides from the left; the
  // title gets the rest.
  readonly property real freeWidth: width - fixedWidth + (compactTabs ? mrsLong.advanceWidth - mrsShort.advanceWidth + chipRoom : 0)
  readonly property real titleRoom: freeWidth - Math.min(status.implicitWidth, width * 0.4, Math.max(Style.space(48), freeWidth - title.implicitWidth))

  // An icon button: a 28 px target, the glyph at 14 px, a faint fill on hover
  // and the accent tint while its view is open. color is the glyph's. The fill
  // turns against the button, so it stays square while refresh spins.
  component HeadButton: Item {
    id: hb
    property alias text: glyph.text
    property alias color: glyph.color
    property bool active: false
    property string tip: ""
    readonly property alias hovered: hbMouse.containsMouse
    signal clicked()
    implicitWidth: Math.max(Style.space(28), glyph.implicitWidth + Style.space(14)); implicitHeight: Style.space(28)
    width: implicitWidth; height: implicitHeight
    // No fill for on or hover (v0.1.112): on is an accent icon, a hovered
    // off icon brightens to the foreground, a hovered on icon to a lighter accent.
    BoardText { id: glyph; objectName: "headGlyph"; anchors.centerIn: parent; color: hb.active ? (hb.hovered ? Qt.lighter(header.host.accent, 1.2) : header.host.accent) : hb.hovered ? header.host.foreground : header.host.dim; font.pixelSize: Style.font.title }
    MouseArea { id: hbMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: hb.clicked() }
    IconTip { host: header.host; shown: hb.hovered; text: hb.tip }
    FocusRing { host: header.host }
    Accessible.role: Accessible.Button
    Accessible.name: hb.tip
    Accessible.onPressAction: hb.clicked()
  }
  // A view tab: its name, the accent underline while it is on screen.
  component HeadTab: Item {
    id: ht
    property string label: ""
    property bool on: false
    property string tip: ""
    property string badge: ""
    readonly property alias hovered: htMouse.containsMouse
    // What the badge adds to the tab's width (for the header's sums).
    readonly property real badgeRoom: badge !== "" && !on ? Math.max(badgeText.implicitHeight + Style.space(1), badgeText.implicitWidth + Style.space(6)) + tabRow.spacing : 0
    signal clicked()
    implicitWidth: tabRow.implicitWidth + Style.space(20); implicitHeight: Style.space(28)
    width: implicitWidth; height: implicitHeight
    Rectangle { objectName: "headFill"; anchors.fill: parent; radius: Style.space(6); color: ht.hovered && !ht.on ? header.hoverFill : "transparent" }
    Row {
      id: tabRow
      anchors.centerIn: parent
      spacing: Style.space(6)
      BoardText {
        id: tabText
        objectName: "tabText"
        anchors.verticalCenter: parent.verticalCenter
        text: ht.label
        color: ht.on || ht.hovered ? header.host.foreground : header.host.dim
        font { pixelSize: Style.font.body; bold: ht.on }
      }
      Rectangle {
        objectName: ht.objectName === "todoTab" ? "todoBadge" : "mrsBadge"
        visible: ht.badge !== "" && !ht.on
        anchors.verticalCenter: parent.verticalCenter
        width: Math.max(height, badgeText.implicitWidth + Style.space(6)); height: badgeText.implicitHeight + Style.space(1)
        radius: height / 2
        color: header.host.accent
        BoardText { id: badgeText; anchors.centerIn: parent; text: ht.badge; color: header.host.background; font { pixelSize: Style.font.caption * 0.85; bold: true } }
      }
    }
    Rectangle {
      objectName: "tabUnderline"
      visible: ht.on
      anchors { top: tabRow.bottom; topMargin: Style.space(3); horizontalCenter: parent.horizontalCenter }
      width: tabRow.implicitWidth; height: Math.max(2, Style.space(2)); radius: height / 2
      color: header.host.accent
    }
    MouseArea { id: htMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: ht.clicked() }
    IconTip { host: header.host; shown: ht.hovered; text: ht.tip }
    FocusRing { host: header.host }
    Accessible.role: Accessible.PageTab
    Accessible.name: ht.label
    Accessible.onPressAction: ht.clicked()
  }

  // Elides at the end, so the board name goes before the project.
  BoardText {
    id: title
    anchors.verticalCenter: parent.verticalCenter
    width: Math.max(0, Math.min(implicitWidth, header.titleRoom))
    elide: Text.ElideRight
    text: host.project === "" ? "GitLabby" : host.project + (host.boardName !== "" ? " / " + host.boardName : "")
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
    hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: host.openJumpMenu()
    function kbActivate() { host.openJumpMenu() }
    IconTip { host: header.host; shown: titleMouse.containsMouse && host.headerMenu === ""; text: "Starred boards" }
    FocusRing { host: header.host }
    Accessible.role: Accessible.Button
    Accessible.name: "Starred boards"
    Accessible.onPressAction: kbActivate()
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
      onClicked: if (!host.onDefault) host.openDefaultMenu()
      function kbActivate() { if (!host.onDefault) host.openDefaultMenu() }
      FocusRing { host: header.host }
      Accessible.role: Accessible.Button
      Accessible.name: host.onDefault ? "Your default board" : "Default board"
      Accessible.onPressAction: kbActivate()
    }
    IconTip { host: header.host; shown: defaultMouse.containsMouse && host.headerMenu === ""; text: host.onDefault ? "Your default board" : "Default board" }
  }
  // Board · Merge requests: the two views, after a hairline.
  Rectangle {
    id: tabRule
    visible: header.tabsShown
    anchors { left: defaultMark.right; leftMargin: Style.space(12); verticalCenter: parent.verticalCenter }
    width: 1; height: Style.space(16)
    color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.12)
  }
  Row {
    id: tabs
    visible: header.tabsShown
    anchors { left: tabRule.right; leftMargin: Style.space(6); verticalCenter: parent.verticalCenter }
    HeadTab {
      id: boardTab
      label: "Board"
      on: host.view === "board"
      tip: host.view === "board" ? "" : "Back to the board (Esc)"
      onClicked: host.showView("board")
    }
    // Merge requests (MrsView), like m does. The badge: how many waited on his
    // review at the last look (no fetch for it; it shows what the view loaded).
    HeadTab {
      id: mrsButton
      label: header.compactTabs ? "MRs" : "Merge requests"
      on: host.view === "mrs"
      tip: "Merge requests (m)"
      badge: Logic.mrBadge((host.feed.mrs.answers[mrsScope] || {}).data)
      onClicked: host.showView("mrs")
    }
    // To-do (TodoView), like t does. The badge: pending to-dos at the last look
    // (no fetch for it, as the Merge requests one).
    HeadTab {
      id: todoTab
      objectName: "todoTab"
      label: "To-do"
      on: host.view === "todos"
      tip: "To-do (t)"
      badge: Logic.todoBadge((host.feed.todos.answers[todoScope] || {}).data)
      onClicked: host.showView("todos")
    }
  }
  Pill {
    id: readOnlyChip
    objectName: "readOnlyChip"
    visible: header.readOnlyView && header.tabsShown && !header.compactTabs
    anchors { left: tabs.right; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    label: "read-only"
    textColor: host.quiet
    border.color: Qt.rgba(host.quiet.r, host.quiet.g, host.quiet.b, 0.4)
  }
  BoardText {
    id: status
    anchors { left: botsButton.visible ? botsButton.right : columnsButton.visible ? columnsButton.right : readOnlyChip.visible ? readOnlyChip.right : header.tabsShown ? tabs.right : defaultMark.right; leftMargin: Style.space(12); right: refreshButton.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
    horizontalAlignment: Text.AlignRight
    elide: Text.ElideLeft
    text: host.statusText()
    color: host.moveError !== "" || (host.refreshError !== "" && host.boardState === "ready" && !host.refreshing) ? host.urgent : host.boardState === "ready" && host.message === "" && !host.move && !host.cached ? host.quiet : host.accent
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
  // While any refresh runs with the popup open, a small dot before the status
  // breathes: grey for the timer's, accent for one you asked for. Nothing else
  // moves, and the status keeps saying when the board was updated.
  Rectangle {
    id: refreshDot
    objectName: "refreshDot"
    visible: host.refreshActive && status.text !== ""
    anchors { right: status.right; rightMargin: status.paintedWidth + Style.space(8); verticalCenter: status.verticalCenter }
    width: Style.space(6); height: width; radius: width / 2
    color: host.loudRefresh ? host.accent : host.quiet
    SequentialAnimation on opacity {
      running: refreshDot.visible; loops: Animation.Infinite
      NumberAnimation { from: 0.25; to: 1; duration: 700; easing.type: Easing.InOutSine }
      NumberAnimation { from: 1; to: 0.25; duration: 700; easing.type: Easing.InOutSine }
    }
  }
  // Show or hide columns: opens the column row under the bots (board only).
  // Board-only buttons sit right after the tabs (v0.1.112), so the right
  // cluster and the status never move between views.
  // Shows how many are hidden, so a hidden column is never forgotten.
  HeadButton {
    id: columnsButton
    readonly property int hiddenCount: host.availableColumns.length - host.shownColumns.length
    visible: host.view === "board" && host.boardState === "ready" && host.setup === ""
    anchors { left: readOnlyChip.visible ? readOnlyChip.right : header.tabsShown ? tabs.right : defaultMark.right; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter }
    text: "\uf0db" + (hiddenCount > 0 ? " " + hiddenCount : "")
    active: host.columnChips
    tip: hiddenCount > 0 ? "Show or hide columns (" + hiddenCount + " hidden)" : "Show or hide columns"
    onClicked: { host.headerMenu = ""; host.columnChips = !host.columnChips }
  }
  // Show or hide the bots row (board only, and only when the project has bots).
  // md-robot-outline (U+F167A) is above the BMP: built from its code point.
  HeadButton {
    id: botsButton
    objectName: "botsButton"
    visible: host.hasBots
    anchors { left: columnsButton.visible ? columnsButton.right : readOnlyChip.visible ? readOnlyChip.right : header.tabsShown ? tabs.right : defaultMark.right; leftMargin: Style.space(4); verticalCenter: parent.verticalCenter }
    text: String.fromCodePoint(0xF167A)
    active: !host.botsHidden
    tip: host.botsHidden ? "Show bots (b)" : "Hide bots (b)"
    onClicked: host.toggleBots()
  }
  HeadButton {
    id: refreshButton
    anchors { right: keysButton.left; rightMargin: Style.space(4); verticalCenter: parent.verticalCenter }
    text: "\uf021"
    tip: "Refresh (r)"
    // Spins while a refresh you asked for runs with the popup open
    // (host.loudRefresh: Refresh, r, the first load, or the MR list on
    // screen), as Omarchy's Ui/Button.qml spins its icon, and finishes the
    // turn it is on, so it always stops upright. The timer's doesn't spin it.
    RotationAnimation on rotation { running: host.loudRefresh; alwaysRunToEnd: true; loops: Animation.Infinite; from: 0; to: 360; duration: 900 }
    onClicked: { host.headerMenu = ""; host.refresh() }
  }
  // The keyboard shortcuts (KeysView), like ? does.
  HeadButton {
    id: keysButton
    anchors { right: gear.left; rightMargin: Style.space(4); verticalCenter: parent.verticalCenter }
    text: "\uf11c"
    active: host.view === "keys"
    tip: "Keyboard shortcuts (?)"
    onClicked: host.toggleView("keys")
  }
  HeadButton {
    id: gear
    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
    text: "\uf013"
    active: host.view === "settings"
    tip: "Settings (s)"
    onClicked: host.toggleView("settings")
  }

  // A · outline Default: Go to your default / Make this your default.
  Rectangle {
    id: defaultMenu
    objectName: "defaultMenu"
    visible: host.headerMenu === "default"
    z: 30
    clip: true
    anchors { top: defaultMark.bottom; topMargin: Style.space(10); left: defaultMark.left }
    width: Style.space(260)
    height: defaultMenuCol.implicitHeight + Style.space(8)
    radius: Style.space(6)
    color: Qt.rgba(host.background.r, host.background.g, host.background.b, 1)
    border { width: 1; color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.2) }
    Column {
      id: defaultMenuCol
      y: Style.space(4); width: parent.width
      spacing: 0
      Repeater {
        model: [
          { id: "go", label: "Go to your default board" },
          { id: "make", label: "Make this your default" }
        ]
        delegate: Item {
          id: defRow
          required property var modelData
          required property int index
          width: defaultMenuCol.width; height: Style.space(28)
          // Lit: the key-selected row after a key, else the hovered one.
          readonly property bool rowHovered: host.menuKeys ? host.menuIndex === index : defMouse.containsMouse
          Rectangle {
            objectName: "defHover"
            anchors { fill: parent; leftMargin: Style.space(4); rightMargin: Style.space(4); topMargin: Style.space(2); bottomMargin: Style.space(2) }
            radius: Style.space(4)
            border.width: 0
            color: defRow.rowHovered ? header.hoverFill : "transparent"
          }
          BoardText {
            anchors { left: parent.left; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter; right: parent.right; rightMargin: Style.space(10) }
            elide: Text.ElideRight
            text: defRow.modelData.label
            color: defRow.rowHovered ? host.foreground : host.dim
            font.pixelSize: Style.font.bodySmall
          }
          MouseArea {
            id: defMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onContainsMouseChanged: if (containsMouse) host.hoverMenu(defRow.index)
            onClicked: {
              if (defRow.modelData.id === "go") host.openDefault()
              else host.setDefaultCurrent()
            }
          }
        }
      }
    }
  }

  // B · title: starred boards (roomy two-line rows), then Browse all projects…
  Rectangle {
    id: jumpMenu
    objectName: "jumpMenu"
    visible: host.headerMenu === "jump"
    z: 30
    clip: true
    anchors { top: title.bottom; topMargin: Style.space(10); left: title.left }
    width: Math.min(header.width - Style.space(16), Style.space(420))
    height: jumpMenuCol.implicitHeight + Style.space(8)
    radius: Style.space(6)
    color: Qt.rgba(host.background.r, host.background.g, host.background.b, 1)
    border { width: 1; color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.2) }
    Column {
      id: jumpMenuCol
      y: Style.space(4); width: parent.width
      // Starred boards scroll inside a bounded list; Browse stays pinned below.
      Item {
        id: jumpListBox
        width: jumpMenuCol.width
        height: Math.min(jumpRows.implicitHeight, header.jumpListMax)
      Flickable {
        id: jumpList
        objectName: "jumpList"
        anchors.fill: parent
        clip: true
        contentWidth: width; contentHeight: jumpRows.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height
        // Keys move the selection: keep the selected row in view.
        Connections {
          target: header.host
          function onMenuIndexChanged() {
            var h = header.host, rowH = Style.space(56)
            if (h.headerMenu !== "jump" || !h.menuKeys || h.menuIndex >= h.jumpBoards.length) return
            var top = h.menuIndex * rowH
            if (top < jumpList.contentY) jumpList.contentY = top
            else if (top + rowH > jumpList.contentY + jumpList.height) jumpList.contentY = top + rowH - jumpList.height
          }
        }
      Column {
        id: jumpRows
        width: jumpMenuCol.width
      Repeater {
        model: host.jumpBoards
        delegate: Item {
          id: jumpRow
          required property var modelData
          required property int index
          readonly property bool isDefaultRow: jumpRow.modelData.isDefault === true
          // × MouseArea sits above jumpMouse; count it as hovered too.
          readonly property bool rowHovered: host.menuKeys ? host.menuIndex === index : (jumpMouse.containsMouse || xMouse.containsMouse)
          width: jumpMenuCol.width; height: Style.space(56)
          Rectangle {
            id: jumpHover
            objectName: "jumpHover"
            anchors { fill: parent; leftMargin: Style.space(4); rightMargin: Style.space(4); topMargin: Style.space(2); bottomMargin: Style.space(2) }
            radius: Style.space(4)
            border.width: 0
            color: jumpRow.rowHovered ? header.hoverFill : "transparent"
          }
          BoardText {
            id: jumpStar
            anchors { left: parent.left; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter }
            text: "\uf005"; color: host.accent; font.pixelSize: Style.font.bodySmall
          }
          Column {
            id: jumpLabels
            anchors {
              left: jumpStar.right; leftMargin: Style.space(8)
              verticalCenter: parent.verticalCenter
              right: jumpRow.isDefaultRow ? jumpDefault.left : jumpRemove.left
              rightMargin: Style.space(8)
            }
            spacing: Style.space(2)
            BoardText {
              objectName: "jumpBoardName"
              width: parent.width
              elide: Text.ElideRight
              text: Logic.boardLabel(jumpRow.modelData.name, jumpRow.modelData.id)
              color: host.foreground
              font.pixelSize: Style.font.bodySmall
            }
            BoardText {
              objectName: "jumpProject"
              width: parent.width
              elide: Text.ElideMiddle
              text: String(jumpRow.modelData.project || "")
              color: host.dim
              font.pixelSize: Style.font.caption
            }
          }
          BoardText {
            id: jumpDefault
            objectName: "jumpDefaultBadge"
            visible: jumpRow.isDefaultRow
            anchors { right: parent.right; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
            text: "Default"; color: host.quiet; font.pixelSize: Style.font.caption
          }
          BoardText {
            id: jumpRemove
            objectName: "jumpUnfavorite"
            visible: !jumpRow.isDefaultRow
            anchors { right: parent.right; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
            text: "\uf00d"; color: host.dim; font.pixelSize: Style.font.bodySmall
          }
          MouseArea {
            id: jumpMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onContainsMouseChanged: if (containsMouse) host.hoverMenu(jumpRow.index)
            onClicked: host.jumpTo(jumpRow.modelData)
          }
          MouseArea {
            id: xMouse
            // Above the row: × unfavorites without jumping; menu stays open.
            anchors.fill: jumpRemove; anchors.margins: -Style.space(6)
            visible: jumpRemove.visible
            enabled: jumpRemove.visible
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            z: 2
            onClicked: host.unfavoriteJump(jumpRow.modelData)
          }
        }
      }
      }
      }
        Rectangle {
          objectName: "jumpScrollBar"
          visible: jumpList.contentHeight > jumpList.height
          anchors.right: parent.right; anchors.rightMargin: Style.space(2)
          width: Style.space(3); radius: width / 2
          height: Math.max(Style.space(24), jumpList.height * jumpList.height / Math.max(1, jumpList.contentHeight))
          y: (jumpList.height - height) * (jumpList.contentY / Math.max(1, jumpList.contentHeight - jumpList.height))
          color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.25)
        }
      }
      Rectangle {
        visible: host.jumpBoards.length > 0
        width: parent.width; height: 1
        color: Qt.rgba(host.foreground.r, host.foreground.g, host.foreground.b, 0.12)
      }
      Item {
        id: browseRow
        width: jumpMenuCol.width; height: Style.space(28)
        readonly property bool rowHovered: host.menuKeys ? host.menuIndex === host.jumpBoards.length : browseMouse.containsMouse
        Rectangle {
          objectName: "browseHover"
          anchors { fill: parent; leftMargin: Style.space(4); rightMargin: Style.space(4); topMargin: Style.space(2); bottomMargin: Style.space(2) }
          radius: Style.space(4)
          border.width: 0
          color: browseRow.rowHovered ? header.hoverFill : "transparent"
        }
        BoardText {
          anchors { left: parent.left; leftMargin: Style.space(10); verticalCenter: parent.verticalCenter; right: parent.right; rightMargin: Style.space(10) }
          text: "Browse all projects…"
          color: browseRow.rowHovered ? host.foreground : host.dim
          font.pixelSize: Style.font.bodySmall
        }
        MouseArea {
          id: browseMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
          onContainsMouseChanged: if (containsMouse) host.hoverMenu(host.jumpBoards.length)
          onClicked: host.openBrowse()
        }
      }
    }
  }
}
