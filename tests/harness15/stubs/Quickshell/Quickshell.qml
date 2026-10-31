pragma Singleton
import QtQuick
// Stand-in: records what would be launched, runs nothing.
QtObject {
  property var launched: []
  function execDetached(cmd) { launched = launched.concat([cmd]) }
  function env(name) { return "" }
}
