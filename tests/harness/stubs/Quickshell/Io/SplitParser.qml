import QtQuick
// Stand-in: the harness emits read(line) for each line a process "prints".
QtObject {
  property string splitMarker: "\n"
  signal read(string data)
}
