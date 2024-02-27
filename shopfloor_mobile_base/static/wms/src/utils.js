/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */
import {utils_registry} from "./services/utils_registry.js";

export class DisplayUtils {
    _ensure_UTC_datetime(date_string) {
        if (!date_string.endsWith("Z")) {
            const _value = date_string.replace(" ", "T") + "Z";
            if (!_.isNaN(Date.parse(_value))) {
                return _value;
            }
        }
        return date_string;
    }
    format_date_display(date_string, options = {}, utc = true) {
        if (utc) {
            date_string = this._ensure_UTC_datetime(date_string);
        }
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
