import QtQuick
import QtQuick.Controls
import qs.Commons
import qs.Ui
import "Logic.js" as Logic
import "components"

// The board: the columns, and above them, when the header's columns button
// opens it (host.columnChips), a row of chips to show or hide columns. A column header
// collapses its column to a strip; clicking a card opens the issue view.
// Dragging a card past a small threshold drags a copy of it (the ghost); dropping
// it on another column, expanded or collapsed, asks the host to move the issue.
// The host's keyboard cursor lights its card like a hover and scrolls it into view.
Item {
  id: view
  required property var host
  property var dragRow: null   // card being dragged, and its column
  property var dragFrom: null
  // A card holds the mouse, from press to release. Meanwhile the host holds
  // refreshes back: new data would replace the card mid-drag.
  property bool holding: false

  // Ends a press or drag without dropping; safe to call any number of times.
  function endDrag() {
    ghost.Drag.active = false
    dragRow = null
    dragFrom = null
    holding = false
  }

  // Every column is as tall as the tallest one's content (or the viewport, if
  // taller), so panes, strips and drop areas all run the full scroll length.
  readonly property real tallest: {
    var m = 0
    for (var i = 0; i < board.children.length; i++) m = Math.max(m, board.children[i].contentHeight || 0)
    return m
  }
  function reveal(item) {
    var p = item.mapToItem(board, 0, 0)
    flick.contentX = Math.max(0, Math.min(Math.max(flick.contentX, p.x + item.width - flick.width), p.x, flick.contentWidth - flick.width))
    flick.contentY = Math.max(0, Math.min(Math.max(flick.contentY, p.y + item.height - flick.height), p.y, flick.contentHeight - flick.height))
  }
  implicitHeight: (chips.visible ? chips.implicitHeight + host.gap : 0) + Math.max(tallest, Style.space(60))

  Flow {
    id: chips
    visible: view.host.columnChips
    height: visible ? implicitHeight : 0
    width: parent.width; spacing: Style.space(4)
    Repeater {
      model: view.host.availableColumns
      delegate: Pill {
        required property var modelData
        readonly property bool shown: !view.host.isHidden(modelData.name)
        label: modelData.name + " " + Logic.countLabel(modelData)
        textColor: shown ? view.host.foreground : view.host.dim
        color: shown ? view.host.faint : "transparent"
        opacity: shown ? 1 : 0.6
        clickable: true
        onClicked: view.host.toggleHidden(modelData.name)
      }
    }
  }

  Flickable {
    id: flick
    anchors { top: chips.bottom; topMargin: chips.visible ? view.host.gap : 0; left: parent.left; right: parent.right; bottom: parent.bottom }
    contentWidth: board.implicitWidth; contentHeight: board.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
    ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }

    Row {
      id: board
      spacing: view.host.gap
      Repeater {
        model: view.host.shownColumns
        delegate: Item {
          id: column
          required property var modelData
          required property int index
          readonly property bool isCollapsed: view.host.isCollapsed(modelData.name)
          readonly property var issues: modelData.issues || []
          readonly property color tint: view.host.columnAccent(modelData)
          readonly property bool dropHot: dropArea.containsDrag
          width: isCollapsed ? view.host.stripWidth : view.host.columnWidth
          readonly property real contentHeight: isCollapsed ? strip.implicitHeight : cards.implicitHeight + Style.space(12)
          height: Math.max(view.tallest, flick.height)
          clip: true  // while the width animates
          Behavior on width { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

          // Glass pane behind the column.
          Rectangle {
            anchors.fill: parent
            radius: Style.space(8)
            color: column.dropHot ? Qt.rgba(column.tint.r, column.tint.g, column.tint.b, 0.16)
              : Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, column.isCollapsed && stripMouse.containsMouse ? 0.08 : 0.035)
            border { width: column.dropHot ? 2 : 0; color: column.tint }
            Behavior on color { ColorAnimation { duration: 120 } }
          }

          // Collapsed: a narrow strip with the count and the rotated name.
          Item {
            id: strip
            anchors.fill: parent
            opacity: column.isCollapsed ? 1 : 0
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 140 } }
            implicitHeight: stripCount.implicitHeight + stripDot.height + stripName.implicitWidth + Style.space(32)
            BoardText { id: stripCount; objectName: "stripCount"; anchors.horizontalCenter: parent.horizontalCenter; y: Style.space(8); text: Logic.countLabel(column.modelData); color: view.host.dim; font.pixelSize: Style.font.bodySmall }
            Rectangle { id: stripDot; anchors.horizontalCenter: parent.horizontalCenter; y: stripCount.y + stripCount.height + Style.space(6); width: Style.space(6); height: width; radius: width / 2; color: column.tint }
            BoardText {
              id: stripName
              anchors.horizontalCenter: parent.horizontalCenter
              y: stripDot.y + stripDot.height + Style.space(8) + (implicitWidth - implicitHeight) / 2
              rotation: 90
              text: column.modelData.name
              color: stripMouse.containsMouse ? view.host.foreground : view.host.quiet
            }
            MouseArea {
              id: stripMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
              onClicked: view.host.toggleCollapsed(column.modelData.name)
            }
            IconTip { host: view.host; shown: stripMouse.containsMouse; text: "Expand " + column.modelData.name }
          }

          // Expanded: header in the column's color, then cards. Fixed width so
          // text does not reflow while the column animates.
          Column {
            id: cards
            x: Style.space(6); y: Style.space(6)
            width: view.host.columnWidth - Style.space(12)
            spacing: Style.space(6)
            opacity: column.isCollapsed ? 0 : 1
            visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 140 } }

            Item {
              width: parent.width
              implicitHeight: headerRow.implicitHeight + Style.space(6)
              // Dot in the column's colour, the name, the count as a quiet number.
              Row {
                id: headerRow
                x: Style.space(2); y: Style.space(2)
                spacing: Style.space(6)
                Rectangle { anchors.verticalCenter: parent.verticalCenter; width: Style.space(6); height: width; radius: width / 2; color: column.tint }
                BoardText {
                  anchors.verticalCenter: parent.verticalCenter
                  text: column.modelData.name
                  color: headerMouse.containsMouse || column.issues.length > 0 ? view.host.foreground : view.host.dim
                  font { bold: true; pixelSize: Style.font.bodySmall }
                }
                BoardText { objectName: "columnCount"; anchors.verticalCenter: parent.verticalCenter; text: Logic.countLabel(column.modelData); color: view.host.quiet; font.pixelSize: Style.font.bodySmall }
              }
              MouseArea {
                id: headerMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: view.host.toggleCollapsed(column.modelData.name)
              }
              IconTip { host: view.host; shown: headerMouse.containsMouse; text: "Collapse " + column.modelData.name }
            }

            BoardText {
              visible: column.issues.length === 0
              width: parent.width; wrapMode: Text.Wrap
              text: column.modelData.note || "No issues"
              color: view.host.dim; opacity: 0.7; font.italic: true
            }

            Repeater {
              model: column.issues
              delegate: Rectangle {
                id: card
                required property var modelData
                readonly property var chips: (modelData.labels || []).filter(function(l) { return l !== column.modelData.name })
                readonly property var assignees: modelData.assignees || []
                readonly property bool keyed: view.host.cursor !== null && view.host.cursor.col === column.index && view.host.cursor.iid === modelData.iid
                onKeyedChanged: if (keyed) Qt.callLater(view.reveal, card)
                readonly property bool hovered: cardMouse.containsMouse || keyed
                readonly property bool picked: view.host.picked.indexOf(Logic.pickKey(column.modelData, modelData.iid)) !== -1
                readonly property bool movable: view.host.canDrop(column.modelData) && !view.host.move
                readonly property bool lifted: ghost.Drag.active && view.dragRow !== null && view.dragRow.iid === modelData.iid
                  && Logic.columnKey(view.dragFrom) === Logic.columnKey(column.modelData)
                readonly property color fg: view.host.foreground
                property bool pressing: false  // this card holds the mouse
                width: cards.width
                implicitHeight: cardText.implicitHeight + (chipFlow.visible ? chipFlow.implicitHeight + Style.space(6) : 0)
                  + footer.implicitHeight + Style.space(22)
                radius: Style.space(6)
                opacity: lifted || (view.host.move !== null && view.host.move.iid === modelData.iid) ? 0.4 : column.modelData.kind === "closed" ? 0.65 : 1
                color: picked ? Qt.rgba(view.host.accent.r, view.host.accent.g, view.host.accent.b, 0.1) : Qt.rgba(fg.r, fg.g, fg.b, hovered ? 0.1 : 0.05)
                border { width: picked ? 2 : 1; color: picked ? view.host.accent : hovered ? column.tint : Qt.rgba(fg.r, fg.g, fg.b, 0.1) }
                // Hover: lift by a couple of pixels and brighten.
                transform: Translate { y: card.hovered ? -Style.space(2) : 0; Behavior on y { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } } }
                Behavior on color { ColorAnimation { duration: 120 } }
                Behavior on border.color { ColorAnimation { duration: 120 } }
                // Safety net: if the board is rebuilt under a pressed card, it
                // never gets the release, so clear the drag here.
                Component.onDestruction: if (pressing) view.endDrag()

                CursorSurface { anchors.fill: parent; radius: card.radius; visible: card.keyed; hasCursor: true; foreground: card.fg; accent: view.host.accent }
                // Glass sheen along the top edge.
                Rectangle {
                  x: card.radius; y: 1; width: parent.width - card.radius * 2; height: 1
                  color: Qt.rgba(card.fg.r, card.fg.g, card.fg.b, card.hovered ? 0.22 : 0.12)
                }
                BoardText {
                  id: cardText
                  x: Style.space(8); y: Style.space(8); width: parent.width - Style.space(16)
                  textFormat: Text.StyledText
                  text: "<font color='" + view.host.dim + "'>#" + card.modelData.iid + "</font>&nbsp; " + Logic.escaped(card.modelData.title)
                  font.pixelSize: Style.font.bodySmall
                  wrapMode: Text.Wrap
                }
                Flow {
                  id: chipFlow
                  visible: card.chips.length > 0
                  x: Style.space(8); width: parent.width - Style.space(16); spacing: Style.space(4)
                  anchors { top: cardText.bottom; topMargin: Style.space(6) }
                  Repeater {
                    model: card.chips
                    delegate: LabelChip { required property var modelData; host: view.host; name: String(modelData); pixelSize: Math.max(8, Style.font.caption - 1) }
                  }
                }
                // Footer: up to three avatars (+N), then comment count and age.
                Item {
                  id: footer
                  x: Style.space(8); width: parent.width - Style.space(16)
                  anchors { top: chipFlow.visible ? chipFlow.bottom : cardText.bottom; topMargin: Style.space(6) }
                  implicitHeight: Math.max(people.implicitHeight, meta.implicitHeight)
                  Row {
                    id: people
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: -Style.space(4)
                    Repeater {
                      model: card.assignees.slice(0, card.assignees.length > 3 ? 2 : 3)
                      delegate: Avatar { required property var modelData; host: view.host; person: modelData }
                    }
                    Pill {
                      visible: card.assignees.length > 3
                      anchors.verticalCenter: parent.verticalCenter
                      label: "+" + (card.assignees.length - 2)
                      color: view.host.faint
                      pixelSize: Math.max(8, Style.font.caption - 1)
                    }
                  }
                  BoardText {
                    id: meta
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    text: (card.modelData.notes > 0 ? "\uf075 " + card.modelData.notes + "   " : "") + Logic.age(card.modelData.createdAt, view.host.updatedAt)
                    color: view.host.dim
                    font.pixelSize: Math.max(8, Style.font.caption - 1)
                  }
                }
                MouseArea {
                  id: cardMouse; anchors.fill: parent; hoverEnabled: true
                  cursorShape: ghost.Drag.active && card.lifted ? Qt.ClosedHandCursor : Qt.PointingHandCursor
                  property point pressedAt
                  property bool dragged: false
                  // The Flickable must not take the press over; a drag starts
                  // once the pointer has moved past the threshold.
                  preventStealing: true
                  onPressed: function(mouse) { pressedAt = Qt.point(mouse.x, mouse.y); dragged = false; card.pressing = true; view.holding = true }
                  onPositionChanged: function(mouse) {
                    if (!pressed) return
                    if (!dragged) {
                      if (!card.movable || Math.abs(mouse.x - pressedAt.x) + Math.abs(mouse.y - pressedAt.y) < Style.space(8)) return
                      dragged = true
                      view.dragRow = card.modelData
                      view.dragFrom = column.modelData
                      ghost.width = card.width
                      ghost.Drag.hotSpot = pressedAt
                    }
                    var p = mapToItem(view, mouse.x, mouse.y)
                    ghost.x = p.x - pressedAt.x
                    ghost.y = p.y - pressedAt.y
                    ghost.Drag.active = true
                  }
                  onReleased: { if (dragged && ghost.Drag.active) ghost.Drag.drop(); card.pressing = false; view.endDrag() }
                  onCanceled: { card.pressing = false; view.endDrag() }
                  // Ctrl+click picks the card for a bulk action (BulkBar.qml).
                  onClicked: function(mouse) {
                    if (dragged) return
                    if (mouse.modifiers & Qt.ControlModifier) view.host.togglePick(column.modelData, card.modelData.iid)
                    else view.host.openIssue(card.modelData)
                  }
                }
                // A picked card: a check on its corner.
                Rectangle {
                  objectName: "pickMark"
                  visible: card.picked; z: 5
                  anchors { right: parent.right; top: parent.top; margins: -Style.space(5) }
                  width: Style.space(16); height: width; radius: width / 2; color: view.host.accent
                  BoardText { anchors.centerIn: parent; text: "\uf00c"; color: view.host.background; font.pixelSize: Style.space(9) }
                }
                // Review cards: their merge request's pipeline, left of the age; above
                // cardMouse, so a click opens the pipeline, not the issue.
                PipelineMark {
                  id: pipelineMark
                  host: view.host
                  pipeline: card.modelData.pipeline || null
                  x: footer.x + meta.x - width - Style.space(8)
                  y: footer.y + (footer.height - height) / 2
                }
              }
            }

            // A capped column (board-fetch: Closed holds the latest 20 when there are more) says so
            // and links to the rest on GitLab. Open and label columns are never capped.
            BoardText {
              visible: !!column.modelData.seeAll
              width: parent.width; wrapMode: Text.Wrap
              horizontalAlignment: Text.AlignHCenter
              topPadding: Style.space(2)
              text: "Showing the latest " + column.issues.length + " · See all on GitLab ↗"
              color: seeAllMouse.containsMouse ? view.host.accent : view.host.dim
              font.pixelSize: Style.font.caption
              MouseArea { id: seeAllMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: view.host.openUrl(column.modelData.seeAll) }
            }
          }

          // Drop target: the whole column, strip included. Never the column the
          // card came from, nor columns the host cannot move into.
          DropArea {
            id: dropArea
            anchors.fill: parent
            keys: ["odevvy-gitlab-issue"]
            enabled: view.dragFrom !== null && view.host.canDrop(column.modelData)
              && Logic.columnKey(view.dragFrom) !== Logic.columnKey(column.modelData)
            onDropped: {
              var row = view.dragRow, from = view.dragFrom, to = column.modelData
              Qt.callLater(function() { view.host.requestMove(row, from, to) })  // after the press ends
            }
          }
        }
      }
    }
  }

  // The dragged copy of a card; the card's MouseArea moves it and sets Drag.active.
  Rectangle {
    id: ghost
    visible: Drag.active
    z: 10
    height: ghostText.implicitHeight + Style.space(16)
    radius: Style.space(6)
    color: view.host.background
    border { width: 1; color: view.host.accent }
    opacity: 0.92
    Drag.keys: ["odevvy-gitlab-issue"]
    BoardText {
      id: ghostText
      x: Style.space(8); y: Style.space(8); width: parent.width - Style.space(16)
      text: view.dragRow ? "#" + view.dragRow.iid + "  " + view.dragRow.title : ""
      font.pixelSize: Style.font.bodySmall
      elide: Text.ElideRight
      maximumLineCount: 2; wrapMode: Text.Wrap
    }
  }
}
