# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleDeliveryCarrierPreference(models.Model):

    _name = "sale.delivery.carrier.preference"
    _description = "Preferred Shipping Methods"
    _order = "sequence, id"

    sequence = fields.Integer(required=True, default=10, index=True)
    name = fields.Char(compute="_compute_name", readonly=True)
    preference = fields.Selection(
        [("carrier", "Defined carrier"), ("partner", "Partner carrier")],
        required=True,
        default="carrier",
    )
    carrier_id = fields.Many2one("delivery.carrier", ondelete="cascade")
    sale_order_max_weight = fields.Float(
        "Sale order max weight (kg)", help="Leave empty for no limit",
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.constrains("preference", "carrier_id")
    def _check_preference_carrier_id(self):
        for pref in self:
            if pref.preference == "carrier" and not pref.carrier_id:
                raise ValidationError(
                    _(
                        "Preferred Shipping Methods with 'Carrier' preference "
                        "must define a Delivery carrier."
                    )
                )
        partner_pref_cnt = self.search_count(
            [("preference", "=", "partner"), ("company_id", "=", self.env.company.id)]
        )
        if partner_pref_cnt > 1:
            raise ValidationError(
                _(
                    "Only one Preferred Shipping Method can be set with "
                    "'Partner carrier' preference."
                )
            )

    @api.constrains("sale_order_max_weight")
    def _check_sale_order_max_weight(self):
        for pref in self:
            if pref.sale_order_max_weight < 0:
                raise ValidationError(
                    _(
                        "Sale order max weight (kg) must have a positive or "
                        "null value."
                    )
                )

    @api.onchange("preference")
    def onchange_preference(self):
        self.ensure_one()
        if self.preference == "partner" and self.carrier_id:
            self.carrier_id = False

    @api.depends("preference", "carrier_id", "sale_order_max_weight")
    def _compute_name(self):
        pref_descr = {
            k: v for k, v in self._fields["preference"]._description_selection(self.env)
        }
        for pref in self:
            name = pref_descr.get(pref.preference)
            if pref.carrier_id:
                name = _("%s: %s") % (name, pref.carrier_id.name)
            if pref.sale_order_max_weight:
                name = _("%s (Max weight %s kg)") % (name, pref.sale_order_max_weight)
            pref.name = name

    @api.model
    def get_preferred_carriers(self, order):
        wiz = self.env["choose.delivery.carrier"].new({"order_id": order.id})
        carrier_preferences = self.env["sale.delivery.carrier.preference"].search(
            [
                "&",
                "|",
                ("sale_order_max_weight", ">=", order.shipping_weight,),
                ("sale_order_max_weight", "=", 0.0,),
                "|",
                ("carrier_id", "in", wiz.available_carrier_ids.ids),
                ("carrier_id", "=", False),
            ]
        )
        carriers_ids = list()
        for cp in carrier_preferences:
            if cp.preference == "carrier":
                carriers_ids.append(cp.carrier_id.id)
            else:
                carriers_ids.append(
                    order.partner_shipping_id.property_delivery_carrier_id.id
                )
        return self.env["delivery.carrier"].browse(carriers_ids)
