# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestActivateSync(SavepointCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env.ref("stock.warehouse0")

    def test_active_deactivate_wms_sync(self):
        self.warehouse.active_wms_sync = True
        for field in (
            "wms_export_cron_id",
            "wms_import_confirm_reception_cron_id",
            "wms_import_confirm_delivery_cron_id",
        ):
            self.assertTrue(getattr(self.warehouse, field))
        self.warehouse.active_wms_sync = False
        for field in (
            "wms_export_cron_id",
            "wms_import_confirm_reception_cron_id",
            "wms_import_confirm_delivery_cron_id",
        ):
            self.assertFalse(getattr(self.warehouse, field).active)

    def test_wms_product_sync_created(self):
        self.warehouse.active_wms_sync = True
        self.warehouse.refresh_wms_products()
        self.assertEqual(
            len(self.env["product.product"].search([])),
            len(self.env["wms.product.sync"].search([])),
        )

    def test_wms_product_sync_created_filter(self):
        self.warehouse.active_wms_sync = True
        self.warehouse.wms_export_product_filter_id.domain = '[("id" ,"=", {})]'.format(
            self.env.ref("product.product_product_1").id
        )
        self.warehouse.refresh_wms_products()
        self.assertEqual(
            1,
            len(self.env["wms.product.sync"].search([])),
        )
