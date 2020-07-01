# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    shipping_weight = fields.Float(
        string="Shipping weight (kg)", compute="_compute_shipping_weight",
    )

    def action_confirm(self):
        """Automatically add delivery.carrier on sale order confirmation"""
        for order in self:
            if (
                any([line.product_id.type != "service" for line in order.order_line])
                and not order.carrier_id
            ):
                order.carrier_id = order.get_preferred_carrier()
        return super().action_confirm()

    @api.depends("order_line", "order_line.shipping_weight")
    def _compute_shipping_weight(self):
        for order in self:
            order.shipping_weight = sum(order.order_line.mapped("shipping_weight"))

    def get_preferred_carrier(self):
        self.ensure_one()
        return fields.first(
            self.env["sale.delivery.carrier.preference"].get_preferred_carriers(self)
        )

    def action_open_delivery_wizard(self):
        res = super().action_open_delivery_wizard()
        if not self.env.context.get("carrier_recompute"):
            carrier = self.get_preferred_carrier()
            res["context"]["default_carrier_id"] = carrier.id
        return res


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    shipping_weight = fields.Float(
        string="Shipping weight (kg)", compute="_compute_shipping_weight",
    )

    @api.depends("product_id", "product_uom_qty", "product_uom")
    def _compute_shipping_weight(self):
        uom_categ_weight = self.env.ref(
            "uom.product_uom_categ_kgm", raise_if_not_found=False
        )
        uom_kg = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        for line in self:
            line_weight = 0
            if line.product_id and line.product_id.type == "product":
                if line.product_uom.category_id == uom_categ_weight:
                    if line.product_uom == uom_kg:
                        line_weight = line.product_uom_qty
                    else:
                        line_weight = line.product_uom._compute_quantity(
                            line.product_uom_qty, uom_kg
                        )
                else:
                    line_qty = line.product_uom_qty
                    if line.product_uom != line.product_id.uom_id:
                        line_qty = line.product_uom._compute_quantity(
                            line.product_uom_qty, line.product_id.uom_id
                        )
                    line_weight = line.product_id.weight * line_qty
            line.shipping_weight = line_weight
