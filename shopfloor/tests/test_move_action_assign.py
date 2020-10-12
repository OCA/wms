# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import CommonCase


class TestStockMoveActionAssign(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.wh = cls.env.ref("stock.warehouse0")

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"

    def test_action_assign_package_level(self):
        """calling _action_assign on move does not erase lines' "result_package_id"

        At the end of the method ``StockMove._action_assign()``, the method
        ``StockPicking._check_entire_pack()`` is called. This method compares
        the move lines with the quants of their source package, and if the entire
        package is moved at once in the same transfer, a ``stock.package_level`` is
        created. On creation of a ``stock.package_level``, the result package of
        the move lines is directly updated with the entire package.

        This is good on the first assign of the move, but when we call assign for
        the second time on a move, for instance because it was made partially available
        and we want to assign the remaining, it can override the result package we
        selected before.

        An override of ``StockPicking._check_move_lines_map_quant_package()`` ensures
        that we ignore:

        * picked lines (qty_done > 0)
        * lines with a different result package already
        """
        package = self.env["stock.quant.package"].create({"name": "Src Pack"})
        dest_package1 = self.env["stock.quant.package"].create({"name": "Dest Pack1"})

        picking = self._create_picking(
            picking_type=self.wh.pick_type_id, lines=[(self.product_a, 50)]
        )
        self._update_qty_in_location(
            picking.location_id, self.product_a, 20, package=package
        )
        picking.action_assign()

        self.assertEqual(picking.state, "assigned")
        self.assertEqual(picking.package_level_ids.package_id, package)

        move = picking.move_lines
        line = move.move_line_ids

        # we are no longer moving the entire package
        line.qty_done = 20
        line.result_package_id = dest_package1

        # create remaining quantity
        new_package = self.env["stock.quant.package"].create({"name": "New Pack"})
        self._update_qty_in_location(
            picking.location_id, self.product_a, 30, package=new_package
        )

        move._action_assign()
        new_line = move.move_line_ids - line

        # At the end of _action_assign(), StockPicking._check_entire_pack() is
        # called, which, by default, look the sum of the move lines qties, and
        # if they match a package, it:
        #
        # * creates a package level
        # * updates all the move lines result package with the package,
        #   including the 'done' lines
        #
        # These checks ensure that we prevent this to happen if we already set
        # a result package.
        self.assertRecordValues(
            line + new_line,
            [
                {"qty_done": 20, "result_package_id": dest_package1.id},
                {"qty_done": 0, "result_package_id": new_package.id},
            ],
        )
