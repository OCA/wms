# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()
    profile_id = fields.Many2one(
        "shopfloor.profile", string="Profile", help="Visible on this profile only"
    )
    scenario_id = fields.Many2one(
        comodel_name="shopfloor.scenario",
        required=True,
        ondelete="cascade",
        compute="_compute_scenario_id",
        store=True,
        readonly=False,
        inverse="_inverse_scenario_id",
    )
    # TODO: on next versions we could remove this field and drop the compute on m2o.
    # ATM is kept only to have a smooth transition to the m2o field.
    scenario = fields.Char(string="Legacy scenario field")
    active = fields.Boolean(default=True)

    def _compute_scenario_id(self):
        for rec in self:
            if not rec.scenario_id and rec.scenario:
                rec.with_context(
                    set_by_compute=True
                ).scenario_id = rec.scenario_id.search(
                    [("key", "=", rec.scenario)], limit=1
                )

    def _inverse_scenario_id(self):
        if not self.env.context.get("set_by_compute"):
            for rec in self:
                rec.scenario = rec.scenario_id.key
