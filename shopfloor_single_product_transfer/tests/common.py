# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.shopfloor.tests.common import CommonCase as BaseCommonCase


class CommonCase(BaseCommonCase):
    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "single_product_transfer", menu=self.menu, profile=self.profile
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cache_existing_record_ids()

    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref(
            "shopfloor_single_product_transfer.shopfloor_menu_demo_single_product_transfer"
        )
        cls.profile = cls.env.ref("shopfloor.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.other_picking_type = cls.env.ref(
            "shopfloor.picking_type_location_content_transfer_demo"
        )
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # cls.packing_location.sudo().active = True
        cls.location_src = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.env.ref("stock.stock_location_company")
        cls.location_customer = cls.env.ref("stock.stock_location_suppliers")
        cls.child_location = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "location_id": cls.location_src.id,
                    "name": "Child Location",
                    "barcode": "CLN",
                }
            )
        )

    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True, assign=True):
        picking = super()._create_picking(
            picking_type=picking_type, lines=lines, confirm=confirm
        )
        if assign:
            picking.action_assign()
        cls.cache_existing_record_ids()
        return picking

    @classmethod
    def cache_existing_record_ids(cls):
        # store ids of pickings, moves and move lines already created before
        # tests are run.
        cls.existing_picking_ids = cls.env["stock.picking"].search([]).ids
        cls.existing_move_ids = cls.env["stock.move"].search([]).ids
        cls.existing_move_line_ids = cls.env["stock.move.line"].search([]).ids

    @classmethod
    def _add_stock_to_product(cls, product, location, qty, lot=None):
        """Set the stock quantity of the product."""
        values = {
            "product_id": product.id,
            "location_id": location.id,
            "inventory_quantity": qty,
        }
        if lot:
            values["lot_id"] = lot.id
        cls.env["stock.quant"].sudo().with_context(inventory_mode=True).create(values)
        cls.cache_existing_record_ids()

    @classmethod
    def _create_lot_for_product(cls, product, name):
        return cls.env["stock.production.lot"].create(
            {
                "product_id": product.id,
                "name": name,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _set_product_tracking_by_lot(cls, product):
        product.tracking = "lot"

    @classmethod
    def _enable_create_move_line(cls):
        cls.menu.sudo().allow_move_create = True

    @classmethod
    def _enable_unreserve_other_moves(cls):
        cls.menu.sudo().allow_unreserve_other_moves = True

    @classmethod
    def _enable_ignore_no_putaway_available(cls):
        cls.menu.sudo().ignore_no_putaway_available = True

    @classmethod
    def _enable_no_prefill_qty(cls):
        cls.menu.sudo().no_prefill_qty = True

    # Data methods

    def _data_for_location(self, location):
        return self.data.location(location, with_operation_progress=True)

    def _data_for_move_line(self, move_line):
        return self.data.move_line(move_line)

    def _data_for_package(self, package, with_operation_progress_src=False):
        if with_operation_progress_src:
            return self.data.package(
                package, with_operation_progress_src=with_operation_progress_src
            )
        return self.data.package(package)

    @classmethod
    def get_new_move_line(cls):
        return cls.env["stock.move.line"].search(
            [("id", "not in", cls.existing_move_line_ids)]
        )

    @classmethod
    def get_new_picking(cls):
        return cls.env["stock.picking"].search(
            [("id", "not in", cls.existing_picking_ids)]
        )

    @classmethod
    def get_new_move(cls):
        return cls.env["stock.move"].search([("id", "not in", cls.existing_move_ids)])
