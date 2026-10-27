import QtQuick
import QtQuick.Controls
import qs.Commons

// The board: chips to show or hide columns, then the columns. A column header
// collapses its column to a strip; clicking a card opens the issue view.
Item {
  id: view
  required property var host

  implicitHeight: chips.implicitHeight + host.gap + Math.max(board.implicitHeight, Style.space(60))

  Flow {
    id: chips
    width: parent.width; spacing: Style.space(4)
    Repeater {
      model: view.host.availableColumns
      delegate: Pill {
        required property var modelData
        readonly property bool shown: !view.host.isHidden(modelData.name)
        label: modelData.name + " " + (modelData.issues || []).length
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
    anchors { top: chips.bottom; topMargin: view.host.gap; left: parent.left; right: parent.right; bottom: parent.bottom }
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
          readonly property bool isCollapsed: view.host.isCollapsed(modelData.name)
          readonly property var issues: modelData.issues || []
          width: isCollapsed ? view.host.stripWidth : view.host.columnWidth
          implicitHeight: isCollapsed ? Math.max(strip.implicitHeight, flick.height) : cards.implicitHeight

          // Collapsed: a narrow strip with the count and the rotated name.
          Rectangle {
            id: strip
            visible: column.isCollapsed
            anchors.fill: parent
            implicitHeight: stripCount.implicitHeight + stripName.implicitWidth + Style.space(24)
            radius: Style.space(6)
            color: stripMouse.containsMouse ? view.host.faint : "transparent"
            border { width: 1; color: view.host.faint }
            Pill { id: stripCount; anchors.horizontalCenter: parent.horizontalCenter; y: Style.space(6); label: String(column.issues.length); textColor: view.host.foreground }
            BoardText {
              id: stripName
              anchors.horizontalCenter: parent.horizontalCenter
              y: stripCount.y + stripCount.height + Style.space(6) + (implicitWidth - implicitHeight) / 2
              rotation: 90
              text: column.modelData.name
              color: view.host.dim
              font.capitalization: Font.AllUppercase
            }
            MouseArea {
              id: stripMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
              onClicked: view.host.toggleCollapsed(column.modelData.name)
            }
          }

          // Expanded: header with count badge and accent underline, then cards.
          Column {
            id: cards
            visible: !column.isCollapsed
            width: parent.width
            spacing: Style.space(6)

            Item {
              width: parent.width
              implicitHeight: headerRow.implicitHeight + Style.space(6)
              Row {
                id: headerRow
                spacing: Style.space(6)
                BoardText {
                  anchors.verticalCenter: parent.verticalCenter
                  text: column.modelData.name
                  font { bold: true; capitalization: Font.AllUppercase }
                }
                Pill { anchors.verticalCenter: parent.verticalCenter; label: String(column.issues.length); color: view.host.faint }
              }
              Rectangle {
                anchors.bottom: parent.bottom; width: parent.width; height: Math.max(1, Style.space(2))
                color: view.host.accent; opacity: headerMouse.containsMouse ? 1 : 0.6
              }
              MouseArea {
                id: headerMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: view.host.toggleCollapsed(column.modelData.name)
              }
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
                width: column.width
                implicitHeight: cardText.implicitHeight + (chipFlow.visible ? chipFlow.implicitHeight + Style.space(6) : 0) + Style.space(16)
                radius: Style.space(6)
                opacity: column.modelData.kind === "closed" ? 0.65 : 1
                color: cardMouse.containsMouse ? view.host.faint : "transparent"
                border { width: 1; color: cardMouse.containsMouse ? view.host.accent : view.host.faint }
                BoardText {
                  id: cardText
                  x: Style.space(8); y: Style.space(8); width: parent.width - Style.space(16)
                  textFormat: Text.StyledText
                  text: "<font color='" + view.host.dim + "'>#" + card.modelData.iid + "</font>&nbsp; " + view.host.escaped(card.modelData.title)
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
                    delegate: Pill { required property var modelData; label: String(modelData); pixelSize: Math.max(8, Style.font.caption - 1) }
                  }
                }
                MouseArea {
                  id: cardMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: view.host.openIssue(card.modelData)
                }
              }
            }
          }
        }
      }
    }
  }
}
