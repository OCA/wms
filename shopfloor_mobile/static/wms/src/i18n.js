/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "./services/translation_registry.js";

const messages = translation_registry.all();

export const i18n = new VueI18n({
    locale: "en-US", // set locale
    availableLocales: ["en-US", "fr-FR", "de-DE"],
    messages, // set locale messages
});

/*
TODO: decide how to handle translations in the long term.
App-only terms can be translated in json files.
Odoo-only terms can be loaded from Odoo.
*/
