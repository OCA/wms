# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    move_need_release_count = fields.Integer(
        string="Moves Need Release", compute="_compute_move_need_release_count"
    )

    @api.depends("stock_move_ids.need_release")
    def _compute_move_need_release_count(self):
        for product in self:
            product.move_need_release_count = len(
                product.stock_move_ids.filtered("need_release")
            )

    def action_open_move_need_release(self):
        self.ensure_one()
        if not self.move_need_release_count:
            return
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [
            ("product_id", "in", self.ids),
            ("need_release", "=", True),
        ]
        action["context"] = {}
        return action
