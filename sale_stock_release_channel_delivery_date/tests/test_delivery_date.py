# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.fields import Command

from odoo.addons.sale.tests.common import SaleCommon
from odoo.addons.stock_release_channel.tests.common import (  # noqa
    StockReleaseChannelDeliveryDateCommon,
)


class TestSaleStockReleaseChannelDeliveryDate(
    StockReleaseChannelDeliveryDateCommon, SaleCommon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.channel.warehouse_id = cls.warehouse
        cls.channel.is_manual_assignment = False

    @freeze_time("2025-01-02 10:00:00")
    def test_empty(self):
        """Test empty SO

        Expected date is computed as if there will be stock lines"""
        so = self.empty_order
        dt = fields.Datetime.now() + timedelta(days=2)
        # the order was created in setup outside freezegun
        so.invalidate_recordset(["expected_date"])
        self.assertEqual(so.expected_date, dt)

    @freeze_time("2025-01-02 10:01:00")
    def test_service(self):
        """Test SO with service"""
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.service_product.id,
                            "product_uom_qty": 22,
                        }
                    )
                ],
            }
        )
        dt = fields.Datetime.now()
        # the order was created in setup outside freezegun
        so.invalidate_recordset(["expected_date"])
        self.assertEqual(so.expected_date, dt)

    @freeze_time("2025-01-02 10:02:00")
    def test_product(self):
        """Test SO with 2 consumables"""
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.consumable_product.id,
                            "product_uom_qty": 22,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.consumable_product.id,
                            "product_uom_qty": 22,
                        }
                    ),
                ],
            }
        )
        dt = fields.Datetime.now() + timedelta(days=2)
        # the order was created in setup outside freezegun
        so.invalidate_recordset(["expected_date"])
        self.assertEqual(so.expected_date, dt)

    @freeze_time("2025-01-02 10:03:00")
    def test_product_customer_lead(self):
        """Test SO with a customer lead time"""
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.consumable_product.id,
                            "product_uom_qty": 22,
                            "customer_lead": 5,
                        }
                    )
                ],
            }
        )
        dt = fields.Datetime.now() + timedelta(days=7)
        # the order was created in setup outside freezegun
        so.invalidate_recordset(["expected_date"])
        self.assertEqual(so.expected_date, dt)
