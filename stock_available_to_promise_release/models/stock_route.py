# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    available_to_promise_defer_pull = fields.Boolean(
        string="Release based on Available to Promise",
        default=False,
        help="Do not create chained moved automatically for delivery. "
        "Transfers must be released manually when they have enough available"
        " to promise.",
    )

    no_backorder_at_release = fields.Boolean(
        string="No backorder at release",
        default=False,
        help="When releasing a transfer, do not create a backorder for the "
        "moves created for the unavailable quantities.",
    )
