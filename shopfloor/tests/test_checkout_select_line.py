# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutSelectLineCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        cls.moves_pack = picking.move_lines[:2]
        cls.move_single = picking.move_lines[2:]
        cls._fill_stock_for_moves(cls.moves_pack, in_package=True)
        cls._fill_stock_for_moves(cls.move_single)
        picking.action_assign()
        cls.picking = picking

    def test_select_line_package_ok(self):
        selected_lines = self.moves_pack.move_line_ids
        # we want to check that when we give the package id, we get
        # all its move lines
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "package_id": selected_lines.package_id.id,
            },
        )
        self._assert_selected(response, selected_lines)

    def test_select_line_no_package_disabled(self):
        selected_lines = self.moves_pack.move_line_ids
        self.service.work.options = {"checkout__disable_no_package": True}
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "package_id": selected_lines.package_id.id,
            },
        )
        self._assert_selected(response, selected_lines, no_package_enabled=False)

    def test_select_line_move_line_package_ok(self):
        selected_lines = self.moves_pack.move_line_ids
        # When we select a single line but the line is part of a package,
        # we select all the lines. Note: not really supposed to happen as
        # the client application should use send a package id when there is
        # a package and use the move line id only for lines without package
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "move_line_id": selected_lines[0].id,
            },
        )
        self._assert_selected(response, selected_lines)

    def test_select_line_move_line_ok(self):
        selected_lines = self.move_single.move_line_ids
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "move_line_id": selected_lines[0].id,
            },
        )
        self._assert_selected(response, selected_lines)

    def _test_select_line_error(self, params, message):
        """Test errors for /select_line

        :param params: params sent to /select_line
        :param message: the dict of expected error message
        """
        response = self.service.dispatch("select_line", params=params)
        self.assert_response(
            response,
            next_state="select_line",
            data=self._data_for_select_line(self.picking),
            message=message,
        )

    def test_select_line_package_error_not_found(self):
        selected_lines = self.move_single.move_line_ids
        selected_lines.unlink()
        self._test_select_line_error(
            {"picking_id": self.picking.id, "package_id": selected_lines[0].id},
            {
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
        )

    def test_select_line_move_line_error_not_found(self):
        selected_lines = self.move_single.move_line_ids
        selected_lines.unlink()
        self._test_select_line_error(
            {"picking_id": self.picking.id, "move_line_id": selected_lines[0].id},
            {
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
        )

    def test_select_line_all_lines_done(self):
        # set all lines as done
        self.picking.move_line_ids.write(
            {"qty_done": 10.0, "shopfloor_checkout_done": True}
        )
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                # doesn't matter as all lines are done, we should be
                # redirected to the summary
                "package_id": self.picking.move_line_ids[0].package_id.id,
            },
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": True,
            },
        )
