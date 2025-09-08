# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first

from .common import ClusterPickingUnloadPackingCommonCase


class TestClusterPickingPrepareUnload(ClusterPickingUnloadPackingCommonCase):
    def _create_package_type(self):
        self.carrier_product = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test Product",
                    "type": "service",
                }
            )
        )
        self.carrier = (
            self.env["delivery.carrier"]
            .sudo()
            .create(
                {
                    "name": "Test Carrier",
                    "product_id": self.carrier_product.id,
                }
            )
        )
        self.package_type = (
            self.env["stock.package.type"]
            .sudo()
            .create(
                {
                    "name": "BOX-5",
                    "package_carrier_type": "none",
                    "number_of_parcels": 5.0,
                    "barcode": "BOX-5",
                }
            )
        )
        self.package_types = self.env["stock.package.type"].search(
            [("package_carrier_type", "=", "none")], order="number_of_parcels,name"
        )

    def test_prepare_unload_all_same_dest_with_dest_package(self):
        """
        Activate the behavior that allows to pack at the pick step (cluster)
        Activate the behavior that change the default action -> Scan the package type
        At the unload step, ask to select a delivery package (from types)
        """
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        location = self.packing_location
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
                "nbr_packages": 4,
            },
        )
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        result_package = picking.move_line_ids.mapped("result_package_id")
        self.assertEqual(len(result_package), 1)
        self.assertEqual(result_package[0].number_of_parcels, 4)

        picking = move_lines[0].picking_id
        data = self.data.pack_picking(picking)
        # message = self.service.msg_store.stock_picking_packed_successfully(picking)
        self.assert_response(
            response, next_state="pack_picking_scan_pack", data=data, message=message
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin2.name,
            },
        )
        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
                "nbr_packages": 2,
            },
        )
        data = self._data_for_batch(self.batch, location)
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        self.assert_response(
            response, next_state="unload_all", data=data, message=message
        )

        result_package = picking.move_line_ids.mapped("result_package_id")
        self.assertEqual(len(result_package), 1)
        self.assertEqual(result_package[0].number_of_parcels, 2)

    def test_pack_no_package_type(self):
        """
        Activate the behavior that allows to pack at the pick step (cluster)
        Activate the behavior that change the default action -> Scan the package type
        At the unload step, ask to select a delivery package (from types)
        """
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )
        # We use new pack
        response = self.service.dispatch(
            "list_delivery_package_types",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
            },
        )
        message = {
            "message_type": "warning",
            "body": "No delivery package type available.",
        }
        data = self.data.select_package(picking, lines)
        self.assert_response(
            response, next_state="select_package", data=data, message=message
        )

    def test_list_delivery_package_picking_done(self):
        """ """
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )

        picking._action_done()
        # Delivery is already done
        response = self.service.dispatch(
            "list_delivery_package_types",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
            },
        )
        message = {"message_type": "info", "body": "Operation already processed."}
        data = {}
        self.assert_response(response, next_state="start", data=data, message=message)

    def test_list_delivery_package_picking_qty_superior(self):
        self._create_package_type()
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        picking.carrier_id = self.carrier
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )
        line = first(picking.move_line_ids)
        line.qty_picked = line.quantity + 1
        # Delivery is already done
        response = self.service.dispatch(
            "list_delivery_package_types",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
            },
        )
        msg_store = self.service.msg_store
        message = msg_store.selected_lines_qty_picked_higher_than_allowed(line)
        data = self.data.select_package(picking, lines.sorted())
        # data  = self.data.pack_picking(next_picking)
        self.assert_response(
            response, next_state="select_package", data=data, message=message
        )

    def test_pack_package_type(self):
        self._create_package_type()
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        picking.carrier_id = self.carrier
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )
        # We use new pack
        response = self.service.dispatch(
            "list_delivery_package_types",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
            },
        )
        data = {}
        data["selected_lines_for_packing"] = self.data.move_lines(lines)
        data["package_type"] = self.data.package_type_list(self.package_types)
        data["picking"] = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="select_delivery_package_type",
            data=data,
        )

        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
                "package_type_id": self.package_type.id,
            },
        )
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        next_picking = self.batch.picking_ids.filtered(
            lambda p: p.is_shopfloor_packing_todo
        )
        data = data = self.data.pack_picking(next_picking)

        self.assert_response(
            response, next_state="pack_picking_scan_pack", data=data, message=message
        )

    def test_pack_package_type_scan(self):
        self._create_package_type()
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        picking.carrier_id = self.carrier
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )

        # we scan the package type
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
                "barcode": "BOX-5",
            },
        )
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        next_picking = first(
            self.batch.picking_ids.filtered(lambda p: p.is_shopfloor_packing_todo)
        )
        data = self.data.pack_picking(next_picking)
        self.assert_response(
            response, next_state="pack_picking_scan_pack", message=message, data=data
        )

    def test_pack_package_type_no_picking(self):
        self._create_package_type()
        self.menu.sudo().write(
            {
                "pick_pack_same_time": True,
                "default_pack_pickings_action": "package_type",
            }
        )

        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore scan the bin 1
        # to pack and put in pack
        picking = move_lines[-1].picking_id
        picking.carrier_id = self.carrier
        data = self.data.pack_picking(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        lines = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id.is_internal
        ).sorted(key=lambda ml: ml.result_package_id.name)
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )

        data = self.data.select_package(picking, lines)
        self.assert_response(
            response,
            next_state="select_package",
            data=data,
        )

        # Another action validated the picking
        picking._action_done()

        # We use new pack
        response = self.service.dispatch(
            "list_delivery_package_types",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "selected_line_ids": lines.ids,
            },
        )
        data = {}
        data["package_type"] = self.data.package_type_list(self.package_types)
        data["picking"] = self.data.picking(picking)
        message = {"message_type": "info", "body": "Operation already processed."}
        data = {}
        self.assert_response(response, next_state="start", data=data, message=message)
