/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {BaseRegistry} from "./registry.js";

/**
 * A "process" represents a barcode app process (eg: pick goods for reception).
 *
 * A process registry is responsible for collecting all the processes
 * and ease their registration, lookup and override.
 *
 * The router will use this registry to register processes routes.
 */

class ProcessRegistry extends BaseRegistry {
    constructor() {
        super();
        this._make_route_path_pattern = "/${ key }/:menu_id/:state?";
        this._profileRequired = true;
    }
}
export var process_registry = new ProcessRegistry();
