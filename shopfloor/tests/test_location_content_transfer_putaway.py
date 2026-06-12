# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_location_content_transfer_base import LocationContentTransferCommonCase

# pylint: disable=missing-return


class TestLocationContentTransferPutaway(LocationContentTransferCommonCase):
    """Tests with putaway when using option to ignore unavailable putaway locations"""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # create a test source location to be sure it's empty
        cls.test_loc = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "location_id": cls.stock_location.id,
                    "name": "test",
                    "barcode": "test_loc",
                }
            )
        )
        cls.package_type = (
            cls.env["stock.package.type"]
            .sudo()
            .create({"name": "TestLocationContentTransferPutaway"})
        )
        cls.package_type2 = (
            cls.env["stock.package.type"]
            .sudo()
            .create({"name": "TestLocationContentTransferPutaway2"})
        )
        cls.package = cls.env["stock.quant.package"].create(
            {"package_type_id": cls.package_type.id}
        )
        cls.package2 = cls.env["stock.quant.package"].create(
            {"package_type_id": cls.package_type2.id}
        )
        cls._update_qty_in_location(
            cls.test_loc, cls.product_a, 10, package=cls.package
        )
        cls._update_qty_in_location(
            cls.test_loc, cls.product_a, 10, package=cls.package2
        )
        # create a destination child location
        cls.main_pallets_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Pallet Location",
                    "location_id": cls.picking_type.default_location_dest_id.id,
                }
            )
        )
        cls.reserve_pallets_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Reserve Pallet Location",
                    "location_id": cls.picking_type.default_location_dest_id.id,
                }
            )
        )
        cls.menu.sudo().allow_move_create = True
        cls.menu.sudo().ignore_no_putaway_available = (
            True  # read as ignore transfer when no putaway available
        )
        cls.menu.sudo().allow_unreserve_other_moves = True

    def test_normal_putaway(self):
        """Ensure putaway is applied on moves"""
        self.pallet_putaway_rule = (
            self.env["stock.putaway.rule"]
            .sudo()
            .create(
                {
                    "product_id": self.product_a.id,
                    "package_type_ids": [(6, 0, self.package_type.ids)],
                    "location_in_id": self.stock_location.id,
                    "location_out_id": self.main_pallets_location.id,
                }
            )
        )
        self.pallet_putaway_rule = (
            self.env["stock.putaway.rule"]
            .sudo()
            .create(
                {
                    "product_id": self.product_a.id,
                    "package_type_ids": [(6, 0, self.package_type2.ids)],
                    "location_in_id": self.stock_location.id,
                    "location_out_id": self.reserve_pallets_location.id,
                }
            )
        )
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.test_loc.barcode}
        )
        self.assert_response(
            response,
            next_state="start_single",
            data=self.ANY,
        )
        package_level_id = response["data"]["start_single"]["package_level"]["id"]
        package_level = self.env["stock.package_level"].browse(package_level_id)
        self.assertIn(package_level.location_dest_id, self.main_pallets_location)

    def test_ignore_no_putaway_available(self):
        """Ignore no putaway available is activated on the menu

        In this case, when no putaway is possible, the changes
        are rollbacked and an error is returned.
        """
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.test_loc.barcode}
        )
        self.assert_response(
            response,
            next_state="scan_location",
            message=self.service.msg_store.no_putaway_destination_available(),
        )

        package_levels = self.env["stock.package_level"].search(
            [("package_id", "in", (self.package.id, self.package2.id))]
        )
        # no package level created to move the package
        self.assertFalse(package_levels)

    def test_putaway_move_dest_not_child_of_picking_type_dest(self):
        """Putaway is applied on move but the destination location is not a
        child of the default picking type destination location.
        """
        # Change the default destination location of the picking type
        # to get it outside of the putaway destination
        self.picking_type.sudo().default_location_dest_id = self.main_pallets_location
        # Create a standard putaway to move the package from pallet storage
        # to a unrelated one (outside of the pallet storage tree)
        self.env["stock.putaway.rule"].sudo().create(
            {
                "product_id": self.product_a.id,
                "location_in_id": self.picking_type.default_location_dest_id.id,
                "location_out_id": self.env.ref("stock.location_refrigerator_small").id,
            }
        )
        # Check the result
        existing_moves = self.env["stock.move"].search(
            [("location_id", "=", self.test_loc.id), ("state", "=", "assigned")]
        )
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.test_loc.barcode}
        )
        self.assert_response(
            response,
            next_state="scan_location",
            data=self.ANY,
            message=self.service.msg_store.location_content_unable_to_transfer(
                self.test_loc
            ),
        )
        current_moves = self.env["stock.move"].search(
            [("location_id", "=", self.test_loc.id), ("state", "=", "assigned")]
        )
        self.assertEqual(existing_moves, current_moves)
