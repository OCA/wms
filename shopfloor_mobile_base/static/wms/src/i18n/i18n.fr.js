/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_fr = {
    screen: {
        home: {
            title: "Accueil",
            main_title: "Accueil",
        },
        scan_anything: {
            name: "Scanner",
            title: "Scannez {what}",
        },
        settings: {
            home: {
                name: "Réglages",
                title: "Réglages",
            },
            language: {
                name: "Langue",
                title: "Choisir la langue",
            },
            profile: {
                name: "Profil",
                title: "Choisissez un profil",
            },
            fullscreen: {
                enter: "Go fullscreen",
                exit: "Exit fullscreen",
            },
        },
    },
    language: {
        name: {
            English: "Anglais",
            French: "Français",
            German: "Allemand",
        },
    },
    btn: {
        back: {
            title: "Retour",
        },
        confirm: {
            title: "Confirmer",
        },
        ok: {
            title: "Ok",
        },
    },
};

translation_registry.add("fr-FR", messages_fr);
