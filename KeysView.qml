import QtQuick
import qs.Commons
import "Logic.js" as Logic

// The popup's keys (Logic.keys, also in the README). ? toggles it; ✕ or Esc
// returns to the board.
Item {
  id: view
  required property var host

  implicitHeight: content.implicitHeight

  Column {
    id: content
    width: parent.width
    spacing: Style.space(8)

    Item {
      width: parent.width
      implicitHeight: close.implicitHeight
      BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Keys"; font { pixelSize: Style.font.bodySmall; bold: true } }
      GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; onClicked: view.host.back() }
    }

    Repeater {
      model: Logic.keys
      delegate: Row {
        id: keyRow
        required property var modelData
        spacing: Style.space(12)
        BoardText { width: Style.space(130); text: keyRow.modelData[0]; color: view.host.accent; font { pixelSize: Style.font.bodySmall; bold: true } }
        BoardText { width: content.width - Style.space(142); wrapMode: Text.Wrap; text: keyRow.modelData[1]; font.pixelSize: Style.font.bodySmall }
      }
    }
  }
}
