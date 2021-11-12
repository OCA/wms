/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_fr = {
    screen: {
        login: {
            title: "Connexion",
            api_key_placeholder: "Entrez votre API key",
            api_key_label: "API key",
            action: {
                login: "Connexion",
            },
            error: {
                api_key_invalid: "API Key non valide",
            },
        },
        home: {
            title: "Home",
            main_title: "Barcode scanner",
            version: "Version:",
            action: {
                nuke_data_and_reload: "Recharger les données et rafraichir la page",
            },
        },
        scan_anything: {
            name: "Scanner",
            title: "Scanner {what}",
        },
        settings: {
            title: "Réglages",
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
                profile_updated: "Profil mis à jour",
            },
            fullscreen: {
                enter: "Plein écran",
                exit: "Sortir du mode plein écran",
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
        cancel: {
            title: "Annuler",
        },
        ok: {
            title: "Ok",
        },
        reset: {
            title: "Reset",
        },
        reload_config: {
            title: "Recharger la configuration et le menu",
        },
    },
    app: {
        profile_not_configured: "Profil non configuré. Choisissez-en un.",
        profile_configure: "Configurer un profil",
        loading: "Chargement...",
        action: {
            logout: "Déconnexion",
        },
        log_entry_link: "Voir le log",
    },
    misc: {
        actions_popup: {
            btn_action: "Action",
        },
    },
    list: {
        no_items: "Pas d'item dans la liste.",
    },
    select: {
        no_items: "Pas d'item à sélectionner.",
    },
    order_lines_by: {
        priority: "Ordonner par priorité",
        location: "Ordonner par emplacement",
    },
};

translation_registry.add("fr-FR", messages_fr);
