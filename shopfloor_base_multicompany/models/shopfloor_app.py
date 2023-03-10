# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    company_ids = fields.Many2many(
        comodel_name="res.company",
        column1="app_id",
        column2="company_id",
        string="Allowed companies",
        help="Limit access to this app only to selected companies' users. "
        "If a non authorized user calls an endpoint of this app, an exception will be raised.",
    )
    must_validate_company = fields.Boolean(
        compute="_compute_must_validate_company", store=True
    )

    @api.depends("company_ids")
    def _compute_must_validate_company(self):
        for rec in self:
            rec.must_validate_company = bool(rec.company_ids)
