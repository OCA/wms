# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import _, api, exceptions, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    shipping_weight = fields.Float(
        string="Shipping weight (kg)", compute="_compute_shipping_weight"
    )

    def action_confirm(self):
        self._add_delivery_carrier_on_confirmation()
        return super().action_confirm()

    def _add_delivery_carrier_on_confirmation(self):
        """Automatically add delivery.carrier on sale order confirmation"""
        for order in self:
            if order.carrier_id or any(line.is_delivery for line in order.order_line):
                continue
            carrier = order.get_preferred_carrier()
            if not carrier:
                continue
            # rate_shipment returns None if the shipping method doesn't
            # implement rate computation. If it returns a dict, we expect it to
            # return if it was a success or not, however, to be defensive,
            # consider that a dictionary without 'success' key was a success.
            vals = carrier.rate_shipment(order) or {}
            if not vals.get("success", True):
                raise exceptions.UserError(
                    _(
                        "Error when adding shipping on {}. Try adding"
                        " shipping manually. Message: {}"
                    ).format(order.name, vals.get("error_message"))
                )
            delivery_price = vals.get("price", 0.0)
            order.set_delivery_line(carrier, delivery_price)
            order.recompute_delivery_price = False
            if vals.get("warning_message"):
                order.delivery_message = vals["warning_message"]

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
        string="Shipping weight (kg)", compute="_compute_shipping_weight"
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
