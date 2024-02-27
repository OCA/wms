/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/* eslint-disable strict */
import {config_registry} from "/shopfloor_mobile_base/static/wms/src/services/config_registry.js";

config_registry.add("report_issue_config", {
    default: _.result(shopfloor_app_info, "report_issue_config", {
        enabled: false,
        mail_to: "",
    }),
});

const REPORT_ISSUE_TEMPLATES = {
    inline: Vue.compile(`
        <a class="report-issue-action text-decoration-none"
           :href="report_issue_mail_to_href">
           <v-icon v-text="icon"></v-icon> <span v-text="$t('app.report_issue.action_txt')" />
        </a>
    `),
    vertical: Vue.compile(`
        <v-list-item v-if="report_issue_enabled"
            class="report-issue-action"
            data-ref="report-issue-action"
            :href="report_issue_mail_to_href"
            >
            <v-list-item-avatar>
                <v-avatar :size="icon_size" color="info">
                    <v-icon dark v-text="icon"></v-icon>
                </v-avatar>
            </v-list-item-avatar>
            <v-list-item-content>
                <span v-text="$t('app.report_issue.action_txt')" />
            </v-list-item-content>
        </v-list-item>
  `),
};

Vue.component("report-issue-action", {
    props: {
        display_mode: {
            type: String,
            default: "vertical",
        },
        icon: {
            type: String,
            default: "mdi-help-circle-outline",
        },
        icon_size: {
            type: Number,
            default: 36,
        },
    },
    computed: {
        report_issue_conf: function () {
            return this.$root.report_issue_config;
        },
        report_issue_enabled: function () {
            const enabled = this.report_issue_conf.enabled;
            const configured = _.result(this.report_issue_conf, "mail_to", "").trim()
                .length;
            return enabled && configured;
        },
        report_issue_mail_to_href: function () {
            if (!this.report_issue_enabled) {
                return "";
            }
            const email = this.report_issue_conf.mail_to;
            const subject = this.$t("app.report_issue.mail.subject", {
                app_name: this.$root.app_info.name,
            });
            const body = encodeURIComponent(this._get_report_issue_body());
            return `mailto:${email}?subject=${subject}&body=${body}`;
        },
    },
    methods: {
        _get_report_issue_body: function () {
            const bits = [
                "",
                "",
                "-- " + this.$t("app.report_issue.mail.info_warning_msg") + " --",
                "",
                "APP: " + this.$root.app_info.version,
                "UID: " + this.$root.user.id,
                "UA: " + window.navigator.userAgent,
            ];
            return bits.join("\n");
        },
    },
    render(createElement) {
        const tmpl = REPORT_ISSUE_TEMPLATES[this.display_mode];
        return tmpl.render.call(this, createElement);
    },
});
