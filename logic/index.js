// Every module of Logic.js for node (tests/logic.test.js): the same names
// Logic.js re-exports to QML.
module.exports = Object.assign({},
  require("./core.js"),
  require("./labels.js"),
  require("./bots.js"),
  require("./markdown.js"),
  require("./board.js"),
  require("./alerts.js"),
  require("./mrs.js"),
  require("./bulk.js"),
  require("./access.js"),
  require("./favorites.js")
)
