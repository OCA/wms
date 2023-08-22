# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_single_pack_transfer_base import (
    SinglePackTransferCommonBase,
)


class TestSinglePackTransferForcePackage(SinglePackTransferCommonBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prepare the pack and related picking has started
        cls.pack_a = cls.env["stock.quant.package"].create(
            {"location_id": cls.stock_location.id}
        )
        cls.quant_a = (
            cls.env["stock.quant"]
            .sudo()
            .create(
                {
                    "product_id": cls.product_a.id,
                    "location_id": cls.shelf1.id,
                    "quantity": 1,
                    "package_id": cls.pack_a.id,
                }
            )
        )
        cls.picking = cls._create_initial_move(lines=[(cls.product_a, 1)])
        cls.package_level = cls.picking.move_line_ids.package_level_id
        cls.package_level.is_done = True
        cls.picking.move_line_ids.qty_done = 1
        # Add restriction on destination location
        cls.shelf2.sudo().package_restriction = "singlepackage"
        # Add a package on the destination location
        cls._update_qty_in_location(
            cls.shelf2,
            cls.product_a,
            1,
            package=cls.env["stock.quant.package"].create(
                {"location_id": cls.shelf2.id}
            ),
        )

    def test_scan_location_has_restrictions(self):
        """ """
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": self.package_level.id,
                "location_barcode": self.shelf2.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="scan_location",
            data=self.ANY,
            message=self.service.msg_store.location_has_restrictions(),
        )
