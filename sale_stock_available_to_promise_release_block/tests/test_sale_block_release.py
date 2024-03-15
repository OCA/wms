# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.sale_stock_available_to_promise_release.tests import common


class TestSaleBlockRelease(common.Common):
    def test_sale_release_not_blocked(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.assertFalse(self.sale.block_release)
        self.sale.action_confirm()
        self.assertFalse(self.sale.picking_ids.release_blocked)

    def test_sale_release_blocked(self):
        self._set_stock(self.line.product_id, self.line.product_uom_qty)
        self.sale.block_release = True
        self.sale.action_confirm()
        self.assertTrue(self.sale.picking_ids.release_blocked)
