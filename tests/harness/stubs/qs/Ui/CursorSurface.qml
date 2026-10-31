import QtQuick
import qs.Commons
import qs.Commons as Commons
Rectangle {
  property bool hasCursor: false
  property bool current: false
  property bool outline: false
  property bool bordered: false
  property color foreground: Commons.Color.foreground
  property color accent: Commons.Color.accent
  color: "transparent"
  border { width: hasCursor ? 2 : 0; color: accent }
}
