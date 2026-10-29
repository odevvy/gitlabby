import QtQuick
import qs.Commons

// First run, in place of the board and at the placeholder board's size (so the
// popup doesn't jump when the board arrives): install glab, sign in, or pick a
// project. Checks again only on Try again, r, or when the popup opens.
Item {
  id: setupView
  required property var host
  readonly property string mode: host.setup
  readonly property string step: mode === "pick" ? (host.boardState === "error" ? "error" : host.boardState === "ready" ? "pick" : "checking") : mode
  property bool copied: false
  onModeChanged: copied = false

  // Enter: the main button of the panel.
  function primary() {
    if (step === "logged-out") host.signIn()
    else if (step === "no-glab") copy()
    else if (step === "pick") host.openPicker()
    else if (step === "error") host.refresh()
  }
  function copy() { host.copyInstall(); copied = true }

  implicitWidth: column.implicitWidth
  implicitHeight: column.implicitHeight + Style.space(48)

  // Buttons styled like Omarchy's ConfirmDialog (Ui/ConfirmDialog.qml):
  // the main one in the accent on a faint fill, the other a quiet outline.
  component SetupButton: Rectangle {
    id: button
    property string label: ""
    property bool main: false
    signal clicked()
    readonly property color fg: setupView.host.foreground
    implicitWidth: Math.max(Style.space(120), buttonText.implicitWidth + Style.space(32))
    implicitHeight: Style.space(34)
    color: main || mouse.containsMouse ? Qt.rgba(fg.r, fg.g, fg.b, 0.08) : "transparent"
    border { width: 1; color: main || mouse.containsMouse ? setupView.host.accent : Qt.rgba(fg.r, fg.g, fg.b, 0.38) }
    BoardText {
      id: buttonText
      anchors.centerIn: parent
      text: button.label
      color: button.main ? setupView.host.accent : button.fg
      font { pixelSize: Style.font.body; bold: button.main }
    }
    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: button.clicked() }
  }

  Column {
    id: column
    anchors.centerIn: parent
    width: Math.min(parent.width, Style.space(440))
    spacing: Style.space(12)

    BoardText {
      anchors.horizontalCenter: parent.horizontalCenter
      text: setupView.host.icon
      color: setupView.host.accent
      font.pixelSize: Style.space(40)
    }
    BoardText {
      width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
      font { pixelSize: Style.font.title; bold: true }
      text: ({ "logged-out": "Sign in to GitLab", "no-glab": "Install glab", checking: "Checking GitLab…",
               error: "Could not reach GitLab", pick: "Choose a project" })[setupView.step] || ""
    }
    BoardText {
      width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
      color: setupView.host.dim
      visible: text !== ""
      text: setupView.step === "logged-out" ? "This board reads your issues through glab. Sign in once and you're set."
        : setupView.step === "no-glab" ? "This board reads your issues through glab, GitLab's command-line tool. Install it in a terminal:"
        : setupView.step === "error" ? setupView.host.message
        : setupView.step === "pick" ? "Pick a project and board. The first one you open becomes your default." : ""
    }

    // The install command, with Copy.
    Row {
      visible: setupView.step === "no-glab"
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: Style.space(8)
      Rectangle {
        width: command.implicitWidth + Style.space(24); height: Style.space(34)
        color: setupView.host.faint
        border { width: 1; color: Qt.rgba(setupView.host.foreground.r, setupView.host.foreground.g, setupView.host.foreground.b, 0.12) }
        BoardText { id: command; anchors.centerIn: parent; text: setupView.host.installCommand }
      }
      SetupButton { label: setupView.copied ? "Copied" : "Copy"; main: true; onClicked: setupView.copy() }
    }

    Row {
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: Style.space(10)
      SetupButton {
        visible: setupView.step === "logged-out"
        label: "Sign in to GitLab"; main: true
        onClicked: setupView.host.signIn()
      }
      SetupButton {
        visible: setupView.step === "pick"
        label: "Choose a project"; main: true
        onClicked: setupView.host.openPicker()
      }
      SetupButton {
        visible: setupView.step === "logged-out" || setupView.step === "no-glab" || setupView.step === "error"
        label: "Try again"; main: setupView.step === "error"
        onClicked: setupView.host.refresh()
      }
    }

    BoardText {
      width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
      visible: setupView.step === "logged-out"
      color: setupView.host.dim
      font.pixelSize: Style.font.bodySmall
      text: "A terminal opens. Follow the steps there, then come back here."
    }
  }
}
