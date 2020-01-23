from .common import CommonCase


class PutawayCase(CommonCase):
    def setUp(self, *args, **kwargs):
        super(PutawayCase, self).setUp(*args, **kwargs)
        stock_location = self.env.ref("stock.stock_location_stock")
        out_location = self.env["stock.location"].search(
            [
                ("location_id", "=", stock_location.id),
                ("barcode", "!=", False),
                ("usage", "=", "internal"),
            ]
        )[0]
        self.productA = self.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        self.packA = self.env["stock.quant.package"].create(
            {"location_id": stock_location.id}
        )
        self.quantA = self.env["stock.quant"].create(
            {
                "product_id": self.productA.id,
                "location_id": stock_location.id,
                "quantity": 1,
                "package_id": self.packA.id,
            }
        )
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.productA.id,
                "location_in_id": stock_location.id,
                "location_out_id": out_location.id,
            }
        )
        menu = self.env.ref("shopfloor.shopfloor_menu_put_away_reach_truck")
        profile = self.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        profile.warehouse_id.int_type_id.process_id = menu.process_id.id
        with self.work_on_services(menu=menu, profile=profile) as work:
            self.service = work.component(usage="single_pack_putaway")

    def test_scan_pack(self):
        barcode = self.packA.name
        params = {"barcode": barcode}
        response = self.service.dispatch("scan", params=params)
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
