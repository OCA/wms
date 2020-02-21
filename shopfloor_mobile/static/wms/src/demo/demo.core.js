/* eslint no-use-before-define: 0 */  // --> OFF

var getRandomInt = function (max) {
    return Math.floor(Math.random() * Math.floor(max)) + 1
}

var batchList = function (count=5) {
    let list = []
    for (let i = 1; i < count + 1; i++) {
        list.push({
            "id": i,
            "name": 'Batch #' + i,
            "picking_count": getRandomInt(3),
            "move_line_count": getRandomInt(15),
        })
    }
    return list
}

window.DEMO_CASES = {} // collection
/* eslint no-use-before-define: 2 */  // --> ON
