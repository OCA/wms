# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    adr_message = fields.Text(readonly=True)

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        res = super()._onchange_carrier_id()
        self._set_adr_warning()
        return res

    @api.onchange("order_id")
    def _onchange_order_id(self):
        res = super()._onchange_carrier_id()
        self._set_adr_warning()
        return res

    def _set_adr_warning(self):
        """Sets a warning if any sale order line has a good defined as
            dangerous and if this same dangerosity is defined on the carrier"""
        self.ensure_one()
        warning = self.order_id._check_adr(carrier=self.carrier_id)
        if warning:
            self.adr_message = warning.get("warning").get("message")
