# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


# TODO seems like the "partner carrier" preference will not be used.
# If true, then we should remove this model,
# move the fields (weight related fields and picking_domain)
# in "delivery.carrier" (which already has a sequence) and activate
# the "automatic carrier" by a boolean on the carrier.
class DeliveryCarrierPreference(models.Model):

    _name = "delivery.carrier.preference"
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
    max_weight = fields.Float("Max weight", help="Leave empty for no limit")
    max_weight_uom_id = fields.Many2one(
        "uom.uom",
        compute="_compute_max_weight_uom_id",
        readonly=True,
        default=lambda p: p._default_max_weight_uom_id(),
    )
    max_weight_uom_name = fields.Char(
        string="Max weight UOM",
        related="max_weight_uom_id.display_name",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    picking_domain = fields.Char(
        default="[]",
        help="Domain to restrict application of this preference "
        "for carrier selection on pickings",
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

    @api.constrains("max_weight")
    def _check_max_weight(self):
        for pref in self:
            if (
                float_compare(
                    pref.max_weight,
                    0,
                    precision_rounding=pref.max_weight_uom_id.rounding,
                )
                < 0
            ):
                raise ValidationError(
                    _("Max weight must have a positive or null value.")
                )

    @api.onchange("preference")
    def onchange_preference(self):
        self.ensure_one()
        if self.preference == "partner" and self.carrier_id:
            self.carrier_id = False

    @api.depends("preference", "carrier_id", "max_weight")
    def _compute_name(self):
        pref_descr = {
            k: v for k, v in self._fields["preference"]._description_selection(self.env)
        }
        for pref in self:
            name = pref_descr.get(pref.preference)
            if pref.carrier_id:
                name = _("%s: %s") % (name, pref.carrier_id.name)
            if pref.max_weight:
                name = _("%s (Max weight %s %s)") % (
                    name,
                    pref.max_weight,
                    pref.max_weight_uom_id.display_name,
                )
            pref.name = name

    def _default_max_weight_uom_id(self):
        return self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()

    def _compute_max_weight_uom_id(self):
        for pref in self:
            pref.max_weight_uom_id = self._default_max_weight_uom_id().id
