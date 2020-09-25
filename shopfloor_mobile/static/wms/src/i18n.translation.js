/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "./services/translation_registry.js";

const messages_en = {
    screen: {
        home: {
            title: "Barcode scanner",
        },
        scan_anything: {
            title: "Scan {what}",
        },
        settings: {
            home: {
                name: "Settings",
                title: "Settings",
            },
            language: {
                name: "Language",
                title: "Select language",
            },
            profile: {
                name: "Profile",
                title: "Select profile",
            },
            fullscreen: {
                enter: "Go fullscreen",
                exit: "Exit fullscreen",
            },
        },
    },
    language: {
        name: {
            English: "English",
            French: "French",
            German: "German",
        },
    },
    btn: {
        back: {
            title: "Back",
        },
        confirm: {
            title: "Confirm",
        },
        ok: {
            title: "Ok",
        },
    },
    picking_type: {
        lines_count: "{lines_count} lines (over {picking_count} operations).",
        priority_lines_count:
            "{priority_lines_count} priority lines (over {priority_picking_count} operations).",
    },
    order_lines_by: {
        priority: "Order by priority",
        location: "Order by location",
    },
};
const messages_fr = {
    screen: {
        home: {
            title: "Barcode scanner",
        },
        scan_anything: {
            name: "Scanner",
            title: "Scanner {what}",
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

translation_registry.add("en-US", messages_en);
translation_registry.add("fr-FR", messages_fr);
translation_registry.add("de-DE", messages_de);
