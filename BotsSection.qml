import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui
import "Logic.js" as Logic

// Settings > Bots, for the project on screen: the bots behind the busy row
// under the header (BotsRow), what makes each one busy, and the busy columns.
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
  readonly property bool typing: nameField.activeFocus || picker.field.activeFocus

  readonly property var raw: host.setting("bots", null)
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
  visible: host.project !== ""
  width: parent.width
  spacing: Style.space(6)

  function isList(b) { return typeof b.list === "string" && b.list.trim() !== "" }
  function knownLabel(name) { return labels.some(function(l) { return String(l.name).toLowerCase() === String(name).toLowerCase() }) }
  function open() {
    adding = true; addFor = host.project; kind = "label"; pick = ""; nameField.text = ""; picker.filter = ""
    wantLabels()
    nameField.forceActiveFocus()
  }
  function cancel() { adding = false; pick = ""; nameField.text = ""; picker.filter = "" }
  function choose(k) { if (kind !== k) { kind = k; pick = "" } }
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
  component Link: BoardText {
    id: link
    signal clicked()
    color: linkMouse.containsMouse ? sec.host.foreground : sec.host.accent
    font.pixelSize: Style.font.bodySmall
    MouseArea { id: linkMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: link.clicked() }
  }
  // A choice or a busy column: filled in the accent when on.
  component Toggle: Pill {
    property bool on: false
    clickable: enabled
    opacity: enabled ? 1 : 0.5
    color: on ? sec.host.accent : "transparent"
    textColor: on ? sec.host.background : sec.host.dim
    border.color: on ? sec.host.accent : sec.host.faint
  }

  Heading { text: "Bots" }
  BoardText {
    id: intro
    width: parent.width; wrapMode: Text.Wrap; color: sec.host.dim
    text: sec.bots.length === 0 && !sec.adding
      ? "Show who is busy on " + sec.host.project + ": a dot per bot under the header, read from the cards already on the board."
      : "On " + sec.host.project + ". A bot is busy while it has an issue in a busy column."
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
              text: !bot.ok ? "ignored: needs a name and a label or a column" : bot.byList ? "every card in" : bot.label !== "" ? "cards labelled" : "cards with no bot's label"
            }
            LabelChip { visible: bot.label !== ""; anchors.verticalCenter: parent.verticalCenter; host: sec.host; name: bot.label }
            Pill { visible: bot.byList; anchors.verticalCenter: parent.verticalCenter; label: bot.byList ? bot.modelData.list.trim() : "" }
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
        implicitHeight: sec.adding ? form.implicitHeight + Style.space(20) : Style.space(34)
        Rectangle { visible: sec.bots.length > 0; width: parent.width; height: 1; color: pane.border.color }
        Link { id: addLink; visible: !sec.adding; x: Style.space(12); anchors.verticalCenter: parent.verticalCenter; text: "+  Add a bot"; onClicked: sec.open() }
        Column {
          id: form
          visible: sec.adding
          x: Style.space(12); y: Style.space(10); width: parent.width - Style.space(24)
          spacing: Style.space(8)
          Row {
            spacing: Style.space(8)
            TextField {
              id: nameField
              width: Style.space(180); verticalPadding: Style.space(3)
              font.pixelSize: Style.font.bodySmall; foreground: sec.host.foreground
              placeholderText: "Bot name"
              onAccepted: sec.add()
              Keys.onEscapePressed: sec.cancel()
            }
            BoardText { anchors.verticalCenter: parent.verticalCenter; text: "is busy with"; color: sec.host.dim; font.pixelSize: Style.font.bodySmall }
            Toggle { anchors.verticalCenter: parent.verticalCenter; label: "cards with a label"; on: sec.kind === "label"; onClicked: sec.choose("label") }
            Toggle { anchors.verticalCenter: parent.verticalCenter; label: "every card in a column"; enabled: sec.labelColumns.length > 0; on: sec.kind === "list"; onClicked: sec.choose("list") }
            Toggle { anchors.verticalCenter: parent.verticalCenter; visible: !sec.hasNoOwner; label: "cards no bot owns"; on: sec.kind === "none"; onClicked: sec.choose("none") }
          }
          LabelPicker {
            id: picker
            visible: sec.kind === "label"
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
          Flow {
            visible: sec.kind === "list"
            width: parent.width; spacing: Style.space(4)
            Repeater {
              model: sec.labelColumns
              delegate: Toggle { required property string modelData; label: modelData; on: sec.pick === modelData; onClicked: sec.pick = modelData }
            }
          }
          BoardText {
            visible: sec.taken
            width: parent.width; wrapMode: Text.Wrap
            text: "There's already a bot named " + sec.newName + "."
            color: sec.host.urgent; font.pixelSize: Style.font.bodySmall
          }
          Row {
            spacing: Style.space(8)
            ActionButton { id: addButton; host: sec.host; small: true; main: true; enabled: sec.ready; label: "Add " + (sec.newName || "bot"); onClicked: sec.add() }
            ActionButton { host: sec.host; small: true; label: "Cancel"; onClicked: sec.cancel() }
          }
        }
      }
    }
  }

  // Busy columns: this board's label columns; names saved for other boards stay.
  Flow {
    id: busyRow
    visible: sec.bots.length > 0
    width: parent.width; spacing: Style.space(6)
    BoardText { height: Style.space(20); verticalAlignment: Text.AlignVCenter; text: "Busy columns"; color: sec.host.dim; font.pixelSize: Style.font.bodySmall }
    BoardText {
      visible: sec.labelColumns.length === 0
      height: Style.space(20); verticalAlignment: Text.AlignVCenter
      text: "Open the board to pick columns."; color: sec.host.dim; font { pixelSize: Style.font.bodySmall; italic: true }
    }
    Repeater {
      model: sec.labelColumns
      delegate: Item {
        required property string modelData
        width: busyToggle.width; height: Style.space(20)
        Toggle { id: busyToggle; anchors.verticalCenter: parent.verticalCenter; label: parent.modelData; on: Logic.has(sec.busy, parent.modelData); onClicked: sec.toggleBusy(parent.modelData) }
      }
    }
  }
}
