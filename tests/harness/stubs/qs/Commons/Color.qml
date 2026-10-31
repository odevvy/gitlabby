pragma Singleton
import QtQuick
// Stand-in theme close to the user's (dark blue card, warm text, orange accent).
QtObject {
  readonly property color foreground: "#e8d5b0"
  readonly property color accent: "#e8935a"
  readonly property color urgent: "#e06c75"
  readonly property color muted: "#7f8a99"
  readonly property QtObject popups: QtObject {
    readonly property color background: "#14233a"
    readonly property color text: "#e8d5b0"
    readonly property color border: "#e8935a"
  }
  readonly property QtObject tooltip: QtObject {
    readonly property color background: "#14233a"
    readonly property color text: "#e8d5b0"
    readonly property color border: "#e8935a"
  }
}
