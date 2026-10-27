import QtQuick
import qs.Commons
import qs.Commons as Commons

// Plain themed text used by every view.
Text {
  textFormat: Text.PlainText
  color: Commons.Color.popups.text
  font.family: Style.font.family
  font.pixelSize: Style.font.caption
}
