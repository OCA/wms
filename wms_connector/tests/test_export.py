# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import WmsConnectorCase

FN_EXPORT_VALS = (
    "odoo.addons.wms_connector.tests.model.WmsProductSync._prepare_export_data"
)


class TestExportFile(WmsConnectorCase):
    def setUp(self):
        super().setUp()
        self.warehouse.active_wms_sync = True
        self.cron_export_product = self.warehouse.wms_export_product_cron_id
        self.cron_export_picking_in = self.warehouse.wms_export_picking_in_cron_id
        self.cron_export_picking_out = self.warehouse.wms_export_picking_out_cron_id
        self.demo_product = self.env.ref("product.product_product_1")

    def test_export_filter(self):
        self.warehouse.refresh_wms_products()
        self.setAllExported()
        prd = self.env["wms.product.sync"].search(
            [("product_id", "=", self.demo_product.id)]
        )
        prd.wms_export_date = False
        self.cron_export_product.method_direct_trigger()
        self.assertTrue(prd.wms_export_date)
        self.assertNewAttachmentQueue()

    def test_export_error(self):
        self.warehouse.refresh_wms_products()
        self.setAllExported()
        self.env["wms.product.sync"].search(
            [("product_id", "=", self.demo_product.id)]
        ).wms_export_date = False
        self.demo_product.name = "".rjust(110, "X")
        self.cron_export_product.method_direct_trigger()
        wms_product = self.env["wms.product.sync"].search(
            [("product_id", "=", self.demo_product.id)]
        )
        self.assertIn("Boom", wms_product.wms_export_error)

    def test_export_repeat(self):
        self.warehouse.refresh_wms_products()
        self.cron_export_product.method_direct_trigger()
        n_products = len(self.env["wms.product.sync"].search([]).ids)
        self.assertNewAttachmentQueue(n_products)
        self.cron_export_product.method_direct_trigger()
        self.assertNewAttachmentQueue(n_products)

    def test_export_pickings(self):
        self.env["stock.picking"].search([]).state = "assigned"
        self.cron_export_picking_in.method_direct_trigger()
        aq_in = len(
            self.env["stock.picking"]
            .search(
                [
                    ("wms_export_date", "!=", False),
                    ("picking_type_id", "=", self.warehouse.in_type_id.id),
                ]
            )
            .ids
        )
        self.assertNewAttachmentQueue(aq_in)
        self.cron_export_picking_out.method_direct_trigger()
        aq_out = len(
            self.env["stock.picking"]
            .search(
                [
                    ("wms_export_date", "!=", False),
                    ("picking_type_id", "=", self.warehouse.out_type_id.id),
                ]
            )
            .ids
        )
        self.assertNewAttachmentQueue(aq_in + aq_out)
