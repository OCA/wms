/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "./services/translation_registry.js";

const default_lang = translation_registry.get_default_lang();
const available_langs = translation_registry.available_langs();
const messages = translation_registry.all();

export const i18n = new VueI18n({
    locale: default_lang, // set locale
    availableLocales: available_langs,
    messages, // set locale messages
});

/*
TODO: decide how to handle translations in the long term.
App-only terms can be translated in json files.
Odoo-only terms can be loaded from Odoo.
*/
