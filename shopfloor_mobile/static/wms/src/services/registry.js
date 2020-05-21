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

export class ColorRegistry {
    constructor(theme, _default = "default") {
        this.themes = [];
        this.colors = {};
        this.default_theme = _default;
    }

    add_theme(colors, theme) {
        if (_.isUndefined(theme)) theme = this.default_theme;
        if (!this.themes.includes(theme)) {
            this.themes.push(theme);
        }
        this.colors[theme] = colors;
    }

    color_for(key, theme) {
        if (_.isUndefined(theme)) theme = this.default_theme;
        if (!this.themes.includes(theme)) {
            console.log("Theme", theme, "not registeed.");
            return null;
        }
        return this.colors[theme][key];
    }
}
