# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestExportFile(TransactionCase):

    def setUp(self):
        super().setUp()
        self.warehouse = self.env.ref("stock.warehouse0")
        self.warehouse.active_wms_sync = True

    def test_run_export_cron(self):
        self.warehouse.wms_export_cron_id.run()
        pass

