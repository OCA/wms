# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class AlcPromiseReleaseImmediatelyExcludeTest(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping = cls._out_picking(
            cls._create_picking_chain(
                cls.wh, [(cls.product1, 5)], date=datetime(2019, 9, 2, 16, 0)
            )
        )
        cls.loc_bin1.exclude_from_immediately_usable_qty = True
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "no_backorder_at_release": True,
            }
        )

        cls.shipping.release_available_to_promise()
        cls.picking = cls._prev_picking(cls.shipping)
        cls.picking.action_assign()

    def test_unrelease_full(self):
        """Try to unrelease the shipping move.

        As the bin location is marked as
        to exclude from immediately available, new picking should not be generated.
        """
        self.shipping.move_ids.unrelease()

        # I can release again the move and a new pick is created
        self.shipping.release_available_to_promise()
        new_picking = self._prev_picking(self.shipping) - self.picking
        self.assertFalse(new_picking)
