# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

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

        return self._response_for_select_move(picking=pickings, shipment=shipment)

    def _scan_document__get_handlers_by_type(self):
        res = super()._scan_document__get_handlers_by_type()
        res["shipment"] = self._scan_document__by_shipment
        res["dock"] = self._scan_document__by_dock
        return res

    def _response_for_select_move_get_data(self, picking, **kwargs):
        data = {}
        if picking:
            data = super()._response_for_select_move_get_data(picking)
        if "shipment" in kwargs.keys():
            data["shipment"] = self.data_detail.shipment_advice_detail(
                kwargs["shipment"]
            )
            data.pop("picking", None)
        return data

    def _response_for_manual_selection_shipment(self, dock):
        shipments = self.env["shipment.advice"].search(
            [
                ("dock_id", "=", dock.id),
                ("state", "in", ["in_progress", "confirmed"]),
                ("warehouse_id", "in", self.picking_types.warehouse_id.ids),
            ]
        )
        data = {
            "dock": self.data.dock(dock),
            "shipments": [
                self.data.shipment_advice(shipment) for shipment in shipments
            ],
        }
        return self._response(next_state="manual_selection_shipment", data=data)

    def _scan_line_shipment__by_product(self, shipment, product):
        moves = shipment.planned_move_ids.filtered(lambda m: m.product_id == product)
        # TODO probably should check if still all available...
        move = fields.first(moves)
        message = self._check_move_available(move, "product")
        picking = move.picking_id
        if message:
            return self._response_for_select_move(
                picking, message=message, shipment=shipment
            )
        return self._scan_line__find_or_create_line(picking, move)

    def _scan_line_shipment__by_packaging(self, shipment, packaging):
        moves = shipment.planned_move_ids.filtered(
            lambda m: packaging in m.product_id.packaging_ids
        )
        # TODO probably should check if still all available...
        move = fields.first(moves)
        message = self._check_move_available(move, "product")
        picking = move.picking_id
        if message:
            return self._response_for_select_move(
                picking, message=message, shipment=shipment
            )
        return self._scan_line__find_or_create_line(picking, move)

    def scan_line(self, picking_id, barcode, **kwargs):
        if "shipment_id" not in kwargs:
            return super().scan_line(picking_id, barcode, **kwargs)
        shipment = self.env["shipment.advice"].browse(kwargs["shipment_id"])
        # check shipment status ?
        if not shipment:
            return super().scan_line(picking_id, barcode, **kwargs)
        handlers_by_type = {
            "product": self._scan_line_shipment__by_product,
            "packaging": self._scan_line_shipment__by_packaging,
            # "lot": self._scan_line__by_lot,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, handlers_by_type.keys())
        # Fallback handler, returns a barcode not found error
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(shipment, search_result.record)
        # return self._scan_line__fallback(picking, barcode)
        message = self.msg_store.barcode_not_found()
        return self._response_for_select_move(None, shipment=shipment, message=message)


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
