# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    release_channel_shipment_advice_arrival_delay = fields.Integer(
        help="Default value for the delay between the release channel process "
        "end time and the arrival of shipments to docks of this warehouse.",
    )
    release_channel_shipment_advice_departure_delay = fields.Integer(
        help="Default value for the delay between the release channel process "
        "end time and the departure of shipments from the dock.",
    )
