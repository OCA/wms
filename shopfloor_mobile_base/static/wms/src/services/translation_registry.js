/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
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
        this._enabled = [];
    }

    add(path, value) {
        _.set(this._data, path, value);
    }

    get(path) {
        return _.result(this._data, path);
    }

    messages() {
        return this._data;
    }

    ensure_lang(lang, log_missing = false) {
        if (!_.isEmpty(this._data[lang])) {
            return lang;
        }
        // find most suitable lang (eg: fr-FR for fr-CH)
        const fallback_lang = this.available_langs().find((x) => {
            return x.startsWith(lang.slice(0, 2));
        });
        if (log_missing) {
            if (fallback_lang) {
                console.log("Lang fallback", {lang, fallback_lang});
            } else {
                console.log("Lang fallback on default", {
                    lang,
                    default: this._default_lang,
                });
            }
        }
        return fallback_lang || this._default_lang;
    }

    available_langs() {
        return Object.keys(this._data);
    }

    set_default_lang(lang) {
        this._default_lang = this.ensure_lang(lang, true);
    }

    default_lang() {
        return this._default_lang;
    }

    set_enabled_langs(langs) {
        let enabled = [];
        langs.forEach((lang) => {
            enabled.push(this.ensure_lang(lang, true));
        });
        this._enabled = enabled;
    }

    enabled_langs() {
        return this._enabled || this.available_langs();
    }

    available_langs_display($root) {
        return [
            {
                id: "en-US",
                name: $root.$t("language.name.English"),
            },
            {
                id: "fr-FR",
                name: $root.$t("language.name.French"),
            },
            {
                id: "de-DE",
                name: $root.$t("language.name.German"),
            },
        ].filter((x) => {
            return this.enabled_langs().includes(x.id);
        });
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
    /**
     * Initilize VueI18n configuration
     * @returns {VueI18n} Object
     */
    init_i18n() {
        return new VueI18n({
            locale: this.default_lang(), // Set locale
            availableLocales: this.available_langs(),
            messages: this.messages(),
        });
    }
}

export var translation_registry = new TranslationRegistry();
