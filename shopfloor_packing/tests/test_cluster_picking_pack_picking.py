# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .common import ClusterPickingUnloadPackingCommonCase


class TestClusterPickingPrepareUnload(ClusterPickingUnloadPackingCommonCase):
    def test_scan_destination_pack_bin_not_internal(self):
        """Scan a destination package that is not an internal package."""
        self.bin2.is_internal = False
        move_line = self.move_lines[0]
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": move_line.id,
                # this bin is used for the other picking
                "barcode": self.bin2.name,
                "quantity": move_line.reserved_qty,
            },
        )
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(move_line),
            message=self.service.msg_store.bin_should_be_internal(self.bin2),
        )

    def test_prepare_unload_all_same_dest(self):
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
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 4,
            },
        )
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        result_package = picking.move_line_ids.mapped("result_package_id")
        self.assertEqual(len(result_package), 1)
        self.assertEqual(result_package[0].number_of_parcels, 4)

        picking = move_lines[0].picking_id
        data = self.data_detail.pack_picking_detail(picking)
        # message = self.service.msg_store.stock_picking_packed_successfully(picking)
        self.assert_response(
            response, next_state="pack_picking_scan_pack", data=data, message=message
        )
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin2.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
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

    def test_prepare_unload_different_dest(self):
        """All move lines have different destination locations."""
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[:1], self.bin2)
        self._set_dest_package_and_done(move_lines[1:], self.bin1)
        move_lines[:1].write({"location_dest_id": self.packing_a_location.id})
        move_lines[1:].write({"location_dest_id": self.packing_b_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # The first bin to process is bin1 we should therefore a pack_picking
        # step with the picking info of the last move_line
        picking = move_lines[-1].picking_id
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 4,
            },
        )

        message = self.service.msg_store.stock_picking_packed_successfully(picking)

        # next picking..
        picking = move_lines[0].picking_id
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response, next_state="pack_picking_scan_pack", data=data, message=message
        )
        # we scan the pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin2.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        # we process to the put in pack
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 2,
            },
        )
        # Since the last move_line has been put in pack first, the first pack
        # to unload is the one from the last move_line
        new_bin = move_lines[-1].result_package_id
        location = move_lines[-1].location_dest_id
        data = self._data_for_batch(self.batch, location, pack=new_bin)
        message = self.service.msg_store.stock_picking_packed_successfully(picking)
        self.assert_response(
            response, next_state="unload_single", data=data, message=message
        )

    def test_prepare_full_bin_unload(self):
        # process one move_line and call unload
        # the unload should return a pack_picking state
        # and once processed continue with next move_lines
        move_lines = self.move_lines
        self._set_dest_package_and_done(move_lines[0], self.bin1)
        move_lines.write({"location_dest_id": self.packing_location.id})
        response = self.service.dispatch(
            "prepare_unload", params={"picking_batch_id": self.batch.id}
        )
        # step with the picking info of the last move_line
        picking = move_lines[0].picking_id
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        # we scan the pack and  process to the put in pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 4,
            },
        )
        result_package = picking.move_line_ids.mapped("result_package_id")
        self.assertEqual(len(result_package), 1)
        self.assertEqual(result_package[0].number_of_parcels, 4)

        # now we must unload
        location = move_lines[0].location_dest_id
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
            message=self.service.msg_store.stock_picking_packed_successfully(picking),
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "picking_batch_id": self.batch.id,
                "barcode": self.packing_location.barcode,
            },
        )

        # once the unload is done, we must process the others move_lines
        move_line = self.service._next_line_for_pick(self.batch)
        while move_line:
            picking = move_line.picking_id
            self.assertEqual(response["next_state"], "start_line")
            response = self.service.dispatch(
                "scan_destination_pack",
                params={
                    "picking_batch_id": self.batch.id,
                    "move_line_id": move_line.id,
                    "barcode": self.bin1.name,
                    "quantity": move_line.reserved_uom_qty,
                },
            )
            move_line = self.service._next_line_for_pick(self.batch)

        # everything is processed, we should put in pack...
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_scan_pack",
            data=data,
        )
        # we scan the pack and  process to the put in pack
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "barcode": self.bin1.name,
            },
        )
        data = self.data_detail.pack_picking_detail(picking)
        self.assert_response(
            response,
            next_state="pack_picking_put_in_pack",
            data=data,
        )
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 2,
            },
        )
        data = self._data_for_batch(self.batch, location)
        self.assert_response(
            response,
            next_state="unload_all",
            data=data,
            message=self.service.msg_store.stock_picking_packed_successfully(picking),
        )

        result_package = picking.move_line_ids.mapped("result_package_id")
        self.assertEqual(len(result_package), 1)
        self.assertEqual(result_package[0].number_of_parcels, 2)

    def test_response_for_scan_destination(self):
        """Check that non internal package are not proposed as package_dest."""
        line1 = self.two_lines_picking.move_line_ids[0]
        # we already scan and put the first line in bin1
        self._set_dest_package_and_done(line1, self.bin1)
        self.bin1.is_internal = False
        self.assertFalse(self.service._last_picked_line(line1.picking_id))
        response = self.service._response_for_scan_destination(line1)
        self.assertFalse(response["data"]["scan_destination"]["package_dest"])

    def test_put_in_pack_partial_qty(self):
        """
        Special case.

        If a partially available product becomes completely available and the reserved
        quantity increases after the "put in pack" action, a new move line will be
        created with the done quantity as a copy of the line that will be packed.
        The original line will keep the result package, which is the package scanned
        by the operator, and the remaining quantity to do.

        Since the package is an internal package, the line with the remaining quantity
        to do will be proposed in the packing process and considered as picked. If the
        operator don't pay attention, and confirm the packaging, both lines will be set
        to done.
        Test:
            - The new line is correctly packed.
            - The original line has no result package.
            - After the "put in pack" of the partial quantity, the scenario returns
            the unload step.
        """
        move_line = self.move_lines[0]
        picking = move_line.picking_id
        self.assertEqual(len(picking.move_line_ids), 1)
        move_line.reserved_uom_qty = 5
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": move_line.id,
                "barcode": self.bin1.name,
                # collect half the demanded qty
                "quantity": 5,
            },
        )
        move_line.reserved_uom_qty = 10
        self.assertEqual(response["next_state"], "start_line")
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": move_line.picking_id.id,
                "barcode": self.bin1.name,
            },
        )
        self.assertEqual(response["next_state"], "pack_picking_put_in_pack")
        response = self.service.dispatch(
            "put_in_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": picking.id,
                "nbr_packages": 2,
            },
        )
        # after the put in pack, a new line is created with the remaining qty to do
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertFalse(move_line.result_package_id)
        self.assertTrue((picking.move_line_ids - move_line).result_package_id)
        self.assertFalse(
            (picking.move_line_ids - move_line).result_package_id.is_internal
        )
        self.assertEqual(response["next_state"], "unload_all")
        response = self.service.dispatch(
            "scan_packing_to_pack",
            params={
                "picking_batch_id": self.batch.id,
                "picking_id": move_line.picking_id.id,
                "barcode": self.bin1.name,
            },
        )
        self.assertEqual(response["next_state"], "unload_all")
