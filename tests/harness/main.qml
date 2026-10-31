import QtQuick
import QtQuick.Window
Window {
  id: win
  width: 1300; height: 1000
  visible: true
  color: "#0b1c30"
  Board { id: board; objectName: "board"; x: 0; y: 0 }
}
