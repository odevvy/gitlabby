import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui
import "Logic.js" as Logic

// Settings > Bots, for the project on screen: the bots behind the busy row
// under the header (BotsRow), what makes each one busy, and the busy columns.
// One look per job: choices are Omarchy-style square buttons, a dropdown and
// check boxes; labels (pills in their color) and columns (color dot and name)
// are only ever shown, never clicked. The new-bot form is labelled step by
// step and a dim Add always says what it still needs.
// It edits settings.bots as saved (Logic.withBot / withoutBot / withBusy), so
// other projects, workingLists and unknown keys stay; every change is saved at
// once through host.saveBots. The project's labels come from SettingsView.
Column {
  id: sec
  required property var host
  property var labels: []
  property var fetchedStatus: []
  property string labelsState: ""
  property string labelsError: ""
  signal wantLabels()
  // The new-bot form: open for one project; a project switch closes it.
  property bool adding: false
  property string addFor: ""
  property string kind: "label"  // label | list | none (cards no bot owns)
  property string pick: ""
  property bool menuOpen: false  // the Column dropdown's list
  readonly property bool typing: nameField.activeFocus || picker.field.activeFocus

  readonly property var raw: host.saved("bots", null)
  readonly property var found: Logic.botsEntry(raw, host.project)
  readonly property var bots: found.entry ? found.entry.bots : []
  readonly property var busy: found.entry ? Logic.lowerList(found.entry.busyLists || []) : []
  readonly property var labelColumns: host.columns.filter(function(c) { return c.kind === "label" }).map(function(c) { return String(c.name) })
  readonly property var usable: bots.filter(Logic.botUsable)
  readonly property bool hasNoOwner: usable.some(function(b) { return !isList(b) && b.label.trim() === "" })
  readonly property var ownerLabels: Logic.lowerList(usable.filter(function(b) { return !isList(b) }).map(function(b) { return b.label }))
  // Owner labels only: not a board column or a status label, not one a bot already has.
  readonly property var options: labelsState === "ready"
    ? Logic.addableLabels(labels, [], Logic.statusLabels(fetchedStatus, host.columns).concat(ownerLabels), picker.filter) : []
  readonly property string newName: nameField.text.trim()
  readonly property bool taken: newName !== "" && Logic.botNameTaken(found.entry, newName)
  readonly property bool ready: newName !== "" && !taken && (kind === "none" || pick !== "")
  // Why Add is dim, in words; "" when it isn't.
  readonly property string reason: ready ? ""
    : newName === "" ? "Name the bot to add it."
    : taken ? "There's already a bot named " + newName + "."
    : kind === "list" ? "Choose a column to add " + newName + "."
    : "Choose a label to add " + newName + "."
  readonly property real labelWidth: Style.space(92)  // the form's field names
  visible: host.project !== ""
  width: parent.width
  spacing: Style.space(6)

  function isList(b) { return typeof b.list === "string" && b.list.trim() !== "" }
  function knownLabel(name) { return labels.some(function(l) { return String(l.name).toLowerCase() === String(name).toLowerCase() }) }
  function open() {
    adding = true; addFor = host.project; kind = "label"; pick = ""; menuOpen = false; nameField.text = ""; picker.filter = ""
    wantLabels()
    nameField.forceActiveFocus()
  }
  function cancel() { adding = false; pick = ""; menuOpen = false; nameField.text = ""; picker.filter = "" }
  // A column bot opens the column list at once: the next step is in view.
  function choose(k) { if (kind !== k) { kind = k; pick = ""; menuOpen = k === "list" } }
  function pickColumn(name) { pick = name; menuOpen = false }
  function add() {
    if (!ready || addFor !== host.project) return
    var bot = kind === "list" ? { name: newName, list: pick } : { name: newName, label: pick }  // pick is "" for none (choose)
    host.saveBots(Logic.withBot(raw, host.project, bot, labelColumns))
    cancel()
  }
  function remove(index) { host.saveBots(Logic.withoutBot(raw, host.project, index)) }
  function toggleBusy(column) { host.saveBots(Logic.withBusy(raw, host.project, column, !Logic.has(busy, column))) }
  Connections { target: sec.host; function onProjectChanged() { sec.cancel() } }

  component Heading: BoardText {
    color: sec.host.dim
    font { bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
  }
  // A sub-heading inside the section, like Omarchy's PanelSectionHeader.
  component Caption: BoardText {
    color: sec.host.dim
    font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
  }
  component Hint: BoardText {
    color: sec.host.dim
    wrapMode: Text.Wrap
    font.pixelSize: Style.font.caption
  }
  component Link: BoardText {
    id: link
    signal clicked()
    color: linkMouse.containsMouse ? sec.host.foreground : sec.host.accent
    font.pixelSize: Style.font.bodySmall
    MouseArea { id: linkMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: link.clicked() }
  }
  // A board column, shown as on the board: its color dot and its name.
  component ColumnTag: Row {
    id: tag
    property string name: ""
    readonly property var column: sec.host.columns.filter(function(c) { return c.kind === "label" && String(c.name).toLowerCase() === tag.name.toLowerCase() })[0]
    spacing: Style.space(6)
    Rectangle {
      anchors.verticalCenter: parent.verticalCenter
      width: Style.space(8); height: width; radius: width / 2
      color: tag.column ? sec.host.columnAccent(tag.column) : sec.host.dim
    }
    BoardText { anchors.verticalCenter: parent.verticalCenter; text: tag.name; font.pixelSize: Style.font.bodySmall }
  }
  // One of a few (Omarchy's ButtonGroup): square, bordered; the chosen one is
  // filled and checked.
  component Choice: Rectangle {
    id: choice
    property string label: ""
    property bool on: false
    readonly property bool clickable: enabled
    signal clicked()
    implicitWidth: choiceText.implicitWidth + Style.space(20); implicitHeight: Style.space(26)
    radius: Style.cornerRadius
    opacity: enabled ? 1 : 0.45
    color: Qt.rgba(sec.host.foreground.r, sec.host.foreground.g, sec.host.foreground.b, on ? 0.18 : choiceMouse.containsMouse ? 0.08 : 0.04)
    border { width: 1; color: on ? sec.host.foreground : choiceMouse.containsMouse ? sec.host.dim : sec.host.faint }
    BoardText {
      id: choiceText
      anchors.centerIn: parent
      text: (choice.on ? "\uf00c  " : "") + choice.label
      color: choice.on ? sec.host.foreground : sec.host.dim
      font.pixelSize: Style.font.bodySmall
    }
    MouseArea { id: choiceMouse; anchors.fill: parent; enabled: choice.enabled; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: choice.clicked() }
  }
  // A busy column: the same check box as Start collapsed, then the column.
  component Check: Item {
    id: check
    property string label: ""
    property bool on: false
    readonly property bool clickable: true
    signal clicked()
    implicitWidth: checkRow.implicitWidth; implicitHeight: Style.space(22)
    Row {
      id: checkRow
      anchors.verticalCenter: parent.verticalCenter
      spacing: Style.space(6)
      Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        width: Style.space(16); height: width; radius: Style.space(4)
        color: check.on ? sec.host.accent : "transparent"
        border { width: 1; color: check.on ? sec.host.accent : checkMouse.containsMouse ? sec.host.foreground : sec.host.dim }
        BoardText { anchors.centerIn: parent; visible: check.on; text: "\uf00c"; color: sec.host.background; font.pixelSize: Style.font.caption }
      }
      ColumnTag { anchors.verticalCenter: parent.verticalCenter; name: check.label }
    }
    MouseArea { id: checkMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: check.clicked() }
  }
  // A labelled line of the new-bot form: the field name, then its control.
  component FormRow: Item {
    id: formRow
    property string title: ""
    default property alias control: slot.data
    width: parent ? parent.width : 0
    implicitHeight: Math.max(Style.space(26), slot.childrenRect.height)
    BoardText {
      width: sec.labelWidth; height: Style.space(26)
      verticalAlignment: Text.AlignVCenter
      text: formRow.title; color: sec.host.dim; font.pixelSize: Style.font.bodySmall
    }
    Item { id: slot; x: sec.labelWidth; width: formRow.width - sec.labelWidth; height: childrenRect.height }
  }

  Heading { text: "Bots" }
  BoardText {
    id: intro
    width: parent.width; wrapMode: Text.Wrap; color: sec.host.dim
    text: sec.bots.length === 0 && !sec.adding
      ? "Show who is busy on " + sec.host.project + ": a dot per bot under the header, read from the cards already on the board."
      : "A dot per bot under the board header shows who is working, read from the cards on this board."
  }
  BoardText {
    id: problem
    width: parent.width; wrapMode: Text.Wrap; color: sec.host.urgent
    visible: text !== ""
    text: sec.found.problem === "setting" ? "The bots setting isn't a JSON object (set without --json?). Adding a bot here replaces it."
      : sec.found.problem === "entry" ? "The bots entry for " + sec.host.project + " isn't valid. Adding a bot here replaces it."
      : ""
  }
  Link { id: invite; visible: sec.bots.length === 0 && !sec.adding; text: "+  Show bot status for this board"; onClicked: sec.open() }

  // Busy columns, above the bots they apply to: this board's label columns;
  // names saved for other boards stay.
  Column {
    id: busyRow
    visible: sec.bots.length > 0
    width: parent.width
    spacing: Style.space(4)
    topPadding: Style.space(4)
    bottomPadding: Style.space(6)
    Caption { text: "Count a bot as busy when its card is in" }
    Hint { width: parent.width; text: "Open and Closed never count." }
    BoardText {
      visible: sec.labelColumns.length === 0
      text: "Open the board to pick columns."; color: sec.host.dim; font { pixelSize: Style.font.bodySmall; italic: true }
    }
    Flow {
      width: parent.width
      spacing: Style.space(16)
      topPadding: Style.space(2)
      Repeater {
        model: sec.labelColumns
        delegate: Check { required property string modelData; label: modelData; on: Logic.has(sec.busy, modelData); onClicked: sec.toggleBusy(modelData) }
      }
    }
  }

  Caption { id: listTitle; visible: pane.visible; text: "Bots on " + sec.host.project }
  Rectangle {
    id: pane
    visible: sec.bots.length > 0 || sec.adding
    width: parent.width; implicitHeight: rows.implicitHeight
    radius: Style.space(8)
    color: Qt.rgba(sec.host.foreground.r, sec.host.foreground.g, sec.host.foreground.b, 0.035)
    border { width: 1; color: Qt.rgba(sec.host.foreground.r, sec.host.foreground.g, sec.host.foreground.b, 0.08) }
    Column {
      id: rows
      width: parent.width
      Repeater {
        model: sec.bots
        delegate: Item {
          id: bot
          required property var modelData
          required property int index
          readonly property bool ok: Logic.botUsable(modelData)
          readonly property bool byList: ok && sec.isList(modelData)
          readonly property string label: ok && !byList ? modelData.label.trim() : ""
          width: rows.width; implicitHeight: Style.space(34)
          opacity: ok ? 1 : 0.6
          Rectangle { visible: bot.index > 0; width: parent.width; height: 1; color: pane.border.color }
          Rectangle {
            id: dot
            x: Style.space(12); anchors.verticalCenter: parent.verticalCenter
            width: Style.space(8); height: width; radius: width / 2
            color: "transparent"; border { width: 1; color: bot.ok ? sec.host.accent : sec.host.dim }
          }
          BoardText {
            id: botName
            anchors { left: dot.right; leftMargin: Style.space(8); verticalCenter: parent.verticalCenter }
            width: Style.space(130); elide: Text.ElideRight
            text: bot.ok ? bot.modelData.name.trim() : String(bot.modelData && bot.modelData.name || "(no name)")
            font { pixelSize: Style.font.bodySmall; bold: true }
          }
          Row {
            anchors { left: botName.right; leftMargin: Style.space(8); right: remove.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
            spacing: Style.space(6)
            BoardText {
              anchors.verticalCenter: parent.verticalCenter
              color: sec.host.dim; font.pixelSize: Style.font.bodySmall
              text: !bot.ok ? "ignored: needs a name and a label or a column" : bot.byList ? "every card in" : bot.label !== "" ? "cards labelled" : "cards no other bot owns"
            }
            LabelChip { visible: bot.label !== ""; anchors.verticalCenter: parent.verticalCenter; host: sec.host; name: bot.label }
            ColumnTag { visible: bot.byList; anchors.verticalCenter: parent.verticalCenter; name: bot.byList ? bot.modelData.list.trim() : "" }
            BoardText {
              anchors.verticalCenter: parent.verticalCenter
              visible: text !== ""
              text: bot.label !== "" && sec.labelsState === "ready" && !sec.knownLabel(bot.label) ? "not a label here"
                : bot.byList && sec.labelColumns.length > 0 && !Logic.has(Logic.lowerList(sec.labelColumns), bot.modelData.list.trim()) ? "not a column here" : ""
              color: sec.host.urgent; font.pixelSize: Style.font.caption
            }
          }
          GlyphButton {
            id: remove
            anchors { right: parent.right; rightMargin: Style.space(6); verticalCenter: parent.verticalCenter }
            host: sec.host; glyph: "\uf00d"
            onClicked: sec.remove(bot.index)
          }
        }
      }
      // Footer: + Add a bot, or the new-bot form.
      Item {
        width: rows.width
        implicitHeight: sec.adding ? form.implicitHeight + Style.space(24) : Style.space(34)
        Rectangle { visible: sec.bots.length > 0; width: parent.width; height: 1; color: pane.border.color }
        Link { id: addLink; visible: !sec.adding; x: Style.space(12); anchors.verticalCenter: parent.verticalCenter; text: "+  Add a bot"; onClicked: sec.open() }
        Column {
          id: form
          visible: sec.adding
          x: Style.space(12); y: Style.space(12); width: parent.width - Style.space(24)
          spacing: Style.space(10)
          Caption { text: "New bot" }
          FormRow {
            title: "Name"
            TextField {
              id: nameField
              width: Math.min(Style.space(240), parent.width); verticalPadding: Style.space(3)
              font.pixelSize: Style.font.bodySmall; foreground: sec.host.foreground
              placeholderText: "Bot name"
              onAccepted: sec.add()
              Keys.onEscapePressed: sec.cancel()
            }
          }
          FormRow {
            title: "Busy with"
            // Wraps at the popup's width, so every choice stays in view.
            Flow {
              id: choiceRow
              width: parent.width; spacing: Style.space(6)
              Choice { label: "cards with a label"; on: sec.kind === "label"; onClicked: sec.choose("label") }
              Choice { label: "every card in a column"; enabled: sec.labelColumns.length > 0; on: sec.kind === "list"; onClicked: sec.choose("list") }
              Choice { label: "cards no bot owns"; enabled: !sec.hasNoOwner; on: sec.kind === "none"; onClicked: sec.choose("none") }
            }
          }
          FormRow {
            title: "Label"
            visible: sec.kind === "label"
            LabelPicker {
              id: picker
              width: parent.width
              host: sec.host; colors: Logic.withColors(sec.host.labelColors, sec.labels)
              options: sec.options
              labelsState: sec.labelsState
              error: sec.labelsState === "error" ? sec.labelsError : ""
              choose: true; selected: sec.pick
              emptyText: "No other labels: the rest are board columns or have a bot."
              onPicked: function(name) { sec.pick = name }
              onEscaped: sec.cancel()
            }
          }
          FormRow {
            title: "Column"
            visible: sec.kind === "list"
            // A dropdown (Omarchy's Dropdown look) whose list opens in place.
            Column {
              width: Math.min(Style.space(240), parent.width)
              spacing: Style.space(4)
              Rectangle {
                id: columnMenu
                width: parent.width; height: Style.space(26)
                radius: Style.cornerRadius
                color: Qt.rgba(sec.host.foreground.r, sec.host.foreground.g, sec.host.foreground.b, menuMouse.containsMouse || sec.menuOpen ? 0.08 : 0.04)
                border { width: 1; color: sec.menuOpen || sec.pick === "" ? sec.host.accent : sec.host.faint }
                ColumnTag { visible: sec.pick !== ""; x: Style.space(10); anchors.verticalCenter: parent.verticalCenter; name: sec.pick }
                BoardText {
                  visible: sec.pick === ""
                  x: Style.space(10); anchors.verticalCenter: parent.verticalCenter
                  text: "Choose a column"; color: sec.host.dim; font { pixelSize: Style.font.bodySmall; italic: true }
                }
                BoardText {
                  anchors { right: parent.right; rightMargin: Style.space(10); verticalCenter: parent.verticalCenter }
                  text: sec.menuOpen ? "\uf077" : "\uf078"; color: sec.host.dim; font.pixelSize: Style.font.caption
                }
                MouseArea { id: menuMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sec.menuOpen = !sec.menuOpen }
              }
              Rectangle {
                visible: sec.menuOpen
                width: parent.width; height: menuList.implicitHeight + Style.space(8)
                radius: Style.cornerRadius
                color: "transparent"
                border { width: 1; color: sec.host.faint }
                Column {
                  id: menuList
                  y: Style.space(4); width: parent.width
                  Repeater {
                    model: sec.labelColumns
                    delegate: Rectangle {
                      id: option
                      required property string modelData
                      readonly property string label: modelData
                      readonly property bool clickable: true
                      width: menuList.width; height: Style.space(26)
                      color: optionMouse.containsMouse || sec.pick === modelData ? Qt.rgba(sec.host.foreground.r, sec.host.foreground.g, sec.host.foreground.b, 0.08) : "transparent"
                      ColumnTag { x: Style.space(10); anchors.verticalCenter: parent.verticalCenter; name: option.modelData }
                      MouseArea { id: optionMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sec.pickColumn(option.modelData) }
                    }
                  }
                }
              }
            }
          }
          // Add, Cancel, and why Add is dim.
          Item {
            width: parent.width
            implicitHeight: Math.max(buttons.implicitHeight, why.implicitHeight)
            Row {
              id: buttons
              spacing: Style.space(8)
              ActionButton { id: addButton; host: sec.host; small: true; main: true; enabled: sec.ready; label: "Add " + (sec.newName || "bot"); onClicked: sec.add() }
              ActionButton { host: sec.host; small: true; label: "Cancel"; onClicked: sec.cancel() }
            }
            Row {
              id: why
              visible: sec.reason !== ""
              anchors { left: buttons.right; leftMargin: Style.space(12); right: parent.right; verticalCenter: buttons.verticalCenter }
              spacing: Style.space(6)
              BoardText { id: whyGlyph; text: "\uf05a"; color: whyText.color; font.pixelSize: Style.font.bodySmall }
              BoardText {
                id: whyText
                width: why.width - whyGlyph.width - why.spacing
                wrapMode: Text.Wrap
                text: sec.reason
                color: sec.taken ? sec.host.urgent : sec.host.accent
                font.pixelSize: Style.font.bodySmall
              }
            }
          }
        }
      }
    }
  }
}
