# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestActivateSync(TransactionCase):
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
            self.assertTrue(getattr(self, field))
        self.warehouse.active_wms_sync = False
        for field in (
            "wms_export_cron_id",
            "wms_import_confirm_reception_cron_id",
            "wms_import_confirm_delivery_cron_id",
        ):
            self.assertFalse(getattr(self, field).active)
