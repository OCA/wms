/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_de = {
    screen: {
        login: {
            title: "Login",
            action: {
                login: "Login",
            },
            error: {
                login_invalid: "Ungültige Anmeldeinformationen",
            },
        },
        home: {
            title: "Startseite",
            main_title: "Startseite",
            version: "Version:",
            action: {
                nuke_data_and_reload:
                    "Erzwingen das erneute Laden von Daten und aktualisieren",
            },
        },
        scan_anything: {
            name: "Gescannt",
            title: "Gescannt {what}",
            scan_placeholder: "Alles scannen",
        },
        settings: {
            title: "Einstellungen",
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
                profile_updated: "Profil aktualisiert",
            },
            fullscreen: {
                enter: "Vollbildmodus",
                exit: "Vollbild beenden",
            },
        },
    },
    app: {
        profile_not_configured:
            "Profil noch nicht konfiguriert. Bitte wählen Sie eine aus.",
        profile_configure: "Profil konfigurieren",
        loading: "Wird geladen...",
        action: {
            logout: "Ausloggen",
        },
        nav: {
            scenario: "Szenario:",
            op_types: "Op Typen:",
        },
        log_entry_link: "Logeintrag ansehen / teilen",
        running_env: {
            prod: "Produktion",
            integration: "Integration",
            staging: "Staging",
            test: "Test",
            dev: "Entwicklung",
        },
        report_issue: {
            action_txt: "Benötigen Sie Unterstützung?",
            mail: {
                subject: "Ich benötige Unterstützung mit der {app_name} app",
                info_warning_msg:
                    "BITTE ÄNDERN SIE DIE FOLGENDE INFORMATION/NACHRICHT NICHT",
            },
        },
    },
    language: {
        name: {
            English: "Englisch",
            French: "Französisch",
            German: "Deutsch",
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
        reset: {
            title: "Zurücksetzen",
        },
        cancel: {
            title: "Absagen",
        },
        reload_config: {
            title: "Konfiguration und Menü neu laden",
        },
    },
};

translation_registry.add("de-DE", messages_de);
