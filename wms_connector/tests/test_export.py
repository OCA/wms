# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from .common import WmsConnectorCommon

class TestExportFile(WmsConnectorCommon):
    def setUp(self):
        super().setUp()
        self.warehouse.active_wms_sync = True

    # def test_run_export_cron(self):
    #     self.warehouse.wms_export_cron_id.method_direct_trigger()

    def test_export_product(self):
        self.warehouse.refresh_wms_products()
        self.warehouse.wms_export_cron_id.method_direct_trigger()
        self.assertNewAttachmentQueue()
