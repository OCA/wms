# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    move_need_release_count = fields.Integer(
        string="Moves Need Release", compute="_compute_move_need_release_count"
    )
    is_ok_expected_delivery_date = fields.Boolean(
        compute="_compute_is_ok_expected_delivery_date"
    )

    @api.depends("picking_ids.move_ids.need_release")
    def _compute_move_need_release_count(self):
        for sale in self:
            sale.move_need_release_count = len(
                sale.picking_ids.move_ids.filtered("need_release")
            )

    @api.depends("expected_date", "order_line.availability_status")
    def _compute_is_ok_expected_delivery_date(self):
        for sale in self:
            if not (sale.commitment_date or sale.expected_date):
                sale.is_ok_expected_delivery_date = False
                continue
            for line in sale.order_line:
                if (
                    not line.display_type
                    and not line.is_delivery
                    and not line.product_id.type == "service"
                    and line.availability_status in ("full", "partial", "on_order")
                ):
                    sale.is_ok_expected_delivery_date = True
                    break
            else:
                sale.is_ok_expected_delivery_date = False

    def action_open_move_need_release(self):
        self.ensure_one()
        if not self.move_need_release_count:
            return
        xmlid = "stock_available_to_promise_release.stock_move_release_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [
            ("picking_id", "in", self.picking_ids.ids),
            ("need_release", "=", True),
        ]
        action["context"] = {}
        return action
