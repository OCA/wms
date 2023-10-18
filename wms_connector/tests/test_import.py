# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import WmsConnectorCase


class TestImport(WmsConnectorCase):
    def setUp(self):
        super().setUp()

    def test_import_file(self):
        pass
