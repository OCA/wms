# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import CommonCase

# pylint: disable=missing-return


class LocationContentTransferCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref(
            "shopfloor.shopfloor_menu_demo_location_content_transfer"
        )
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.product_e = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product E",
                    "type": "product",
                    "default_code": "E",
                    "barcode": "E",
                    "weight": 3,
                }
            )
        )
        cls.product_e_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_e.id,
                    "barcode": "ProductEBox",
                }
            )
        )
        cls.content_loc = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Content Location",
                    "barcode": "Content",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        # This is an additional content location to manage the cases
        # where a product can be stored in several locations
        cls.content_loc_1 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Content Location 1",
                    "barcode": "Content1",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "location_content_transfer", menu=self.menu, profile=self.profile
        )
        self.stock_action = self.service._actions_for("stock")

    def _simulate_selected_move_line(self, move_line):
        """Mark the move line as picked (as it's done into the scan_location method)"""
        self.stock_action.mark_move_line_as_picked(move_line)

    @classmethod
    def _simulate_pickings_selected(cls, pickings):
        """Create a state as if pickings has been selected

        ... during a Location content transfer.

        It means a user scanned the location with the pickings. They are:

        * assigned to the user
        * the qty_done of all their move lines is set to they reserved qty

        """
        pickings.user_id = cls.env.uid
        for line in pickings.mapped("move_line_ids"):
            line.qty_done = line.reserved_uom_qty

    def assert_response_start(self, response, message=None, popup=None):
        self.assert_response(
            response, next_state="scan_location", message=message, popup=popup
        )

    def _assert_response_scan_destination_all(
        self, state, response, pickings, message=None, confirmation_required=None
    ):
        # this code is repeated from the implementation, not great, but we
        # mostly want to ensure the selection of pickings is right, and the
        # data methods have their own tests
        move_lines = pickings.move_line_ids
        lines = move_lines.filtered(lambda line: not line.package_level_id)
        package_levels = pickings.package_level_ids
        location = move_lines.location_id
        self.assert_response(
            response,
            next_state=state,
            data={
                "move_lines": self.data.move_lines(lines),
                "package_levels": self.data.package_levels(package_levels),
                "location": self.data.location(location),
                "confirmation_required": confirmation_required,
            },
            message=message,
        )

    def assert_response_scan_destination_all(
        self, response, pickings, message=None, confirmation_required=None
    ):
        self._assert_response_scan_destination_all(
            "scan_destination_all",
            response,
            pickings,
            message=message,
            confirmation_required=confirmation_required,
        )

    def assert_response_start_single(
        self, response, pickings, message=None, popup=None, postponed=False
    ):
        """

            This will check if the line returned correspond to the
            next operation to do

        :param response: The response returned by the service
        :type response: dict
        :param pickings: Pickings to check (recordset)
        :type pickings: stock.picking
        :param message: The message returned in the response, defaults to None
        :type message: dict, optional
        :param popup: The popup message returned to the operator, defaults to None
        :type popup: dict, optional
        :param postponed: Fill in this in order to check if the returned line
        should be the first one or the next one, defaults to False
        :type postponed: bool, optional
        """
        sorter = self.service._actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        location = pickings.mapped("location_id")
        if postponed:
            next(sorter)
        self.assert_response(
            response,
            next_state="start_single",
            data=self.service._data_content_line_for_location(location, next(sorter)),
            message=message,
            popup=popup,
        )

    def _assert_response_scan_destination(
        self, state, response, next_content, message=None, confirmation_required=None
    ):
        location = next_content.location_id
        data = self.service._data_content_line_for_location(location, next_content)
        data["confirmation_required"] = confirmation_required
        self.assert_response(
            response,
            next_state=state,
            data=data,
            message=message,
        )

    def assert_response_scan_destination(
        self, response, next_content, message=None, confirmation_required=None
    ):
        self._assert_response_scan_destination(
            "scan_destination",
            response,
            next_content,
            message=message,
            confirmation_required=confirmation_required,
        )
