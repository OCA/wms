/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_de = {
    screen: {
        home: {
            title: "Barcode scanner",
        },
        scan_anything: {
            name: "Gescannt",
            title: "Gescannt {what}",
        },
        settings: {
            home: {
                name: "Einstellungen",
                title: "Einstellungen",
            },
            language: {
                name: "Sprache",
                title: "Sprache auswählen",
            },
            profile: {
                name: "Profil",
                title: "Wähle Profil",
            },
            fullscreen: {
                enter: "Go fullscreen",
                exit: "Exit fullscreen",
            },
        },
    },
    language: {
        name: {
            English: "Englisch",
            French: "Französisch",
            German: "Deutsche",
        },
    },
    btn: {
        back: {
            title: "Zurück",
        },
        confirm: {
            title: "Bestätigen",
        },
        ok: {
            title: "Ok",
        },
    },
};

translation_registry.add("de-DE", messages_de);
