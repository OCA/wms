# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def has_on_going_operation(self):
        return bool(
            self.env["stock.move.line"].search(
                [
                    ("state", "not in", ("cancel", "done")),
                    ("location_id", "=", self.id),
                    ("qty_done", ">", 0),
                ]
            )
        )
