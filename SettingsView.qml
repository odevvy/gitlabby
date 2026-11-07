import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Logic.js" as Logic
import "components"

// In-popup settings in four sections, each under a thin rule and a small
// heading (Omarchy's PanelSeparator and PanelSectionHeader): General (how often
// to refresh, which columns new boards start with folded), Bots (BotsSection),
// Alerts (three check boxes) and Account (who is signed in, Sign out). Help is one
// quiet line. Changes are saved to shell.json right away. The gear, ✕ or Esc
// returns to the board.
Item {
  id: view
  required property var host
  readonly property color fg: host.foreground
  readonly property color pane: Qt.rgba(fg.r, fg.g, fg.b, 0.035)
  readonly property color line: Qt.rgba(fg.r, fg.g, fg.b, 0.08)
  property bool confirming: false  // Sign out asks first, inline
  onVisibleChanged: {
    confirming = false
    botsSection.cancel()
    if (visible && botsSection.bots.length > 0) loadLabels()  // to flag a bot label the project no longer has
    resetServer()
  }
  readonly property bool typing: botsSection.typing || hostField.activeFocus

  // General > GitLab server: a plain field. Use (or Enter) saves a bare name
  // and switches; typing alone does nothing. Anything else (http, a port, a
  // path) gets the error under it, and Use stays hidden.
  readonly property string hostCandidate: hostField.text.trim() === "" ? "gitlab.com" : Logic.serverHost(hostField.text)
  readonly property bool hostBad: hostCandidate === ""
  readonly property bool hostNew: !hostBad && (hostCandidate !== host.gitlabHost || host.hostInvalid)
  function resetServer() { hostField.text = host.savedHost }
  function useServer() { if (hostNew && host.useServer(hostCandidate)) hostField.text = hostCandidate }
  function focusServer() { flick.contentY = 0; hostField.forceActiveFocus(); hostField.selectAll() }
  Connections { target: view.host; function onSavedHostChanged() { view.resetServer() } }
  readonly property bool adding: botsSection.adding
  function cancelAdd() { botsSection.cancel() }

  // The project's labels for Settings > Bots (`board-fetch labels`, GET), once per project.
  property string labelsFor: ""
  property string labelsState: ""  // "", loading, ready, error
  property string labelsError: ""
  property var allLabels: []
  property var fetchedStatus: []
  function loadLabels() {
    if (labelsProcess.running || (labelsFor === host.projectKey && labelsState === "ready")) return
    labelsFor = host.projectKey
    labelsState = "loading"
    labelsProcess.command = host.helperCommand(["labels", "--project", host.project])
    labelsProcess.running = true
  }
  function labelsDone(raw) {
    if (labelsFor !== host.projectKey) {  // the project (or server) changed meanwhile
      labelsState = ""
      if (botsSection.adding) Qt.callLater(loadLabels)
      return
    }
    var data = host.parse(raw)
    labelsState = data.state === "ready" ? "ready" : "error"
    labelsError = data.state === "ready" ? "" : String(data.message || "Could not load labels.")
    if (data.state === "ready") { allLabels = data.labels || []; fetchedStatus = data.status || [] }
  }
  Process {
    id: labelsProcess
    stdout: StdioCollector { waitForEnd: true; onStreamFinished: view.labelsDone(text) }
  }

  implicitHeight: top.implicitHeight + Style.space(6) + content.implicitHeight

  // Section heading, like Omarchy's PanelSectionHeader.
  component Heading: BoardText {
    color: view.host.dim
    font { pixelSize: Style.font.caption; bold: true; capitalization: Font.AllUppercase; letterSpacing: 1 }
  }
  // The thin rule above a section (Omarchy's PanelSeparator, fg at 12%).
  component Rule: Rectangle { objectName: "sectionRule"; width: parent ? parent.width : 0; height: 1; color: Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.12) }
  // A setting's name, and its one line of help.
  component Label: BoardText { font.pixelSize: Style.font.bodySmall }
  component Help: BoardText { width: parent ? parent.width : 0; wrapMode: Text.Wrap; color: view.host.quiet; font.pixelSize: Style.font.caption }
  // A check box: ticked is an accent outline, tint and tick; unticked a hairline square.
  component CheckBox: Rectangle {
    property bool on: false
    property bool hot: false
    width: Style.space(14); height: width; radius: Style.space(3)
    color: on ? Qt.rgba(view.host.accent.r, view.host.accent.g, view.host.accent.b, 0.18) : "transparent"
    border { width: 1; color: on ? view.host.accent : hot ? view.host.foreground : Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.3) }
    BoardText { anchors.centerIn: parent; visible: parent.on; text: "\uf00c"; color: view.host.accent; font.pixelSize: Style.font.caption }
  }

  // Fixed top row: only the settings below it scroll.
  Item {
    id: top
    width: parent.width
    implicitHeight: close.implicitHeight
    BoardText { anchors.verticalCenter: parent.verticalCenter; text: "Settings"; font { pixelSize: Style.font.subtitle; bold: true } }
    GlyphButton { id: close; anchors.right: parent.right; host: view.host; glyph: "\uf00d"; tip: "Back to the board (Esc)"; onClicked: view.host.back() }
  }

  Flickable {
    id: flick
    anchors { top: top.bottom; topMargin: Style.space(6); left: parent.left; right: parent.right; bottom: parent.bottom }
    contentWidth: width; contentHeight: content.implicitHeight
    clip: true; boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

    Column {
      id: content
      width: parent.width - Style.space(8)
      spacing: Style.space(6)

      Item { width: 1; height: Style.space(2) }
      Heading { text: "General" }
      Item {
        id: hostRow
        objectName: "hostRow"
        width: parent.width
        implicitHeight: Math.max(hostLabel.implicitHeight, hostField.implicitHeight)
        Label { id: hostLabel; y: (parent.implicitHeight - implicitHeight) / 2; text: "GitLab server" }
        Row {
          anchors.right: parent.right
          spacing: Style.space(8)
          TextField {
            id: hostField
            objectName: "hostField"
            width: Style.space(244); verticalPadding: Style.space(3)
            font.pixelSize: Style.font.bodySmall; foreground: view.host.foreground
            placeholderText: "gitlab.com"
            onAccepted: view.useServer()
            Keys.onEscapePressed: { view.resetServer(); view.host.focusBoard() }
          }
          ActionButton {
            objectName: "hostUse"
            anchors.verticalCenter: parent.verticalCenter
            host: view.host; small: true; main: true; label: "Use"
            visible: view.hostNew
            onClicked: view.useServer()
          }
        }
      }
      Help {
        objectName: "hostHelp"
        color: view.hostBad ? view.host.urgent : view.host.quiet
        text: view.hostBad ? "Just the server's name, like gitlab.example.com: no https://, no path, no port (glab keeps those)."
            + (view.host.hostInvalid && hostField.text === view.host.savedHost ? " Until then the board uses gitlab.com." : "")
          : view.hostNew ? "Use switches to " + view.hostCandidate + ": you pick a project there. Your boards and settings on "
            + view.host.gitlabHost + " stay for when you come back. glab must be signed in there."
          : "gitlab.com, or your company's own GitLab. glab must be signed in there: glab auth login --hostname <server>."
      }
      Item { width: 1; height: Style.space(4) }
      // Refresh every: the name and the segments on one line, or the
      // segments under it when the popup is too narrow for both.
      Item {
        id: refreshRow
        width: parent.width
        readonly property bool oneLine: refreshHeading.implicitWidth + Style.space(12) + segPane.implicitWidth <= width
        implicitHeight: oneLine ? segPane.implicitHeight : refreshHeading.implicitHeight + Style.space(6) + segPane.implicitHeight
        Label { id: refreshHeading; y: refreshRow.oneLine ? (segPane.implicitHeight - implicitHeight) / 2 : 0; text: "Refresh every" }
        // Segmented control on a faint track: the current interval is tinted
        // in the accent, its number in the accent.
        Rectangle {
          id: segPane
          objectName: "refreshPane"
          x: refreshRow.oneLine ? refreshRow.width - width : 0
          y: refreshRow.oneLine ? 0 : refreshHeading.implicitHeight + Style.space(6)
          implicitWidth: segments.implicitWidth + Style.space(4)
          implicitHeight: segments.implicitHeight + Style.space(4)
          radius: Style.space(8)
          color: view.pane
          border.width: 0
          // One Tab stop: Left / Right pick the interval, as a click does.
          readonly property var choices: [30, 60, 120, 300, 900]
          function kbMove(dx) {
            var i = Math.max(0, choices.indexOf(view.host.refreshIntervalSec))
            view.host.setRefreshInterval(choices[Math.max(0, Math.min(choices.length - 1, i + dx))])
          }
          function kbActivate() { kbMove(1) }
          FocusRing { host: view.host; radius: Style.space(9) }
          Accessible.role: Accessible.PageTabList
          Accessible.name: "Refresh every"

          Row {
            id: segments
            anchors.centerIn: parent
            spacing: Style.space(2)
            Repeater {
              model: segPane.choices
              delegate: Rectangle {
                id: segment
                required property int modelData
                readonly property int seconds: modelData
                readonly property bool current: view.host.refreshIntervalSec === modelData
                implicitWidth: segText.implicitWidth + Style.space(16)
                implicitHeight: segText.implicitHeight + Style.space(8)
                radius: Style.space(6)
                color: current ? Qt.rgba(view.host.accent.r, view.host.accent.g, view.host.accent.b, 0.18) : segMouse.containsMouse ? Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.06) : "transparent"
                Behavior on color { ColorAnimation { duration: 100 } }
                BoardText {
                  id: segText
                  anchors.centerIn: parent
                  text: segment.modelData < 60 ? segment.modelData + "s" : (segment.modelData / 60) + " min"
                  color: segment.current ? view.host.accent : segMouse.containsMouse ? view.host.foreground : view.host.dim
                  font { pixelSize: Style.font.bodySmall; bold: segment.current }
                }
                MouseArea {
                  id: segMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: view.host.setRefreshInterval(segment.modelData)
                }
              }
            }
          }
        }
      }
      // The adaptive pace (Logic.adaptiveInterval), so the tip on "Updated"
      // saying more than the setting is no surprise.
      Help { text: "Slows down, up to 4x, while the board stays quiet; any change brings it back." }
      Item { width: 1; height: Style.space(2) }
      // Open links in: a browser tab or an app window (Board.linkMode), the
      // same segments as Refresh every, on one line or the segments under it.
      Item {
        id: linkRow
        objectName: "linkRow"
        width: parent.width
        readonly property bool oneLine: linkHeading.implicitWidth + Style.space(12) + linkPane.implicitWidth <= width
        implicitHeight: oneLine ? linkPane.implicitHeight : linkHeading.implicitHeight + Style.space(6) + linkPane.implicitHeight
        Label { id: linkHeading; y: linkRow.oneLine ? (linkPane.implicitHeight - implicitHeight) / 2 : 0; text: "Open links in" }
        Rectangle {
          id: linkPane
          objectName: "linkPane"
          x: linkRow.oneLine ? linkRow.width - width : 0
          y: linkRow.oneLine ? 0 : linkHeading.implicitHeight + Style.space(6)
          implicitWidth: linkSegs.implicitWidth + Style.space(4)
          implicitHeight: linkSegs.implicitHeight + Style.space(4)
          radius: Style.space(8)
          color: view.pane
          border.width: 0
          // One Tab stop: Left / Right (or Enter) switch browser tab and app window.
          function kbMove(dx) { view.host.setLinkMode(dx < 0 ? "browser" : "app") }
          function kbActivate() { view.host.setLinkMode(view.host.linkMode === "app" ? "browser" : "app") }
          FocusRing { host: view.host; radius: Style.space(9) }
          Accessible.role: Accessible.PageTabList
          Accessible.name: "Open links in"
          Row {
            id: linkSegs
            anchors.centerIn: parent
            spacing: Style.space(2)
            Repeater {
              model: [{ mode: "browser", label: "Browser tab" }, { mode: "app", label: "App window" }]
              delegate: Rectangle {
                id: linkSeg
                objectName: "linkSegment"
                required property var modelData
                readonly property bool current: view.host.linkMode === modelData.mode
                implicitWidth: linkText.implicitWidth + Style.space(16)
                implicitHeight: linkText.implicitHeight + Style.space(8)
                radius: Style.space(6)
                color: current ? Qt.rgba(view.host.accent.r, view.host.accent.g, view.host.accent.b, 0.18) : linkMouse.containsMouse ? Qt.rgba(view.fg.r, view.fg.g, view.fg.b, 0.06) : "transparent"
                Behavior on color { ColorAnimation { duration: 100 } }
                BoardText {
                  id: linkText
                  anchors.centerIn: parent
                  text: linkSeg.modelData.label
                  color: linkSeg.current ? view.host.accent : linkMouse.containsMouse ? view.host.foreground : view.host.dim
                  font { pixelSize: Style.font.bodySmall; bold: linkSeg.current }
                }
                MouseArea {
                  id: linkMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                  onClicked: view.host.setLinkMode(linkSeg.modelData.mode)
                }
              }
            }
          }
        }
      }
      Help { objectName: "linkNote"; text: "Board issues still open inside GitLabby. Merge requests, to-dos, and an issue's Open action leave the plugin. They open in a browser tab, or in an app window with no tabs (needs a Chromium-based browser)." }
      Item { width: 1; height: Style.space(2) }
      // The bar icon's dot after an alert (Board.iconLit), unless kept unlit.
      Item {
        id: unlitRow
        objectName: "unlitRow"
        width: parent.width; implicitHeight: Style.space(22)
        Row {
          id: unlitLine
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(8)
          CheckBox { objectName: "unlitCheck"; anchors.verticalCenter: parent.verticalCenter; on: view.host.iconUnlit; hot: unlitMouse.containsMouse }
          Label { anchors.verticalCenter: parent.verticalCenter; text: "Keep the bar icon unlit" }
        }
        MouseArea {
          id: unlitMouse
          width: unlitLine.width + Style.space(8); height: parent.height
          hoverEnabled: true; cursorShape: Qt.PointingHandCursor
          onClicked: view.host.setIconUnlit(!view.host.iconUnlit)
          function kbActivate() { view.host.setIconUnlit(!view.host.iconUnlit) }
          FocusRing { host: view.host; radius: Style.space(4) }
          Accessible.role: Accessible.CheckBox
          Accessible.name: "Keep the bar icon unlit"
          Accessible.checked: view.host.iconUnlit
          Accessible.onToggleAction: kbActivate()
        }
      }
      Help { objectName: "unlitNote"; text: "Otherwise a small dot on it after an alert, until you open the board." }
      // Avatar pictures (Board.showAvatars); off, initials instead.
      Item {
        id: avatarsRow
        objectName: "avatarsRow"
        width: parent.width; implicitHeight: Style.space(22)
        Row {
          id: avatarsLine
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(8)
          CheckBox { objectName: "avatarsCheck"; anchors.verticalCenter: parent.verticalCenter; on: view.host.showAvatars; hot: avatarsMouse.containsMouse }
          Label { anchors.verticalCenter: parent.verticalCenter; text: "Show avatars" }
        }
        MouseArea {
          id: avatarsMouse
          width: avatarsLine.width + Style.space(8); height: parent.height
          hoverEnabled: true; cursorShape: Qt.PointingHandCursor
          onClicked: view.host.setShowAvatars(!view.host.showAvatars)
          function kbActivate() { view.host.setShowAvatars(!view.host.showAvatars) }
          FocusRing { host: view.host; radius: Style.space(4) }
          Accessible.role: Accessible.CheckBox
          Accessible.name: "Show avatars"
          Accessible.checked: view.host.showAvatars
          Accessible.onToggleAction: kbActivate()
        }
      }
      Help { objectName: "avatarsNote"; text: "Pictures come from sites like Gravatar, which can see your IP. Off: initials instead." }
      Item { width: 1; height: Style.space(2) }
      Label { text: "Start collapsed" }
      Help { text: "New boards fold these. Your per-board choice wins." }
      // The same check boxes as the busy columns, wrapping, in columns of a
      // quarter of the row so they line up.
      Flow {
        width: parent.width
        spacing: Style.space(6)
        Repeater {
          model: view.host.availableColumns
          delegate: Item {
            id: chk
            required property var modelData
            readonly property bool on: view.host.isDefaultCollapsed(modelData.name)
            readonly property bool clickable: true
            implicitWidth: chkRow.implicitWidth + Style.space(10); implicitHeight: Style.space(22)
            width: Math.max(implicitWidth, Math.floor((view.width - Style.space(8) - 3 * Style.space(6)) / 4))
            Row {
              id: chkRow
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(6)
              CheckBox { anchors.verticalCenter: parent.verticalCenter; on: chk.on; hot: chkMouse.containsMouse }
              Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: Style.space(6); height: width; radius: width / 2
                color: view.host.columnAccent(chk.modelData)
              }
              BoardText { anchors.verticalCenter: parent.verticalCenter; text: chk.modelData.name; color: chk.on ? view.host.foreground : view.host.dim; font.pixelSize: Style.font.bodySmall }
            }
            MouseArea {
              id: chkMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: kbActivate()
              function kbActivate() { view.host.toggleDefaultCollapsed(chk.modelData.name) }
              FocusRing { host: view.host; radius: Style.space(4) }
              Accessible.role: Accessible.CheckBox
              Accessible.name: "Start collapsed: " + chk.modelData.name
              Accessible.checked: chk.on
              Accessible.onToggleAction: kbActivate()
            }
          }
        }
      }

      Item { width: 1; height: Style.space(6) }
      Rule {}
      Item { width: 1; height: Style.space(2) }
      BotsSection {
        id: botsSection
        host: view.host
        readonly property bool mine: view.labelsFor === view.host.projectKey
        labels: mine ? view.allLabels : []
        fetchedStatus: mine ? view.fetchedStatus : []
        labelsState: mine ? view.labelsState : ""
        labelsError: view.labelsError
        onWantLabels: view.loadLabels()
      }

      Item { width: 1; height: Style.space(6); visible: view.host.project !== "" }
      Rule { visible: view.host.project !== "" }
      Item { width: 1; height: Style.space(2); visible: view.host.project !== "" }
      Heading { visible: view.host.project !== ""; text: "Alerts" }
      Help {
        visible: view.host.project !== ""
        text: "Desktop notifications for " + view.host.project + ". While a card or bot one is on, the board refreshes in the background."
      }
      Flow {
        id: alertRow
        visible: view.host.project !== ""
        width: parent.width
        spacing: Style.space(6)
        Repeater {
          model: [{ kind: "review", label: "A card enters review" }, { kind: "idle", label: "A bot stops working" }, { kind: "pipeline", label: "A pipeline on my MR finishes" }]
          delegate: Item {
            id: alertCheck
            required property var modelData
            readonly property bool on: view.host.alerts[modelData.kind] === true
            readonly property bool clickable: true
            implicitWidth: alertCheckRow.implicitWidth + Style.space(10); implicitHeight: Style.space(22)
            Row {
              id: alertCheckRow
              anchors.verticalCenter: parent.verticalCenter
              spacing: Style.space(6)
              CheckBox { anchors.verticalCenter: parent.verticalCenter; on: alertCheck.on; hot: alertMouse.containsMouse }
              BoardText { anchors.verticalCenter: parent.verticalCenter; text: alertCheck.modelData.label; color: alertCheck.on ? view.host.foreground : view.host.dim; font.pixelSize: Style.font.bodySmall }
            }
            MouseArea {
              id: alertMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: kbActivate()
              function kbActivate() { view.host.setAlert(alertCheck.modelData.kind, !alertCheck.on) }
              FocusRing { host: view.host; radius: Style.space(4) }
              Accessible.role: Accessible.CheckBox
              Accessible.name: alertCheck.modelData.label
              Accessible.checked: alertCheck.on
              Accessible.onToggleAction: kbActivate()
            }
          }
        }
      }

      // The pipeline alert (v0.1.76): what it costs, under the boxes.
      Help {
        objectName: "pipeNote"
        visible: view.host.project !== ""
        text: "Your open MRs in this project: one small read per refresh, only while this is on."
      }
      // While an alert is on (v0.1.111): how often it looks, and the last alert.
      Help {
        objectName: "alertStatus"
        visible: view.host.project !== "" && (view.host.alerts.review === true || view.host.alerts.idle === true || view.host.alerts.pipeline === true)
        text: Logic.alertStatusText(Logic.durationText(view.host.refreshIntervalSec), view.host.lastAlert, view.host.lastAlertTime)
      }

      Item { width: 1; height: Style.space(6) }
      Rule {}
      Item { width: 1; height: Style.space(2) }
      Heading { text: "Account" }
      // One row, no frame: who is signed in on the left, Sign out as a quiet
      // text action on the right (32 high, padded, a faint fill on hover).
      // Sign out asks first: the question and what it deletes on the left,
      // Yes / Cancel under them on the right.
      Item {
        id: accountRow
        width: parent.width
        implicitHeight: view.confirming && !view.host.signingOut
          ? accountText.implicitHeight + cacheNote.implicitHeight + Style.space(8) + confirmRow.implicitHeight
          : Math.max(accountText.implicitHeight, Style.space(32))
        BoardText {
          id: accountText
          y: view.confirming && !view.host.signingOut ? 0 : (parent.height - implicitHeight) / 2
          width: parent.width - (signOutLink.visible ? signOutLink.implicitWidth + Style.space(12) : 0)
          wrapMode: Text.Wrap
          color: view.host.accountError !== "" && !view.confirming ? view.host.urgent : view.confirming ? view.host.foreground : view.host.dim
          text: view.host.signingOut ? "Signing out…"
            : view.confirming ? "Sign out of glab on " + view.host.gitlabHost + "? This also signs glab out in your terminal and scripts on this computer."
            : view.host.accountError !== "" ? view.host.accountError
            : view.host.account !== "" ? "Signed in as " + view.host.account + " on " + view.host.gitlabHost : "Checking your GitLab account…"
        }
        BoardText {
          id: cacheNote
          objectName: "signOutCache"
          anchors { top: accountText.bottom; left: parent.left; right: parent.right }
          visible: view.confirming  // Yes drops the question before signing out
          wrapMode: Text.Wrap
          color: view.host.foreground
          text: "This also deletes this server's saved board cache on this computer."
        }
        BoardText {
          id: signOutLink
          anchors { right: parent.right; verticalCenter: parent.verticalCenter }
          visible: !view.host.signingOut && !view.confirming && (view.host.account !== "" || view.host.accountError !== "")
          text: "Sign out"
          color: view.host.accent
          font.pixelSize: Style.font.bodySmall
          height: Style.space(32)
          leftPadding: Style.space(12); rightPadding: Style.space(12)
          verticalAlignment: Text.AlignVCenter
          function kbActivate() { view.confirming = true }
          Rectangle {
            objectName: "signOutHover"
            z: -1
            anchors.fill: parent
            radius: Style.space(6)
            color: signOutMouse.containsMouse ? Qt.rgba(view.host.foreground.r, view.host.foreground.g, view.host.foreground.b, 0.06) : "transparent"
          }
          MouseArea { id: signOutMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: signOutLink.kbActivate() }
          FocusRing { host: view.host }
          Accessible.role: Accessible.Button
          Accessible.name: "Sign out"
        }
        Row {
          id: confirmRow
          anchors { right: parent.right; bottom: parent.bottom }
          spacing: Style.space(8)
          visible: view.confirming && !view.host.signingOut
          ActionButton {
            id: yesButton
            host: view.host; small: true; danger: true; label: "Yes, sign out"
            onClicked: { view.confirming = false; view.host.signOut() }
            PanelToolTip {
              y: parent.height + Style.space(4); visible: yesButton.hovered
              text: "Signs out glab in your terminal too\nand deletes the saved boards."
              onAboutToShow: x = parent.width - implicitWidth  // keep it inside the popup
            }
          }
          ActionButton {
            host: view.host; small: true; label: "Cancel"
            onClicked: view.confirming = false
          }
        }
      }
      // What glab's token may do: Logic.accessLine over the scopes board-fetch
      // access already read for this project (the token's record, never the
      // token). Nothing until that answer; "can't be read" for a browser sign-in.
      BoardText {
        objectName: "accessLine"
        width: parent.width
        wrapMode: Text.Wrap
        visible: text !== "" && view.host.account !== "" && !view.confirming && !view.host.signingOut
        color: view.host.dim
        font.pixelSize: Style.font.bodySmall
        text: Logic.accessLine(view.host.accessEntry)
      }
    }
  }
  // More below: the bottom edge fades (ScrollHint.qml).
  ScrollHint { flick: flick; host: view.host }
}
