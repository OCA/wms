
export class Registry {

    constructor () {
        this._data = {};
    }

    get (key) {
        return this._data[key];
    }

    add (key, item) {
        this._data[key] = item;
    }

}
