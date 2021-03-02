/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
import {utils_registry} from "./services/utils_registry.js";

export class DisplayUtils {
    constructor() {}
    format_date_display(date_string, options = {}) {
        _.defaults(options, {
            locale: navigator ? navigator.language : "en-US",
            format: {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "numeric",
                minute: "2-digit",
            },
        });
        return new Date(Date.parse(date_string)).toLocaleString(
            options.locale,
            options.format
        );
    }
    render_field_date(record, field) {
        return this.format_date_display(_.result(record, field.path));
    }
}

utils_registry.add("display", new DisplayUtils());
