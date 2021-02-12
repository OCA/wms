/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

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
}

export var translation_registry = new TranslationRegistry();
