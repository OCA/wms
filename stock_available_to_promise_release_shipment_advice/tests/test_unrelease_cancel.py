# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from odoo.exceptions import UserError

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestAvailableToPromiseRelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping = cls._out_picking(
            cls._create_picking_chain(
                cls.wh, [(cls.product1, 5)], date=datetime(2019, 9, 2, 16, 0)
            )
        )
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "allow_unrelease_return_done_move": True,
            }
        )

        cls.shipping.release_available_to_promise()
        cls.cleanup_type = cls.env["stock.picking.type"].create(
            {
                "name": "Cancel Cleanup",
                "default_location_dest_id": cls.loc_stock.id,
                "sequence_code": "CCP",
                "code": "internal",
            }
        )
        cls.picking = cls._prev_picking(cls.shipping)
        cls.picking.picking_type_id.return_picking_type_id = cls.cleanup_type
        cls.shipment_advice = cls.env["shipment.advice"].create(
            {"shipment_type": "outgoing"}
        )

    def test_unrelease_notloaded(self):
        """Unrelease is allowed when delivery is not loaded"""
        self._deliver(self.picking)
        self.assertTrue(self.shipping.move_lines.unrelease_allowed)
        self.shipping.unrelease()
        self.assertTrue(self.shipping.need_release)

    def test_unrelease_loaded(self):
        """Unrelease is not allowed when delivery is loaded"""
        self._deliver(self.picking)
        self.shipping.move_line_ids._load_in_shipment(self.shipment_advice)
        self.assertFalse(self.shipping.move_lines.unrelease_allowed)
        with self.assertRaisesRegex(UserError, "You are not allowed to unrelease"):
            self.shipping.unrelease()
        self.assertFalse(self.shipping.need_release)
