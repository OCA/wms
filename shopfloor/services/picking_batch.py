# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.osv import expression

from odoo.addons.component.core import Component


class PickingBatch(Component):
    """Picking Batch services for the client application."""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.picking.batch"
    _usage = "picking_batch"
    _expose_model = "stock.picking.batch"
    _description = __doc__

    def _get_base_search_domain(self):
        base_domain = super()._get_base_search_domain()
        user = self.env.user
        return expression.AND(
            [
                base_domain,
                [
                    "|",
                    "&",
                    ("user_id", "=", False),
                    ("state", "=", "draft"),
                    "&",
                    ("user_id", "=", user.id),
                    ("state", "in", ("draft", "in_progress")),
                ],
            ]
        )

    def _search(self, name_fragment=None, batch_ids=None):
        domain = self._get_base_search_domain()
        if name_fragment:
            domain = expression.AND([domain, [("name", "ilike", name_fragment)]])
        if batch_ids:
            domain = expression.AND([domain, [("id", "in", batch_ids)]])
        records = self.env[self._expose_model].search(domain, order="id asc")
        records = records.filtered(
            # Include done/cancel because we want to be able to work on the
            # batch even if some pickings are done/canceled. They'll should be
            # ignored later.
            lambda batch: all(
                (
                    # When the batch is already in progress, we do not care
                    # about state of the pickings, because we want to be able
                    # to recover it in any case, even if, for instance, a stock
                    # error changed a picking to unavailable after the user
                    # started to work on the batch.
                    batch.state == "in_progress"
                    or picking.state in ("assigned", "done", "cancel")
                )
                and picking.picking_type_id in self.picking_types
                for picking in batch.picking_ids
            )
        )
        return records

    def search(self, name_fragment=None):
        """List available stock picking batches for current user

        Show only picking batches where all the pickings are available and
        where all pickings are in the picking type of the current scenario.
        """
        records = self._search(name_fragment=name_fragment)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
        )

    def _convert_one_record(self, record):
        assigned_pickings = record.picking_ids.filtered(
            lambda picking: picking.state == "assigned"
        )
        return {
            "id": record.id,
            "name": record.name,
            "picking_count": len(assigned_pickings),
            "move_line_count": len(assigned_pickings.mapped("move_line_ids")),
            "weight": record.total_weight(),
        }


class ShopfloorPickingBatchValidator(Component):
    """Validators for the Picking_Batch endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.picking.batch.validator"
    _usage = "picking_batch.validator"

    def search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }


class ShopfloorPickingBatchValidatorResponse(Component):
    """Validators for the Picking_Batch endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.picking.batch.validator.response"
    _usage = "picking_batch.validator.response"

    def search(self):
        return self._response_schema(
            {
                "size": {"required": True, "type": "integer"},
                "records": {
                    "type": "list",
                    "required": True,
                    "schema": {"type": "dict", "schema": self._record_schema},
                },
            }
        )

    @property
    def _record_schema(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "picking_count": {"required": True, "type": "integer"},
            "move_line_count": {"required": True, "type": "integer"},
            "weight": {"required": True, "nullable": True, "type": "float"},
        }
