# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_single_pack_transfer_base import SinglePackTransferCommonBase


class TestSinglePackTransferPutaway(SinglePackTransferCommonBase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.pallets_storage_type = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )
        cls.main_pallets_location = cls.env.ref(
            "stock_storage_type.stock_location_pallets"
        )
        cls.reserve_pallets_locations = cls.env.ref(
            "stock_storage_type.stock_location_pallets_reserve"
        )
        cls.all_pallets_locations = (
            cls.main_pallets_location.leaf_location_ids
            | cls.reserve_pallets_locations.leaf_location_ids
        )

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.package = cls.env["stock.quant.package"].create(
            {
                # this will parameterize the putaway to use pallet locations,
                # and if not, it will stay on the picking type's default dest.
                "package_storage_type_id": cls.pallets_storage_type.id,
            }
        )
        cls._update_qty_in_location(cls.shelf1, cls.product_a, 10, package=cls.package)
        cls.menu.sudo().ignore_no_putaway_available = True
        cls.menu.sudo().allow_move_create = True

    def test_normal_putaway(self):
        """Ensure putaway is applied on moves"""
        response = self.service.dispatch(
            "start", params={"barcode": self.shelf1.barcode}
        )
        self.assert_response(
            response,
            next_state="scan_location",
            data=self.ANY,
        )
        package_level_id = response["data"]["scan_location"]["id"]
        package_level = self.env["stock.package_level"].browse(package_level_id)
        self.assertIn(package_level.location_dest_id, self.all_pallets_locations)

    def test_ignore_no_putaway_available(self):
        """Ignore no putaway available is activated on the menu

        In this case, when no putaway is possible, the changes
        are rollbacked and an error is returned.
        """
        for location in self.all_pallets_locations:
            package = self.env["stock.quant.package"].create(
                {"package_storage_type_id": self.pallets_storage_type.id}
            )
            self._update_qty_in_location(location, self.product_a, 10, package=package)

        response = self.service.dispatch(
            "start", params={"barcode": self.shelf1.barcode}
        )
        self.assert_response(
            response,
            next_state="start",
            message=self.service.msg_store.no_putaway_destination_available(),
        )

        package_levels = self.env["stock.package_level"].search(
            [("package_id", "=", self.package.id)]
        )
        # no package level created to move the package
        self.assertFalse(package_levels)

    def test_putaway_move_dest_not_child_of_picking_dest(self):
        """Putaway is applied on move but the destination location is not a
        child of the default picking type destination location.
        Case where the picking is created by scanning a package level. Then the
        move destination is according to the putaway and valid.
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
        response = self.service.dispatch(
            "start", params={"barcode": self.shelf1.barcode}
        )
        self.assert_response(response, next_state="scan_location", data=self.ANY)
