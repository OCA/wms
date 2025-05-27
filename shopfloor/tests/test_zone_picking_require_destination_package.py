# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


class ZonePickingNoPAcking(ZonePickingCommonCase):
    """Tests zone picking without packing steps.

    * /set_destination

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id
        self.picking1.move_line_ids.result_package_id = False

    def test_set_destination(self):
        # when no packing is set, you can set the destination directly
        # without the need to pack the product
        self.service.work.menu.sudo().require_destination_package = True
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": move_line.location_dest_id.barcode,
                "quantity": move_line.reserved_uom_qty,
                "confirmation": None,
            },
        )
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            qty_done=move_line.reserved_uom_qty,
            message=self.service.msg_store.dest_package_required(),
        )
        self.service.work.menu.sudo().require_destination_package = False
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": move_line.location_dest_id.barcode,
                "quantity": move_line.reserved_uom_qty,
                "confirmation": None,
            },
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda x: x.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location,
            picking_type,
            move_lines,
            message=self.service.msg_store.confirm_pack_moved(),
        )
