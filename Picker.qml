import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui

// Board switcher. Step 1: pick a project (filterable). Step 2: pick one of its
// boards, or its workflow labels when it has none.
Item {
  id: view
  required property var host
  property alias filterField: filter
  readonly property bool onProjects: host.pickerStep === "projects"
  readonly property var rows: onProjects
    ? host.projects.filter(function(p) { return p.path.toLowerCase().indexOf(filter.text.trim().toLowerCase()) !== -1 })
    : host.pickerBoards

  implicitHeight: head.implicitHeight + Style.space(8) + list.contentHeight

  Column {
    id: head
    width: parent.width
    spacing: Style.space(8)

    Row {
      spacing: Style.space(8)
      Pill { label: "‹ Back"; clickable: true; textColor: view.host.foreground; onClicked: view.onProjects ? view.host.back() : view.host.pickProjectStep() }
      BoardText {
        anchors.verticalCenter: parent.verticalCenter
        text: view.onProjects ? "Choose a project" : "Choose a board in " + view.host.pickerProject
        font { pixelSize: Style.font.bodySmall; bold: true }
      }
    }

    TextField {
      id: filter
      visible: view.onProjects
      width: parent.width
      foreground: view.host.foreground
      placeholderText: "Filter projects"
      onAccepted: if (view.rows.length > 0) view.host.pickProject(view.rows[0].path)
    }

    BoardText {
      visible: text !== ""
      width: parent.width; wrapMode: Text.Wrap
      text: view.host.auxLoading ? "Loading…" : view.host.auxError
      color: view.host.dim; font.italic: true
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
      readonly property string name: view.onProjects ? modelData.path : modelData.name
      readonly property bool current: view.onProjects
        ? modelData.path === view.host.project
        : view.host.pickerProject === view.host.project && String(modelData.id) === String(view.host.boardId || view.host.resolvedBoardId)
      width: list.width - Style.space(8)
      implicitHeight: itemText.implicitHeight + Style.space(12)
      radius: Style.space(6)
      color: itemMouse.containsMouse ? view.host.faint : "transparent"
      border { width: 1; color: itemMouse.containsMouse || current ? view.host.accent : view.host.faint }
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
