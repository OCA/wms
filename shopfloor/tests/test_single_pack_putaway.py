from odoo.tests.common import Form

from .common import CommonCase


class PutawayCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.stock_location = stock_location
        out_location = cls.env["stock.location"].search(
            [
                ("location_id", "=", stock_location.id),
                ("barcode", "!=", False),
                ("usage", "=", "internal"),
            ]
        )[0]
        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.packA = cls.env["stock.quant.package"].create(
            {"location_id": stock_location.id}
        )
        cls.quantA = cls.env["stock.quant"].create(
            {
                "product_id": cls.productA.id,
                "location_id": stock_location.id,
                "quantity": 1,
                "package_id": cls.packA.id,
            }
        )
        cls.env["stock.putaway.rule"].create(
            {
                "product_id": cls.productA.id,
                "location_in_id": stock_location.id,
                "location_out_id": out_location.id,
            }
        )
        cls.shelf1 = cls.env.ref("stock.stock_location_components")
        cls.shelf2 = cls.env.ref("stock.stock_location_14")
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_put_away_reach_truck")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.wh.int_type_id.process_id = cls.menu.process_id.id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="single_pack_putaway")

    def test_single_pack_putaway(self):
        barcode = self.packA.name
        params = {"barcode": barcode}
        response = self.service.dispatch("start", params=params)
        package_level = self.env["stock.package_level"].browse(response["data"]["id"])
        move_id = package_level.move_line_ids[0].move_id.id
        location_dest = self.env["stock.location"].browse(
            response["data"]["location_dst"]["id"]
        )
        params = {
            "package_level_id": package_level.id,
            "location_barcode": location_dest.barcode,
        }
        new_loc_quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.productA.id),
                ("location_id", "=", location_dest.id),
            ]
        )
        self.assertFalse(new_loc_quant)
        response = self.service.dispatch("validate", params=params)
        new_loc_quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.productA.id),
                ("location_id", "=", location_dest.id),
            ]
        )
        move = self.env["stock.move"].browse(move_id)
        self.assertEquals(move.state, "done")
        self.assertEquals(self.quantA.quantity, 0)
        self.assertEquals(new_loc_quant.quantity, move.product_uom_qty)

    def test_validate(self):
        # setup the picking as we need, like if the move line
        # was already started by the first step (start operation)
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.wh.int_type_id
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.productA
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        package_level = picking.move_line_ids.package_level_id
        self.assertEqual(package_level.package_id, self.packA)
        # at this point, the package level is already set to "done", by the
        # "start" method of the pack transfer putaway
        package_level.is_done = True

        # now, call the service to proceed with validation of the
        # movement
        response = self.service.dispatch(
            "validate",
            params={
                "package_level_id": package_level.id,
                "location_barcode": self.shelf2.barcode,
            },
        )
        self.assertDictEqual(
            response,
            {
                "message": {
                    "message": "The pack has been moved," " you can scan a new pack.",
                    "message_type": "info",
                    "title": "Start",
                },
                "state": "start",
            },
        )

        self.assertRecordValues(
            package_level.move_line_ids,
            [{"qty_done": 1.0, "location_dest_id": self.shelf2.id, "state": "done"}],
        )
        self.assertRecordValues(
            package_level.move_line_ids.move_id,
            [{"location_dest_id": self.stock_location.id, "state": "done"}],
        )
