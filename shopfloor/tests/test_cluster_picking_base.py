# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import CommonCase, PickingBatchMixin


class ClusterPickingCommonCase(CommonCase, PickingBatchMixin):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_cluster_picking")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "cluster_picking", menu=self.menu, profile=self.profile
        )

    def _line_data(self, move_line, qty=None, package_dest=False):
        picking = move_line.picking_id
        # A package exists on the move line, because the quant created
        # by ``_simulate_batch_selected`` has a package.
        data = self.data.move_line(move_line)
        if not package_dest:
            data["package_dest"] = None
        if qty:
            data["quantity"] = qty
        data.update(
            {
                "batch": self.data.picking_batch(picking.batch_id),
                "picking": self.data.picking(picking),
            }
        )
        return data

    @classmethod
    def _set_dest_package_and_done(cls, move_lines, dest_package):
        """Simulate what would have been done in the previous steps"""
        for line in move_lines:
            line.write(
                {"qty_done": line.product_uom_qty, "result_package_id": dest_package.id}
            )

    def _data_for_batch(self, batch, location, pack=None):
        data = self.data.picking_batch(batch)
        data["location_dest"] = self.data.location(location)
        if pack:
            data["package"] = self.data.package(pack)
        return data


class ClusterPickingLineCommonCase(ClusterPickingCommonCase):
    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # quants already existing are from demo data
        cls.env["stock.quant"].sudo().search(
            [("location_id", "=", cls.stock_location.id)]
        ).unlink()
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )

    def _line_data(self, move_line, qty=1.0):
        # just force qty to 1.0
        return super()._line_data(move_line, qty=qty)
