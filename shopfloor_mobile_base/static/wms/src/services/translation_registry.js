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

    /**
     * The load method adds collections of translations to the registry.
     * It expects the corresponding language as well as the path to
     * the file with the translations.
     * It adds them on top of the existing ones.
     *
     * If the translations are in dotted_path format ("any.translation.key": "translation"),
     * each entry needs to be added to original_messages individually
     * in order to avoid unwanted overrides to the original translations.
     *
     * @param {string} lang
     * @param {string} path
     * @param {bool} dotted_path
     */
    load(lang, path, dotted_path = false) {
        loadJSON((messages) => {
            const original_messages = this.get(lang);
            let merged_messages;
            if (dotted_path) {
                Object.entries(messages).forEach((entry) => {
                    _.set(original_messages, entry[0], entry[1]);
                });
                merged_messages = original_messages;
            } else {
                merged_messages = {...original_messages, ...messages};
            }
            this.add(lang, merged_messages);
        }, path);
    }
}

export var translation_registry = new TranslationRegistry();
