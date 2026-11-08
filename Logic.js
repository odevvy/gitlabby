.import "logic/core.js" as Core
.import "logic/labels.js" as Labels
.import "logic/bots.js" as Bots
.import "logic/markdown.js" as Markdown
.import "logic/board.js" as BoardLogic
.import "logic/alerts.js" as Alerts
.import "logic/mrs.js" as Mrs
.import "logic/bulk.js" as Bulk
.import "logic/access.js" as Access
.import "logic/favorites.js" as Favorites

// Pure logic for the board and the issue view, split by concern into logic/*.js.
// No Qt there, so tests/logic.test.js runs it under node (through
// logic/index.js); QML imports this file, which hands each module the others
// it needs (use()) and re-exports every name, so QML still calls Logic.<name>.
// Same pattern as Omarchy's panels/clock/Model.js.
Labels.use({ Core: Core })
Bots.use({ Core: Core })
Markdown.use({ Core: Core })
Alerts.use({ Core: Core, Bots: Bots })
Mrs.use({ Core: Core })
Bulk.use({ BoardLogic: BoardLogic, Core: Core })
Access.use({ Core: Core })

// core.js
var plainJson = Core.plainJson
var lowerList = Core.lowerList
var has = Core.has
var toggled = Core.toggled
var countLabel = Core.countLabel
var escaped = Core.escaped
var plain = Core.plain
var copied = Core.copied
var age = Core.age
var savedNote = Core.savedNote
var httpsUrl = Core.httpsUrl
var gitlabUrl = Core.gitlabUrl
var oneLine = Core.oneLine
var serverHost = Core.serverHost
var signInCommand = Core.signInCommand
var serverKey = Core.serverKey
// labels.js
var labelStyle = Labels.labelStyle
var workflowLabels = Labels.workflowLabels
var statusLabels = Labels.statusLabels
var addableLabels = Labels.addableLabels
var statusOn = Labels.statusOn
var withColors = Labels.withColors
var luminance = Labels.luminance
var dotColor = Labels.dotColor
// bots.js
var botsConfig = Bots.botsConfig
var botStates = Bots.botStates
var inColumn = Bots.inColumn
var botsEntry = Bots.botsEntry
var botUsable = Bots.botUsable
var botNameTaken = Bots.botNameTaken
var withBot = Bots.withBot
var withoutBot = Bots.withoutBot
var withBusy = Bots.withBusy
// markdown.js
var byline = Markdown.byline
var people = Markdown.people
var linkUrl = Markdown.linkUrl
var lineLimit = Markdown.lineLimit
var inline = Markdown.inline
var quickAction = Markdown.quickAction
var moveNote = Markdown.moveNote
var descriptionLimit = Markdown.descriptionLimit
var clipped = Markdown.clipped
var markdown = Markdown.markdown
// board.js
var pipelineMarks = BoardLogic.pipelineMarks
var pipelineMark = BoardLogic.pipelineMark
var columnKey = BoardLogic.columnKey
var listSpec = BoardLogic.listSpec
var movedColumns = BoardLogic.movedColumns
var cursorMove = BoardLogic.cursorMove
var cursorFix = BoardLogic.cursorFix
var cursorAt = BoardLogic.cursorAt
var keyGroups = BoardLogic.keyGroups
var openLabel = BoardLogic.openLabel
var keyParts = BoardLogic.keyParts
var boardSig = BoardLogic.boardSig
var boardActive = BoardLogic.boardActive
var nextPace = BoardLogic.nextPace
var paceFloorSec = BoardLogic.paceFloorSec
var openMaxAgeMs = BoardLogic.openMaxAgeMs
var adaptiveInterval = BoardLogic.adaptiveInterval
var durationText = BoardLogic.durationText
var cadenceText = BoardLogic.cadenceText
var keyOps = BoardLogic.keyOps
// alerts.js
var alertsFor = Alerts.alertsFor
var withAlert = Alerts.withAlert
var reviewRows = Alerts.reviewRows
var boardUrl = Alerts.boardUrl
var alertEvents = Alerts.alertEvents
var notifyArgv = Alerts.notifyArgv
var pipesArgs = Alerts.pipesArgs
var pipesAnswer = Alerts.pipesAnswer
var mrListUrl = Alerts.mrListUrl
var pipelineEvents = Alerts.pipelineEvents
var lastAlertText = Alerts.lastAlertText
var alertStatusText = Alerts.alertStatusText
// mrs.js
var mrsAnswer = Mrs.mrsAnswer
var reviewerStates = Mrs.reviewerStates
var mrPerson = Mrs.mrPerson
var mrRows = Mrs.mrRows
var mrStatuses = Mrs.mrStatuses
var toneColors = Mrs.toneColors
var mrStatus = Mrs.mrStatus
var listCaps = Mrs.listCaps
var viewAllUrl = Mrs.viewAllUrl
var todosAnswer = Mrs.todosAnswer
var todoActions = Mrs.todoActions
var todoAction = Mrs.todoAction
var todoRef = Mrs.todoRef
var todoSubline = Mrs.todoSubline
var issueColumn = Mrs.issueColumn
var issueSubline = Mrs.issueSubline
var todoBadge = Mrs.todoBadge
var todosArgs = Mrs.todosArgs
var reviewerMarks = Mrs.reviewerMarks
var reviewerMark = Mrs.reviewerMark
var mrSubline = Mrs.mrSubline
var mrBadge = Mrs.mrBadge
var mrsArgs = Mrs.mrsArgs
// bulk.js
var bulkCap = Bulk.bulkCap
var pickKey = Bulk.pickKey
var togglePick = Bulk.togglePick
var pickedCards = Bulk.pickedCards
var livePicks = Bulk.livePicks
var movable = Bulk.movable
var closeOrReopen = Bulk.closeOrReopen
var bulkPlan = Bulk.bulkPlan
var cardsText = Bulk.cardsText
var iidsText = Bulk.iidsText
var bulkQuestion = Bulk.bulkQuestion
var bulkButton = Bulk.bulkButton
var bulkNote = Bulk.bulkNote
var bulkLines = Bulk.bulkLines
var bulkOutcome = Bulk.bulkOutcome
var bulkSummary = Bulk.bulkSummary
// access.js
var plannerLevel = Access.plannerLevel
var accessEntry = Access.accessEntry
var writeRefusal = Access.writeRefusal
var refusedEntry = Access.refusedEntry
var accessNote = Access.accessNote
var accessHint = Access.accessHint
var accessLine = Access.accessLine
var patUrl = Access.patUrl
// favorites.js
var favoriteKey = Favorites.favoriteKey
var boardLabel = Favorites.boardLabel
var jumpLabel = Favorites.jumpLabel
var hostFavorites = Favorites.hostFavorites
var jumpBoards = Favorites.jumpBoards
var isFavorite = Favorites.isFavorite
var toggledFavorite = Favorites.toggledFavorite
