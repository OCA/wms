# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
import uuid
from odoo_test_helper import FakeModelLoader
from odoo.addons.component.tests.common import ComponentMixin
from odoo.addons.attachment_synchronize.tests.common import SyncCommon
import datetime


class WmsConnectorCommon(SyncCommon):
    # pylint: disable=W8106
    def setUp(self):
        super().setUp()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("wms_connector.demo_wms_backend")
        cls.backend.directory_path = str(uuid.uuid1()) + "/"
        cls.aq_before = cls.env["attachment.queue"].search([])
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .model import WmsProductSync, StockPicking
        cls.loader.update_registry(
            (
                WmsProductSync,
                StockPicking,
            )
        )
        cls.setUpComponent()

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def assertNewAttachmentQueue(self, n=1):
        aq_after = self.env["attachment.queue"].search([])
        self.assertEqual(len(aq_after - self.aq_before), n)
        return aq_after

    def setAllExported(self):
        self.env["stock.picking"].search([]).wms_export_date = datetime.date.today()
        self.env["wms.product.sync"].search([]).wms_export_date = datetime.date.today()
