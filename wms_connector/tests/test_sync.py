# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestSync(TransactionCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env.ref("stock.warehouse0")

    def test_generate_task_cron(self):
        self.warehouse.active_wms_sync = True
        self.assertTrue(self.warehouse.sync_cron_id)
        self.assertTrue(self.warehouse.sync_task_id)
        self.warehouse.active_wms_sync = False
        self.assertFalse(self.warehouse.sync_cron_id.active)
        self.assertFalse(self.warehouse.sync_task_id.active)
