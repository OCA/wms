# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class Route(models.Model):
    _inherit = "stock.location.route"

    allow_unrelease_return_done_move = fields.Boolean(
        string="Reverse done transfer on cancellation",
        default=False,
        help=(
            "If checked, unreleasing the delivery may create a new inverse "
            "internal operation on the last done pulled transfer. "
            "Otherwise, you won't be able to unrelease as soon as one of "
            "the pulled transfer is done"
        ),
    )
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
