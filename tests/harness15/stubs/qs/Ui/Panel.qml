import QtQuick
// Stand-in for Ui/Panel.qml (4.0.6): same API; opened is writable for the harness.
Item {
  property QtObject bar: null
  property string moduleName: ""
  property var settings: ({})
  property string ipcTarget: ""
  property bool opened: false
  function open() { opened = true }
  function close() { opened = false }
  function toggle() { opened = !opened }
  property int switchedPanel: 0
  function switchPanel(direction) { switchedPanel = direction; return false }
  function setting(name, fallback) {
    var value = settings ? settings[name] : undefined
    return value === undefined || value === null ? fallback : value
  }
}
