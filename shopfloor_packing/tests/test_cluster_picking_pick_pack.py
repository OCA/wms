# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .common import ClusterPickingUnloadPackingCommonCase


class TestClusterPickingPrepareUnload(ClusterPickingUnloadPackingCommonCase):
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
            next_state="select_package",
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
