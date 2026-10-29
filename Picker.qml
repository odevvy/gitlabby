import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui

// Board switcher. Step 1: pick a project (filterable). Step 2: pick one of its
// boards, or its workflow labels when it has none. ‹ steps back to the
// projects; ✕ or Esc returns to the board. Up and down (j/k too, outside the
// filter) move a row cursor; Enter picks it, or the first row.
Item {
  id: view
  required property var host
  property alias filterField: filter
  readonly property bool onProjects: host.pickerStep === "projects"
  readonly property var rows: onProjects
    ? host.projects.filter(function(p) { return p.path.toLowerCase().indexOf(filter.text.trim().toLowerCase()) !== -1 })
    : host.pickerBoards
  readonly property bool typing: filter.activeFocus
  property int cursor: -1  // -1: none drawn
  onRowsChanged: cursor = -1
  onCursorChanged: if (cursor >= 0) list.positionViewAtIndex(cursor, ListView.Contain)
  function moveCursor(dy) { cursor = Math.max(0, Math.min(cursor + dy, rows.length - 1)) }
  function activate() {
    var row = rows[Math.max(cursor, 0)]
    if (row) onProjects ? host.pickProject(row.path) : host.pickBoard(row)
  }

  implicitHeight: head.implicitHeight + Style.space(8) + list.contentHeight

  Column {
    id: head
    width: parent.width
    spacing: Style.space(8)

    Item {
      width: parent.width
      implicitHeight: close.implicitHeight
      Row {
        anchors { left: parent.left; right: close.left; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
        spacing: Style.space(4)
        GlyphButton { id: stepBack; visible: !view.onProjects; host: view.host; glyph: "\uf053"; onClicked: view.host.pickProjectStep() }
        BoardText {
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width - (stepBack.visible ? stepBack.width + parent.spacing : 0)
          elide: Text.ElideMiddle
          text: view.onProjects ? "Choose a project" : "Choose a board in " + view.host.pickerProject
          font { pixelSize: Style.font.bodySmall; bold: true }
        }
      }
      GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; onClicked: view.host.back() }
    }

    TextField {
      id: filter
      visible: view.onProjects
      width: parent.width
      foreground: view.host.foreground
      placeholderText: "Filter projects"
      onAccepted: view.activate()
      Keys.onUpPressed: view.moveCursor(-1)
      Keys.onDownPressed: view.moveCursor(1)
      Keys.onEscapePressed: view.host.back()
    }

    Row {
      width: parent.width; spacing: Style.space(6)
      visible: auxStatus.text !== ""
      Spinner { id: auxSpinner; running: view.host.auxLoading; anchors.verticalCenter: auxStatus.verticalCenter }
      BoardText {
        id: auxStatus
        width: parent.width - (auxSpinner.visible ? auxSpinner.width + parent.spacing : 0); wrapMode: Text.Wrap
        text: view.host.auxLoading ? "Loading…" : view.host.auxError
        color: view.host.dim; font.italic: true
      }
    }
  }

  ListView {
    id: list
    anchors { top: head.bottom; topMargin: Style.space(8); left: parent.left; right: parent.right; bottom: parent.bottom }
    clip: true; boundsBehavior: Flickable.StopAtBounds
    spacing: Style.space(4)
    model: view.host.auxLoading ? [] : view.rows
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
    delegate: Rectangle {
      id: item
      required property var modelData
      required property int index
      readonly property bool hot: itemMouse.containsMouse || index === view.cursor
      readonly property string name: view.onProjects ? modelData.path : modelData.name
      readonly property bool current: view.onProjects
        ? modelData.path === view.host.project
        : view.host.pickerProject === view.host.project && String(modelData.id) === String(view.host.boardId || view.host.resolvedBoardId)
      width: list.width - Style.space(8)
      implicitHeight: itemText.implicitHeight + Style.space(12)
      radius: Style.space(6)
      color: hot ? view.host.faint : "transparent"
      border { width: 1; color: hot || current ? view.host.accent : view.host.faint }
      BoardText {
        id: itemText
        x: Style.space(8); anchors.verticalCenter: parent.verticalCenter; width: parent.width - Style.space(16) - (star.visible ? star.width + Style.space(8) : 0)
        elide: Text.ElideMiddle
        text: item.name
        font.pixelSize: Style.font.bodySmall
      }
      MouseArea {
        id: itemMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onClicked: view.onProjects ? view.host.pickProject(item.modelData.path) : view.host.pickBoard(item.modelData)
      }
      // Star = default board (one per widget); clicking it does not switch boards.
      BoardText {
        id: star
        visible: !view.onProjects
        readonly property bool on: visible && view.host.isDefaultBoard(item.modelData)
        anchors { right: parent.right; rightMargin: Style.space(8); verticalCenter: parent.verticalCenter }
        text: on ? "\uf005" : "\uf006"
        color: on || starMouse.containsMouse ? view.host.accent : view.host.dim
        font.pixelSize: Style.font.body
        MouseArea {
          id: starMouse; anchors.fill: parent; anchors.margins: -Style.space(6)
          hoverEnabled: true; cursorShape: Qt.PointingHandCursor
          onClicked: view.host.setDefault(item.modelData)
        }
      }
    }
  }
}
