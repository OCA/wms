from .common import CommonCase


class PutawayCase(CommonCase):

    def setUp(self, *args, **kwargs):
        super(PutawayCase, self).setUp(*args, **kwargs)
        in_location = self.env.ref('stock.stock_location_company').child_ids[0]
        stock_location = self.env.ref('stock.stock_location_stock')
        self.productA = self.env['product.product'].create({'name': 'Product A', 'type': 'product'})
        self.packA = self.env['stock.quant.package'].create({
            'location_id': in_location.id
        })
        self.quantA = self.env['stock.quant'].create({
            'product_id': self.productA.id,
            'location_id': in_location.id,
            'quantity': 1,
            'package_id': self.packA.id,
        })
        self.env['stock.putaway.rule'].create({
            'product_id': self.productA.id,
            'location_in_id': stock_location.id,
            'location_out_id': stock_location.child_ids[0].id,
            })
        with self.work_on_services(
        ) as work:
            self.service = work.component(usage="shopfloor")

    def test_scan_pack(self):
        pack_name = self.packA.name
        params = {
            'pack_name': pack_name,
        }
        response = self.service.dispatch("scan_pack", params=params)
        move_id = response['move_id']
        params ={
            'move_id': move_id,
            'location_name': response['location_dest_name'],
        }
        location_dest_id = self.env['stock.location'].search([
            ('name', '=', params['location_name'])
        ]).id
        new_loc_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.productA.id),
            ('location_id', '=', location_dest_id)
        ])
        self.assertFalse(new_loc_quant)
        response = self.service.dispatch("validate", params=params)
        new_loc_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.productA.id),
            ('location_id', '=', location_dest_id)
        ])
        move = self.env['stock.move'].browse(move_id)
        self.assertEquals(move.state, 'done')
        self.assertEquals(self.quantA.quantity, 0)
        self.assertEquals(new_loc_quant.quantity, move.product_uom_qty)
