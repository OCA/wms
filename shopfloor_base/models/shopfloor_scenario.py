# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import json
import logging

from odoo import api, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized
from odoo.addons.http_routing.models.ir_http import slugify

_logger = logging.getLogger(__name__)


class ShopfloorScenario(models.Model):
    _name = "shopfloor.scenario"
    _description = "Shopfloor Scenario"

    name = fields.Char(required=True, translate=True)
    # TODO: make it readonly in UI?
    # Make it a Selection field?
    # Normally this will be used only by dev implementing new scenario.
    key = fields.Char(
        required=True,
        help="Identify scenario univocally. "
        "This value must match a service component's `usage`.",
    )
    options = Serialized(compute="_compute_options", default={})
    options_edit = fields.Text(
        help="Configure options via JSON", inverse="_inverse_options_edit"
    )

    _sql_constraints = [("key", "unique(key)", "Scenario key must be unique")]

    @api.depends("options_edit")
    def _compute_options(self):
        for rec in self:
            rec.options = rec._load_options()

    def _inverse_options_edit(self):
        for rec in self:
            # Make sure options_edit is always readable
            rec.options_edit = json.dumps(rec.options or {}, indent=4, sort_keys=True)

    def _load_options(self):
        return json.loads(self.options_edit or "{}")

    @api.onchange("name")
    def _onchange_name_for_key(self):
        # Keep this specific name for the method to avoid possible overrides
        # of existing `_onchange_name` methods
        if self.name and not self.key:
            self.key = self.name

    @api.onchange("key")
    def _onchange_key(self):
        if self.key:
            # make sure is normalized
            self.key = self._normalize_key(self.key)

    @api.model
    def create(self, vals):
        self._handle_key(vals)
        return super().create(vals)

    def write(self, vals):
        self._handle_key(vals)
        return super().write(vals)

    def _handle_key(self, vals):
        # make sure technical names are always there
        if not vals.get("key") and vals.get("name"):
            vals["key"] = self._normalize_key(vals["name"])

    @staticmethod
    def _normalize_key(name):
        return slugify(name).replace("-", "_")

    def has_option(self, key):
        return self.options.get(key, False)
