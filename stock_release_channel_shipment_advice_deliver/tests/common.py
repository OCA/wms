# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestStockReleaseChannelDeliverCommon(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wh.write({"delivery_steps": "pick_ship"})
        cls.output_loc = cls.wh.wh_output_stock_loc_id
        cls.channel.picking_ids.move_ids.write({"procure_method": "make_to_stock"})
        cls._update_qty_in_location(cls.wh.lot_stock_id, cls.product1, 100)
        cls._update_qty_in_location(cls.wh.lot_stock_id, cls.product2, 100)
        cls.channel.picking_ids.move_ids._compute_ordered_available_to_promise()
        cls.channel.picking_ids.release_available_to_promise()
        cls.dock = cls.env.ref("shipment_advice.stock_dock_demo")
        cls.dock.warehouse_id = cls.wh
        cls.warehouse2 = cls.env.ref("stock.stock_warehouse_shop0")
        cls.channel.dock_id = cls.dock
        cls.channel.auto_deliver = True
        cls.channel.action_lock()
        cls.channel.shipment_planning_method = "simple"
        cls.internal_pickings = (
            cls.channel.picking_ids.move_ids.move_orig_ids.picking_id.filtered(
                lambda p: p.picking_type_code == "internal"
            )
        )
        cls.pickings = cls.channel.picking_ids.filtered(
            lambda p: p.picking_type_code == "outgoing"
        )

    @classmethod
    def _do_internal_pickings(cls):
        for picking in cls.internal_pickings:
            cls._do_picking(picking)

    @classmethod
    def _do_picking(cls, picking):
        if picking.state != "assigned":
            return
        for move in picking.move_ids:
            move.quantity_done = move.product_qty
        picking._action_done()
