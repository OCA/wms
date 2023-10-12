# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
import uuid
from odoo_test_helper import FakeModelLoader


class WmsConnectorCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("wms_connector.demo_wms_backend")
        cls.backend.directory_path = str(uuid.uuid1()) + "/"
        # cls.loader = FakeModelLoader(cls.env, cls.__module__)
        # cls.loader.backup_registry()
        #
        # from .model import ResUsers
        #
        # cls.loader.update_registry((AttachmentSynchronizeTask,))

    def tearDown(self):
        super().tearDown()
        files = self.backend.list_files("OUT/")
        for f in files:
            self.backend.delete("OUT/" + f)

    @classmethod
    def tearDownClass(cls):
        # cls.loader.restore_registry()
        super().tearDownClass()
