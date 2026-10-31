import QtQuick
import QtQuick.Effects
import qs.Commons

// Round assignee avatar: initials underneath, the image on top once it loads.
Rectangle {
  id: avatar
  required property var host
  required property var person
  readonly property string initials: String(person.name || person.username || "?").split(/\s+/)
    .map(function(w) { return w.charAt(0) }).join("").slice(0, 2).toUpperCase()
  implicitWidth: Style.space(18); implicitHeight: implicitWidth
  radius: width / 2
  color: host.faint
  border { width: 1; color: host.background }

  BoardText {
    anchors.centerIn: parent
    visible: image.status !== Image.Ready
    text: avatar.initials
    color: avatar.host.dim
    font { pixelSize: Math.max(7, avatar.height * 0.42); bold: true }
  }
  Image {
    id: image
    anchors.fill: parent
    visible: false
    source: avatar.person.avatar || ""
    sourceSize { width: avatar.width * 2; height: avatar.height * 2 }
    fillMode: Image.PreserveAspectCrop
    asynchronous: true; cache: true; smooth: true
  }
  MultiEffect {
    anchors.fill: parent
    visible: image.status === Image.Ready
    source: image
    maskEnabled: true
    maskSource: avatar.host.avatarMask  // one shared round mask (Board.qml), not one layer per avatar
    maskThresholdMin: 0.5
    maskSpreadAtMin: 1.0
  }
}
