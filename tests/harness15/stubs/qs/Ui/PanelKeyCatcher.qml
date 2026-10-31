import QtQuick
// Stand-in for Ui/PanelKeyCatcher.qml: h/j/k/l and arrows move, Enter/Space
// activate, Escape closes, Tab switches, x/X delete, other printable keys go
// to textKey (Shift+H is "H").
Item {  // an Item like the real one (PanelKeyCatcher.qml), not a FocusScope
  id: catcher
  focus: true
  property bool blocked: false
  signal moveRequested(int dx, int dy)
  signal activateRequested()
  signal returnRequested()
  signal closeRequested()
  signal deleteRequested()
  signal tabRequested(int direction)
  signal textKey(string text)
  Keys.priority: Keys.BeforeItem  // first, even when a descendant has focus (as the real one)
  Keys.onPressed: function(event) {
    if (catcher.blocked) return
    var k = event.key
    if (k === Qt.Key_Escape) closeRequested()
    else if (k === Qt.Key_Left || event.text === "h") moveRequested(-1, 0)
    else if (k === Qt.Key_Right || event.text === "l") moveRequested(1, 0)
    else if (k === Qt.Key_Up || event.text === "k") moveRequested(0, -1)
    else if (k === Qt.Key_Down || event.text === "j") moveRequested(0, 1)
    else if (k === Qt.Key_Return || k === Qt.Key_Enter) { returnRequested(); activateRequested() }
    else if (k === Qt.Key_Space) activateRequested()
    else if (k === Qt.Key_Tab) tabRequested(1)
    else if (k === Qt.Key_Backtab) tabRequested(-1)
    else if (event.text === "x" || event.text === "X") deleteRequested()  // like the real one
    else if (event.text !== "") textKey(event.text)
    else return
    event.accepted = true
  }
}
