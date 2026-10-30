import QtQuick
import qs.Commons
import qs.Commons as Commons

// Small rounded text pill: counts, label chips, column toggles, choices.
Rectangle {
  id: pill
  readonly property color fg: Commons.Color.popups.text
  readonly property color bg: Commons.Color.popups.background
  property alias label: pillText.text
  property color textColor: Qt.tint(fg, Qt.rgba(bg.r, bg.g, bg.b, 0.45))
  property int pixelSize: Style.font.caption
  property bool clickable: false
  signal clicked()

  implicitWidth: pillText.implicitWidth + Style.space(10)
  implicitHeight: pillText.implicitHeight + Style.space(3)
  radius: height / 2
  color: "transparent"
  border { width: 1; color: Qt.tint(bg, Qt.rgba(fg.r, fg.g, fg.b, 0.2)) }
  BoardText { id: pillText; anchors.centerIn: parent; color: pill.textColor; font.pixelSize: pill.pixelSize }
  MouseArea { visible: pill.clickable; anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: pill.clicked() }
}
