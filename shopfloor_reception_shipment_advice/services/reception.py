# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    # Recover from the header the current shipment ID being worked on.
    #
    # If the move being received was choosen from a shipment advice when
    # redirected back to a move selection, this allows to display the shipment
    # advice related data.

    @property
    def _validation_rules(self):
        return super()._validation_rules + (
            (self.SHIPMENT_ID_HEADER_RULE, self._is_active_header_shipment),
        )

    SHIPMENT_ID_HEADER_RULE = (
        # header name, coerce func, ctx handler, mandatory
        "HTTP_SERVICE_CTX_SHIPMENT_ID",
        int,
        "_work_ctx_get_shipment_id",
        False,
    )

    def _work_ctx_get_shipment_id(self, rec_id):
        return (
            "current_shipment_advice",
            self.env["shipment.advice"].browse(rec_id).exists(),
        )

    def _is_active_header_shipment(self, request, method):
        return True

    @property
    def shipment_advice(self):
        if hasattr(self.work, "current_shipment_advice"):
            return self.work.current_shipment_advice
        return self.env["shipment.advice"]

    def _domain_shipment_advice(self, dock, today_only=False):
        domain = [
            ("state", "in", ["in_progress", "confirmed"]),
            ("warehouse_id", "in", self.picking_types.warehouse_id.ids),
            ("shipment_type", "=", "incoming"),
        ]
        if dock:
            domain.append(("dock_id", "=", dock.id))
        if today_only:
            today_start, today_end = self._get_today_start_end_datetime()
            domain.append(("arrival_date", ">=", today_start))
            domain.append(("arrival_date", "<=", today_end))
        return domain

    def _scan_document__by_dock(self, dock, barcode):
        if not dock:
            return
        return self._response_for_manual_selection_shipment(dock)

    def _scan_document__by_shipment(self, shipment, barcode):
        if not shipment:
            return
        if shipment.shipment_type != "incoming":
            return self._response_for_select_document(
                message=self.msg_store.shipment_incoming_type_only()
            )
        if shipment.state not in ["confirmed", "in_progress"]:
            return self._response_for_select_document(
                message=self.msg_store.shipment_not_ready(shipment)
            )
        planned_pickings = shipment.planned_picking_ids
        pickings = planned_pickings.filtered(
            lambda p: p.picking_type_id.id in self.picking_types.ids
        )
        if not pickings:
            return self._response_for_select_document(
                message=self.msg_store.shipment_nothing_to_unload(shipment)
            )
        self.work.current_shipment_advice = shipment
        return self._response_for_select_move(picking=pickings)

    def _scan_document__get_handlers_by_type(self):
        res = super()._scan_document__get_handlers_by_type()
        res["shipment"] = self._scan_document__by_shipment
        res["dock"] = self._scan_document__by_dock
        return res

    def _response_for_select_move_get_data(self, picking):
        if not self.shipment_advice:
            return super()._response_for_select_move_get_data(picking)
        data = {}
        data["shipment"] = self.data_detail.shipment_advice_detail(self.shipment_advice)
        return data

    def _response_for_manual_selection_shipment(self, dock):
        shipments = self.env["shipment.advice"].search(
            self._domain_shipment_advice(dock=dock, today_only=True),
            order="arrival_date desc",
        )
        data = {
            "dock": self.data.dock(dock),
            "shipments": [
                self.data.shipment_advice(shipment) for shipment in shipments
            ],
        }
        return self._response(next_state="manual_selection_shipment", data=data)

    def _select_move_to_work_on(self, moves, message_code="product"):
        """Select a move with still some quantity to process.

        When working from shipment advice, there can be multiple moves selected for
        the same barcode.
        """
        message = None
        for move in moves:
            message = self._check_move_available(move, message_code)
            if not message:
                # Found a move that can be worked on
                return move, message
        move = fields.first(moves)
        return move, self._check_move_available(move, message_code)

    def _scan_line_shipment__response(self, move, message):
        picking = move.picking_id
        if message:
            return self._response_for_select_move(picking, message=message)
        return self._scan_line__find_or_create_line(picking, move)

    def _scan_line_shipment__by_product(self, shipment, product):
        moves = shipment.planned_move_ids.filtered(lambda m: m.product_id == product)
        move, message = self._select_move_to_work_on(moves, "product")
        return self._scan_line_shipment__response(move, message)

    def _scan_line_shipment__by_packaging(self, shipment, packaging):
        moves = shipment.planned_move_ids.filtered(
            lambda m: packaging in m.product_id.packaging_ids
        )
        move, message = self._select_move_to_work_on(moves, "package")
        return self._scan_line_shipment__response(move, message)

    def _check_shipment_status(self, shipment):
        # TODO check if the shipment is still workable ?
        return False

    def scan_line(self, picking_id, barcode, **kwargs):
        message = None
        if "shipment_id" not in kwargs:
            return super().scan_line(picking_id, barcode, **kwargs)
        shipment = self.env["shipment.advice"].browse(kwargs["shipment_id"])
        if not shipment:
            message = self.msg_store.shipment_not_found()
        else:
            message = self._check_shipment_status(shipment)
        if message:
            # Shipment is not workable anymore
            return self._response_for_select_document()
        handlers_by_type = {
            "product": self._scan_line_shipment__by_product,
            "packaging": self._scan_line_shipment__by_packaging,
            # "lot": self._scan_line__by_lot,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(shipment, search_result.record)
        message = self.msg_store.barcode_not_found()
        return self._response_for_select_move(None, message=message)


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def scan_line(self):
        res = super().scan_line()
        res["shipment_id"] = {"coerce": to_int, "required": False, "type": "integer"}
        res["picking_id"]["required"] = False
        res["picking_id"]["nullable"] = True
        return res


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    @property
    def _schema_select_move(self):
        schema = super()._schema_select_move
        schema["shipment"] = self.schemas._schema_dict_of(
            self.schemas_detail.shipment_advice_detail(), required=False
        )
        return schema

    def _states(self):
        res = super()._states()
        res["manual_selection_shipment"] = self._schema_manual_selection_shipment
        return res

    def _scan_document_next_states(self):
        res = super()._scan_document_next_states()
        res.add("manual_selection_shipment")
        return res

    @property
    def _schema_manual_selection_shipment(self):
        return {
            "dock": {
                "type": "dict",
                "nullable": False,
                "schema": self.schemas.dock(),
            },
            "shipments": self.schemas._schema_list_of(self.schemas.shipment_advice()),
        }
