/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
export function loadJSON(callback, url) {
    let xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open("GET", url, false); // false -> synchronous call to be sure to  have the result before the registry is used by others JS
    xobj.onreadystatechange = function () {
        if (xobj.readyState == 4 && xobj.status == "200") {
            const json = JSON.parse(xobj.responseText);
            callback(json);
        }
    };
    xobj.send(null);
}

export class TranslationRegistry {
    constructor() {
        this._data = {};
        this._default_lang = "en-US";
    }

    get(path) {
        return _.result(this._data, path);
    }

    add(path, value) {
        _.set(this._data, path, value);
    }

    all() {
        return this._data;
    }

    available_langs() {
        return Object.keys(this._data);
    }

    set_default_lang(lang) {
        if (_.isEmpty(this._data[lang])) {
            throw "Language not available: " + lang;
        }
        this._default_lang = lang;
    }

    get_default_lang() {
        return this._default_lang;
    }

    load(lang, path) {
        loadJSON((messages) => {
            const original_messages = this.get(lang);
            const merged_messages = {...messages, ...original_messages};
            this.add(lang, merged_messages);
        }, path);
    }
}

export var translation_registry = new TranslationRegistry();
