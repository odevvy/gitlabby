import QtQuick
// Stand-in: reads the path (local files only). The harness sets
// QML_XHR_ALLOW_FILE_READ so this XMLHttpRequest works offscreen.
Item {
  id: fv
  property string path: ""
  property bool blockLoading: false
  property bool watchChanges: false
  property bool printErrors: false
  property string _data: ""
  signal loaded()
  signal loadFailed()
  function text() { return _data }
  function reload() {
    _data = ""
    if (path === "") { loadFailed(); return }
    var url = path.indexOf("://") >= 0 ? path : "file://" + path
    try {
      var req = new XMLHttpRequest()
      req.open("GET", url, false)
      req.send()
      if (req.status === 200 || req.status === 0) { _data = String(req.responseText || ""); loaded() }
      else loadFailed()
    } catch (e) { loadFailed() }
  }
  onPathChanged: reload()
  Component.onCompleted: if (path !== "") reload()
}
