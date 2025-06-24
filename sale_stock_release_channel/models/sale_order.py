# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @property
    def _release_channel_possible_candidate_domain_base(self):
        """Base domain for finding channel candidates based on picking.

        Mimick the domain defined on stock.picking
        Do not check company, only warehouse
        """
        # Nice to have: also check picking types contain one of the outgoing
        # picking types of the warehouse. For now, we rely on the warehouse
        # properly filled in in case of multi-warehouse setup. This is
        # reasonable.
        return [
            ("warehouse_id", "in", (False, self.warehouse_id.id)),
        ]
