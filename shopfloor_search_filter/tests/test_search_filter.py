# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.shopfloor.tests.common import CommonCase


class TestSearchFilter(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        res = super().setUpClassVars()
        cls.picking_type = cls.env.ref("stock.picking_type_internal")

        cls.test_menu = (
            cls.env["shopfloor.menu"]
            .sudo()
            .create(
                {
                    "name": "Test Scan Search Menu",
                    "scenario_id": cls.env.ref("shopfloor.scenario_cluster_picking").id,
                    "picking_type_ids": [Command.link(cls.picking_type.id)],
                }
            )
        )
        with cls.work_on_actions(cls, menu=cls.test_menu) as work:
            cls.search = work.component(usage="search")

        return res

    def test_search_product_handler(self):
        self.test_menu.sudo().allow_product_scan = True
        res_allowed = self.search.find(barcode="A", types=["product"])
        self.assertEqual(res_allowed.type, "product")
        self.assertEqual(res_allowed.record, self.product_a)

        self.test_menu.sudo().allow_product_scan = False
        res_restricted = self.search.find(barcode="A", types=["product"])
        self.assertEqual(res_restricted.type, "none")

    def test_search_package_handler(self):
        package = self.env["stock.quant.package"].sudo().create({"name": "PKG001"})

        self.test_menu.sudo().allow_package_scan = True
        res_allowed = self.search.find(barcode="PKG001", types=["package"])
        self.assertEqual(res_allowed.type, "package")
        self.assertEqual(res_allowed.record, package)

        self.test_menu.sudo().allow_package_scan = False
        res_restricted = self.search.find(barcode="PKG001", types=["package"])
        self.assertEqual(res_restricted.type, "none")

    def test_search_picking_handler(self):
        picking = self._create_picking(lines=[(self.product_a, 1)], confirm=True)

        self.test_menu.sudo().allow_picking_scan = True
        res_allowed = self.search.find(barcode=picking.name, types=["picking"])
        self.assertEqual(res_allowed.type, "picking")
        self.assertEqual(res_allowed.record, picking)

        self.test_menu.sudo().allow_picking_scan = False
        res_restricted = self.search.find(barcode=picking.name, types=["picking"])
        self.assertEqual(res_restricted.type, "none")

    def test_search_location_handler(self):
        self.test_menu.sudo().allow_location_scan = True
        res_allowed = self.search.find(barcode="SHELF1", types=["location"])
        self.assertEqual(res_allowed.type, "location")
        self.assertEqual(res_allowed.record, self.shelf1)

        self.test_menu.sudo().allow_location_scan = False
        res_restricted = self.search.find(barcode="SHELF1", types=["location"])
        self.assertEqual(res_restricted.type, "none")

    def test_search_lot_handler(self):
        lot = self._create_lot(self.product_a)
        lot.sudo().name = "LOT001"

        self.test_menu.sudo().allow_lot_scan = True
        res_allowed = self.search.find(barcode="LOT001", types=["lot"])
        self.assertEqual(res_allowed.type, "lot")
        self.assertEqual(res_allowed.record, lot)

        self.test_menu.sudo().allow_lot_scan = False
        res_restricted = self.search.find(barcode="LOT001", types=["lot"])
        self.assertEqual(res_restricted.type, "none")

    def test_search_packaging_handler(self):
        self.test_menu.sudo().allow_packaging_scan = True
        res_allowed = self.search.find(barcode="ProductABox", types=["packaging"])
        self.assertEqual(res_allowed.type, "packaging")
        self.assertEqual(res_allowed.record, self.product_a_packaging)

        self.test_menu.sudo().allow_packaging_scan = False
        res_restricted = self.search.find(barcode="ProductABox", types=["packaging"])
        self.assertEqual(res_restricted.type, "none")
