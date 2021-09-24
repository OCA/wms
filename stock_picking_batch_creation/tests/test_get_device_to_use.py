# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import ClusterPickingCommonFeatures


class TestGetDeviceToUse(ClusterPickingCommonFeatures):
    @classmethod
    def setUpClass(cls):
        super(TestGetDeviceToUse, cls).setUpClass()

    def test_get_device_to_use_00(self):
        """
        Data: 3 picks of type 1, total of 4 products for a volume of 60m3
        Test case: We have 3 devices possibles (device1, device2, device3),
        ordered following sequence: device3, device2, device1.
        Expected Result: "device3" should be the device to use for this cluster since its
        min volume is 30m3 and max volume is 100m3
        """
        make_picking_batch = self.makePickingBatch.create(
            {
                "user_id": self.env.user.id,
                "picking_type_ids": [(4, self.picking_type_1.id)],
                "stock_device_type_ids": [
                    (4, self.device1.id),
                    (4, self.device2.id),
                    (4, self.device3.id),
                ],
            }
        )

        candidates_pickings = make_picking_batch._search_pickings()
        for picking in candidates_pickings:
            device = make_picking_batch._compute_device_to_use(picking)
            if device:
                break
        self.assertEqual(device, self.device3)

    def test_get_device_to_use_01(self):
        """
        Data: we create 1 new product with big volume in zone 1
        Test case: We have 3 devices possibles (device1, device2, device3),
        ordered following sequence: device3, device2, device1. The volume of the products
        is higher that the max volume of device3 but not device2 which is next in line
        Expected Result: "device2" should be the device to use for this cluster since its
        max volume is 190m3
        """
        product_big_1 = self._create_product("Unittest P1 voluminous", 10, 100, 1, 1)
        picks = self._get_picks_by_type(self.picking_type_1)
        self._add_product_to_picking(picks[0], product_big_1)

        make_picking_batch = self.makePickingBatch.create(
            {
                "user_id": self.env.user.id,
                "picking_type_ids": [(4, self.picking_type_1.id)],
                "stock_device_type_ids": [
                    (4, self.device1.id),
                    (4, self.device2.id),
                    (4, self.device3.id),
                ],
            }
        )
        candidates_pickings = make_picking_batch._search_pickings()
        for picking in candidates_pickings:
            device = make_picking_batch._compute_device_to_use(picking)
            if device:
                break
        self.assertEqual(device, self.device2)
