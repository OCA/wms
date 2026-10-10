/**
 * Copyright 2025 ACSONE SA/NV
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/wms/src/scenario/mixins.js";

const methods = ScenarioBaseMixin.methods;

methods._print_label_allowed = function () {
    return this.state.data && this.state.data.allow_print_label === true;
};
