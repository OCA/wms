/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

import {translation_registry} from "../services/translation_registry.js";

const messages_fr = {
    screen: {
        login: {
            title: "Se connecter",
            action: {
                login: "Se connecter",
            },
            error: {
                login_invalid: "Iformations d'identification invalides",
            },
        },
        home: {
            title: "Accueil",
            main_title: "Accueil",
            version: "Version:",
            action: {
                nuke_data_and_reload: "Forcer rechargement des données et actualiser",
            },
        },
        scan_anything: {
            name: "Scanner",
            title: "Scannez {what}",
            scan_placeholder: "Scannez quelque chose",
        },
        settings: {
            title: "Paramètres",
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
                exit: "Quitter plein écran",
            },
        },
    },
    app: {
        profile_not_configured:
            "Profil pas encore configuré. S'il vous plait sélectionner en un.",
        profile_configure: "Configurer le profil",
        loading: "Chargement en cours...",
        action: {
            logout: "Se déconnecter",
            toggle_devtools: "Activer/désactiver les outils de développement",
        },
        nav: {
            scenario: "Scénario:",
            op_types: "Op types:",
        },
        log_entry_link: "Afficher / partager l'entrée du journal",
        running_env: {
            prod: "Production",
            integration: "Intégration",
            staging: "Staging",
            test: "Test",
            dev: "Développement",
        },
        report_issue: {
            action_txt: "Besoin d'aide?",
            mail: {
                subject: "J'ai besoin d'aide avec l'application {app_name}",
                info_warning_msg:
                    "VEUILLEZ NE PAS MODIFIER LES INFORMATIONS CI-DESSOUS",
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
        start: {
            title: "Démarrer",
        },
        confirm: {
            title: "Confirmer",
        },
        ok: {
            title: "Ok",
        },
        reset: {
            title: "Réinitialiser",
        },
        cancel: {
            title: "Annuler",
        },
        reload_config: {
            title: "Recharger la configuration et le menu",
        },
    },
    misc: {
        btn_get_work: "Obtenir du travail",
        btn_manual_selection: "Sélection manuelle",
        stock_zero_check: {
            confirm_stock_zero: "Rupture de stock",
            confirm_stock_not_zero: "Confirmer le stock",
        },
        actions_popup: {
            btn_action: "Action",
        },
        lines_count: "{priority_lines_count}/{lines_count}",
        lines_count_extended: "{priority_lines_count}/{lines_count} position(s)",
        picking_count: "{priority_picking_count}/{picking_count}",
        picking_count_extended: "{priority_picking_count}/{picking_count} transfert(s)",
    },
    list: {
        no_items: "Aucun élément à lister.",
    },
    select: {
        no_items: "Aucun élément à sélectionner.",
    },
    order_lines_by: {
        priority: "Trier par priorité",
        location: "Trier par emplacement",
    },
};

translation_registry.add("fr-FR", messages_fr);
