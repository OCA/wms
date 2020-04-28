export class Registry {
    constructor() {
        this._data = {};
    }

    get(key) {
        return this._data[key];
    }

    add(key, item) {
        this._data[key] = item;
    }

    all() {
        return this._data;
    }

    make_route(code) {
        return _.template("/${ code }/:menu_id/:state?")({code: code});
    }
}
