# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
import uuid
from odoo_test_helper import FakeModelLoader
from odoo.addons.component.tests.common import SavepointComponentCase


class WmsConnectorCommon(SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("wms_connector.demo_wms_backend")
        cls.backend.directory_path = str(uuid.uuid1()) + "/"
        cls.aq_before = cls.env["attachment.queue"].search([])
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        from .model import WmsProductSync

        cls.loader.update_registry((WmsProductSync,))

    def tearDown(self):
        super().tearDown()
        files = self.backend.list_files("OUT/")
        for f in files:
            self.backend.delete("OUT/" + f)

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def assertNewAttachmentQueue(self):
        aq_after = self.env["attachment.queue"].search([])
        self.assertEqual(len(aq_after - self.env["attachment.queue"].search([])), 1)
        return aq_after
