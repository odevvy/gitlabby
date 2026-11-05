import QtQuick
import QtQuick.Effects
import qs.Commons

// Round assignee avatar: initials underneath, the image on top once it loads
// (never loaded when Settings > Show avatars is off: then the initials stay).
Rectangle {
  id: avatar
  required property var host
  required property var person
  readonly property string initials: String(person.name || person.username || "?").split(/\s+/)
    .map(function(w) { return w.charAt(0) }).join("").slice(0, 2).toUpperCase()
  implicitWidth: Style.space(18); implicitHeight: implicitWidth
  radius: width / 2
  // Initials circle (what shows while a picture loads, and always with Show
  // avatars off): a soft tint of a colour that stays the same for a person.
  // The username's hash turns the theme accent's hue in 8 steps (45 degrees
  // apart), keeping the theme's saturation and lightness.
  readonly property real hueShift: {
    var s = String(person.username || person.name || ""), h = 0
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360
    return (Math.floor(h / 45) * 45) / 360
  }
  readonly property color tone: Qt.hsla((host.accent.hslHue + hueShift) % 1, host.accent.hslSaturation * 0.7, Math.max(0.55, host.accent.hslLightness), 1)
  color: Qt.tint(host.background, Qt.rgba(tone.r, tone.g, tone.b, 0.30))
  border { width: 1; color: host.background }

  BoardText {
    anchors.centerIn: parent
    visible: image.status !== Image.Ready
    text: avatar.initials
    objectName: "avatarInitials"
    color: Qt.tint(avatar.tone, Qt.rgba(1, 1, 1, 0.25))
    font { pixelSize: Math.max(7, avatar.height * 0.40); weight: Font.DemiBold }
  }
  Image {
    id: image
    objectName: "avatarImage"
    anchors.fill: parent
    visible: false
    source: avatar.host.showAvatars ? avatar.person.avatar || "" : ""  // off: no request at all
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
