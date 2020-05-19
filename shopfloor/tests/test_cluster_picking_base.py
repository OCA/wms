from .common import CommonCase, PickingBatchMixin


class ClusterPickingCommonCase(CommonCase, PickingBatchMixin):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.picking_type = cls.menu.picking_type_ids

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="cluster_picking")

    @classmethod
    def _simulate_batch_selected(
        cls, batches, in_package=False, in_lot=False, fill_stock=True
    ):
        """Create a state as if a batch was selected by the user

        * The picking batch is in progress
        * It is assigned to the current user
        * All the move lines are available

        Note: currently, this method create a source package that contains
        all the products of the batch. It is enough for the current tests.
        """
        pickings = batches.mapped("picking_ids")
        if fill_stock:
            cls._fill_stock_for_moves(
                pickings.mapped("move_lines"), in_package=in_package, in_lot=in_lot
            )
        pickings.action_assign()
        batches.write({"state": "in_progress", "user_id": cls.env.uid})

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
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # quants already existing are from demo data
        cls.env["stock.quant"].search(
            [("location_id", "=", cls.stock_location.id)]
        ).unlink()
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )

    def _line_data(self, move_line, qty=1.0):
        # just force qty to 1.0
        return super()._line_data(move_line, qty=qty)
