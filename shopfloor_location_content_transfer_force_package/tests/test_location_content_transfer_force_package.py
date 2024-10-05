# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)


class LocationContentTransferSetDestinationForcePackage(
    LocationContentTransferCommonCase
):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.location = cls.content_loc
        cls.no_location = cls.env["stock.location"]
        cls.package = cls.env["stock.quant.package"].create({})
        cls._update_qty_in_location(cls.location, cls.product_a, 1, package=cls.package)
        cls.empty_package = cls.env["stock.quant.package"].create({})
        cls.no_package = cls.env["stock.quant.package"]

        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.moves = cls.picking.move_lines

    def test_scanned_location_with_no_package_no_restriction_ok(self):
        message = self.service._set_dest_validate_location(
            self.moves, self.location, self.no_package, self.no_package
        )
        self.assertFalse(message)

    def test_scanned_package_with_restriction_ok(self):
        self.location.package_restriction = "singlepackage"
        message = self.service._set_dest_validate_location(
            self.moves, self.no_location, self.package, self.no_package
        )
        self.assertFalse(message)

    def test_scanned_location_with_restriction_not_empty_package_nok(self):
        self.location.package_restriction = "singlepackage"
        message = self.service._set_dest_validate_location(
            self.moves, self.location, self.no_package, self.no_package
        )
        self.assertTrue(message)

    def test_scanned_location_with_restriction_with_empty_package_ok(self):
        self.location.package_restriction = "singlepackage"
        message = self.service._set_dest_validate_location(
            self.moves, self.location, self.no_package, self.empty_package
        )
        self.assertFalse(message)
