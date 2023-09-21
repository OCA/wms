# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ShipmentAdvice(models.Model):
    _inherit = "shipment.advice"

    delivery_date = fields.Date(
        states={
            "draft": [("readonly", False)],
            "confirmed": [("readonly", False)],
            "in_progress": [("readonly", False)],
        },
        readonly=True,
        help=("maxium shipment date on the channel of related pickings"),
    )
