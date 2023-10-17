# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import WmsConnectorCommon
import mock

FN_EXPORT_VALS = (
    "odoo.addons.wms_connector.tests.model.WmsProductSync._prepare_export_data"
)


class TestExportFile(WmsConnectorCommon):
    def setUp(self):
        super().setUp()
        self.warehouse.active_wms_sync = True
        self.cron_export = self.warehouse.wms_export_cron_id
        self.demo_product = self.env.ref("product.product_product_1")

    def test_export_filter(self):
        self.warehouse.refresh_wms_products()
        self.setAllExported()
        self.env["wms.product.sync"].search(
            [("product_id", "=", self.demo_product.id)]
        ).wms_export_date = False
        self.cron_export.method_direct_trigger()
        self.assertNewAttachmentQueues(1)

    # def test_export_error(self):
    #     self.setAllExported()
    #     self.demo_product.wms_export_date = False
    #     # with mock.patch(FN_EXPORT_VALS) as mocked:
    #     #     # mocked.
    #     #     mocked.side_effect = derp
    #     self.cron_export.method_direct_trigger()
    #     wms_product = self.env["wms.product.sync"].search(
    #         [("product_id", "=", self.demo_product.id)]
    #     )
    #     # self.assertIn(wms_product.wms_export_error, "ValueError")

    def test_export_repeat(self):
        self.warehouse.refresh_wms_products()
        self.cron_export.method_direct_trigger()
        n_products = len(self.env["wms.product.sync"].search([]).ids)
        n_pickings = len(self.env["stock.picking"].search([]).ids)
        self.assertNewAttachmentQueues(n_pickings + n_products)
        self.cron_export.method_direct_trigger()
        self.assertNewAttachmentQueues(n_pickings + n_products)
