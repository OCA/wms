# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor.tests.test_cluster_picking_unload import (
    ClusterPickingUnloadingCommonCase,
)


# pylint: disable=missing-return
class ClusterPickingUnloadPackingCommonCase(ClusterPickingUnloadingCommonCase):
    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.bin1.write({"name": "bin1", "is_internal": True})
        cls.bin2.write({"name": "bin2", "is_internal": True})
        cls.menu.sudo().pack_pickings = True
