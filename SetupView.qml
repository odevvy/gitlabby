import QtQuick
import qs.Commons

// First run, in place of the board: install glab, sign in, or pick a
// project. Checks again only on Try again or when the popup opens.
Item {
  id: setupView
  required property var host
  readonly property string mode: host.setup
  property bool copied: false
  onModeChanged: copied = false

  implicitWidth: column.implicitWidth
  implicitHeight: column.implicitHeight + Style.space(24)

  Column {
    id: column
    anchors { left: parent.left; right: parent.right; top: parent.top; topMargin: Style.space(12) }
    spacing: Style.space(10)

    BoardText {
      width: parent.width
      wrapMode: Text.Wrap
      font { pixelSize: Style.font.title; bold: true }
      text: setupView.mode === "no-glab" ? "Install the GitLab CLI"
        : setupView.mode === "logged-out" ? "Sign in to GitLab"
        : setupView.host.boardState === "loading" ? "Checking GitLab…"
        : setupView.host.boardState === "error" ? "Could not reach GitLab"
        : "Choose a project"
    }
    BoardText {
      width: parent.width
      wrapMode: Text.Wrap
      color: setupView.host.dim
      text: setupView.mode === "no-glab" ? "The board reads GitLab through glab. Install it in a terminal:"
        : setupView.mode === "logged-out" ? "Sign in once with glab in a terminal; it keeps the login, not this board."
        : setupView.host.boardState === "error" ? setupView.host.message
        : setupView.host.boardState === "loading" ? "" : "Pick a project and board. The first one you open becomes your default."
    }

    Row {
      visible: setupView.mode === "no-glab"
      spacing: Style.space(8)
      Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        width: command.implicitWidth + Style.space(16); height: command.implicitHeight + Style.space(8)
        radius: Style.space(4); color: setupView.host.faint
        BoardText { id: command; anchors.centerIn: parent; text: setupView.host.installCommand }
      }
      Pill {
        anchors.verticalCenter: parent.verticalCenter
        label: setupView.copied ? "Copied" : "Copy"
        pixelSize: Style.font.bodySmall; clickable: true
        onClicked: { setupView.host.copyInstall(); setupView.copied = true }
      }
    }

    Row {
      spacing: Style.space(8)
      Pill {
        visible: setupView.mode === "logged-out"
        label: "Sign in to GitLab"; textColor: setupView.host.accent
        pixelSize: Style.font.body; clickable: true
        onClicked: setupView.host.signIn()
      }
      Pill {
        visible: setupView.mode === "pick" && setupView.host.boardState === "ready"
        label: "Choose a project"; textColor: setupView.host.accent
        pixelSize: Style.font.body; clickable: true
        onClicked: setupView.host.openPicker()
      }
      Pill {
        visible: setupView.mode !== "pick" || setupView.host.boardState === "error"
        label: "Try again"
        pixelSize: Style.font.body; clickable: true
        onClicked: setupView.host.refresh()
      }
    }
  }
}
