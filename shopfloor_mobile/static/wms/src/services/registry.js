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

    make_route(code) {
        return _.template("/${ code }/:menu_id")({code: code});
    }

    make_path(code, menu_id) {
        return _.template("/${ code }/${ menu_id }")({code: code, menu_id: menu_id});
    }
}
