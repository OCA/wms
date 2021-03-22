/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {BaseRegistry} from "./registry.js";

/**
 * TODO
 */

class PageRegistry extends BaseRegistry {
    constructor() {
        super(arguments);
    }

    add(key, component, route, metadata, override = false) {
        const rec = super.add(key, component, route, metadata, override);
        if (!_.result(rec, "metadata.tag")) {
            throw "`tag` is required for pages!";
        }
        _.defaults(rec.metadata, {
            display_name: function(instance, rec) {
                return rec.key;
            },
        });
        return rec;
    }
    /**
     * Retrieve all pages matching given tag.
     *
     * @param {*} tag: metadata tag to filter with
     */
    by_tag(tag) {
        return _.filter(this._data, function(x) {
            return x.metadata.tag == tag;
        });
    }
}
export var page_registry = new PageRegistry();
