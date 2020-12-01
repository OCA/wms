# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo_test_helper import FakeModelLoader

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSetLineDestinationPickPackCase(ZonePickingCommonCase):
    """Tests set_line_destination when `pick_pack_same_time` is one

    * /set_destination

    """

    @classmethod
    def _load_test_models(cls):
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import DeliveryCarrierTest, ProductPackagingTest

        cls.loader.update_registry((DeliveryCarrierTest, ProductPackagingTest))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls._load_test_models()
        cls.carrier = cls.env["delivery.carrier"].search([], limit=1)
        default_pkging = (
            cls.env["product.packaging"].sudo().create({"name": "TEST DEFAULT"})
        )
        cls.carrier.sudo().write(
            {
                "delivery_type": "test",
                "integration_level": "rate",  # avoid sending emails
                "test_default_packaging_id": default_pkging.id,
            }
        )

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id
        self.menu.sudo().pick_pack_same_time = True

    def test_set_destination_location_no_carrier(self):
        """Scan location but carrier not set on picking"""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        move_line.location_dest_id = self.shelf1
        # Confirm the destination with the right destination
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.picking_without_carrier_cannot_pack(
                move_line.picking_id
            ),
        )

    def test_set_destination_location_ok_carrier(self):
        """When carried is set goods are packed into new delivery package."""
        existing_packages = self.env["stock.quant.package"].search([])
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids
        move_line.location_dest_id = self.shelf1
        move_line.picking_id.carrier_id = self.carrier
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        delivery_pkg = move_line.result_package_id
        self.assertNotIn(delivery_pkg, existing_packages)
        self.assertEqual(
            delivery_pkg.packaging_id, self.carrier.test_default_packaging_id
        )
        message = self.msg_store.confirm_pack_moved()
        message["body"] += "\n" + self.msg_store.goods_packed_in(delivery_pkg)["body"]
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=message,
        )

    def test_set_destination_package_full_qty_no_carrier(self):
        """Scan destination package, no carrier on picking."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.picking_without_carrier_cannot_pack(
                move_line.picking_id
            ),
        )

    def test_set_destination_package_full_qty_ok_carrier_bad_package(self):
        """Scan destination package, carrier on picking, package invalid."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        move_line.picking_id.carrier_id = self.carrier
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": False,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.packaging_invalid_for_carrier(
                self.free_package.packaging_id, self.carrier
            ),
        )

    def test_set_destination_package_full_qty_ok_carrier_ok_package(self):
        """Scan destination package, carrier on picking, package valid."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        moves_before = self.picking1.move_lines
        self.assertEqual(len(moves_before), 1)
        self.assertEqual(len(moves_before.move_line_ids), 1)
        move_line = moves_before.move_line_ids
        move_line.picking_id.carrier_id = self.carrier
        self.free_package.packaging_id = self.carrier.test_default_packaging_id
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
                "confirmation": True,
            },
        )
        # Check picking data
        moves_after = self.picking1.move_lines
        self.assertEqual(moves_before, moves_after)
        self.assertRecordValues(
            move_line,
            [
                {
                    "result_package_id": self.free_package.id,
                    "product_uom_qty": 10,
                    "qty_done": 10,
                    "shopfloor_user_id": self.env.user.id,
                },
            ],
        )
        # Check response
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
