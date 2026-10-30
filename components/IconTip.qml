import QtQuick
import qs.Commons
import qs.Ui

// The tooltip of an icon-only button: what it does, then its key in brackets
// when it has one ("Refresh (r)"). Centered under the button and kept inside
// the popup card (host.tipArea).
PanelToolTip {
  id: tip
  property var host: null
  property bool shown: false
  visible: shown && text !== ""
  y: parent ? parent.height + Style.space(6) : 0
  onAboutToShow: {
    var area = tip.host ? tip.host.tipArea : null, w = implicitWidth, want = (parent.width - w) / 2
    if (!area) { x = want; return }
    var at = parent.mapToItem(area, 0, 0).x
    x = Math.max(-at, Math.min(want, area.width - at - w))
  }
}
