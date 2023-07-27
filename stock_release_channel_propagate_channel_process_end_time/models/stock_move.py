# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _propagate_release_channel(self):
        pickings_updated = super()._propagate_release_channel()
        pickings_updated._set_scheduled_date_to_release_channel_process_end_date()
        return pickings_updated
