from .common import CommonCase, PickingBatchMixin


class ClusterPickingCommonCase(CommonCase, PickingBatchMixin):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "default_code": "A",
                "barcode": "A",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "default_code": "B",
                "barcode": "B",
            }
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.picking_type = cls.process.picking_type_id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="cluster_picking")

    @classmethod
    def _simulate_batch_selected(cls, batches, in_package=False, in_lot=False):
        """Create a state as if a batch was selected by the user

        * The picking batch is in progress
        * It is assigned to the current user
        * All the move lines are available

        Note: currently, this method create a source package that contains
        all the products of the batch. It is enough for the current tests.
        """
        pickings = batches.mapped("picking_ids")
        cls._fill_stock_for_moves(
            pickings.mapped("move_lines"), in_package=in_package, in_lot=in_lot
        )
        pickings.action_assign()
        batches.write({"state": "in_progress", "user_id": cls.env.uid})

    def _line_data(self, move_line, qty=None):
        picking = move_line.picking_id
        batch = picking.batch_id
        # A package exists on the move line, because the quant created
        # by ``_simulate_batch_selected`` has a package.
        package = move_line.package_id
        lot = move_line.lot_id
        return {
            "id": move_line.id,
            "quantity": qty or move_line.product_uom_qty,
            "postponed": move_line.shopfloor_postponed,
            "location_dst": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "picking": {
                "id": picking.id,
                "name": picking.name,
                "note": "",
                "origin": picking.origin,
            },
            "batch": {"id": batch.id, "name": batch.name},
            "product": {
                "default_code": move_line.product_id.default_code,
                "display_name": move_line.product_id.display_name,
                "id": move_line.product_id.id,
                "name": move_line.product_id.name,
                "qty_available": move_line.product_id.qty_available,
            },
            "lot": {"id": lot.id, "name": lot.name, "ref": lot.ref or ""}
            if lot
            else None,
            "pack": {"id": package.id, "name": package.name} if package else None,
        }


class ClusterPickingAPICase(ClusterPickingCommonCase):
    """Base tests for the cluster picking API"""

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()


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
