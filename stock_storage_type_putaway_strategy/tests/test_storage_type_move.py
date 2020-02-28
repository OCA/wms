# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestStorageTypeMove(TestStorageTypeCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.areas.write({"pack_putaway_strategy": "ordered_locations"})

    def test_package_level_location_dest_domain_only_empty(self):
        # Set pallets location type as only empty
        self.pallets_location_storage_type.write({"only_empty": True})
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 96.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 48.0
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_lines.mapped("location_dest_id"),
            self.stock_location
        )
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 2
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_2_location,
        )
        self.assertEqual(
            int_picking.package_level_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_2_location,
        )
        package_type_locations = int_picking.package_level_ids.mapped(
            'package_id.package_storage_type_id.storage_location_sequence_ids.location_id'
        )
        possible_locations = self.env['stock.location'].search(
            [
                ('allowed_location_storage_type_ids', 'in', int_picking.package_level_ids.mapped('package_id.package_storage_type_id.location_storage_type_ids').ids),
                ('location_id', 'child_of',  int_picking.location_dest_id.id),
                ('location_id', 'child_of', package_type_locations.ids),
                ('child_ids', '=', False),  # Removes areas
                # TODO check change on _existing domain
            ]
        )
        self.assertEqual(
            int_picking.package_level_ids.mapped("allowed_location_dest_ids"),
            possible_locations - int_picking.package_level_ids.mapped("location_dest_id"),
        )

    def test_unallowed_move(self):
        pass
