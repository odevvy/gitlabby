import QtQuick
import qs.Commons
import qs.Commons as Commons
// Stand-in for Ui/KeyboardPanel.qml: the popup card drawn in the harness window
// under the bar button; children fill the padded content area.
Rectangle {
  id: card
  property Item anchorItem: null
  property QtObject bar: null
  property var owner: null
  property int padding: Style.spacing.popupPadding
  property int contentWidth: 280
  property int contentHeight: 200
  property bool open: false
  property Item focusTarget: null
  property real availableCardWidth: 1240
  property real availableCardHeight: 1600
  readonly property real verticalContentInset: padding * 2 + 2
  function fittedContentWidth(width, cap) {
    var desired = Math.max(1, Number(width) || 1), maxWidth = availableCardWidth
    if (cap !== undefined && Number(cap) > 0) maxWidth = Math.min(maxWidth, Number(cap))
    return Math.round(Math.min(desired, maxWidth))
  }
  function fittedContentHeight(implicitHeight, cap) {
    var desired = Math.max(verticalContentInset, (Number(implicitHeight) || 0) + verticalContentInset), maxHeight = availableCardHeight
    if (cap !== undefined && Number(cap) > 0) maxHeight = Math.min(maxHeight, Number(cap))
    return Math.round(Math.min(desired, maxHeight))
  }
  default property alias content: inner.data
  parent: anchorItem ? anchorItem.Window.contentItem : null
  x: 8; y: 40
  visible: open
  width: contentWidth; height: contentHeight
  color: Commons.Color.popups.background
  border { width: 1; color: Commons.Color.popups.border }
  Item { id: inner; anchors.fill: parent; anchors.margins: card.padding }
}
