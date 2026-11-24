# Copyright 2022 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, exceptions, models
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class StockStorageLocationSequenceCond(models.Model):
    _inherit = "stock.storage.condition.mixin"
    _name = "stock.storage.location.sequence.cond"
    _description = "Stock Storage Location Sequence Condition"

    _sql_constraints = [
        (
            "name",
            "EXCLUDE (name WITH =) WHERE (active = True)",
            "Stock storage location sequence condition name must be unique",
        )
    ]

    def _default_code_snippet_docs(self):
        return """
        Available vars:
        * storage_location_sequence
        * condition
        * putaway_location
        * quant (recordset)
        * package
        * product
        * quantity
        * env
        * datetime
        * dateutil
        * time
        * user
        * exceptions

        Must initialize a boolean 'result' variable set to True when condition is met

        """

    def _get_code_snippet_eval_context(
        self,
        storage_location_sequence,
        putaway_location,
        quant,
        package,
        product,
        quantity,
    ):
        """Prepare the context used when evaluating python code
        :returns: dict -- evaluation context given to safe_eval
        """
        self.ensure_one()
        return {
            "env": self.env,
            "user": self.env.user,
            "condition": self,
            "putaway_location": putaway_location,
            "quant": quant,
            "package": package,
            "product": product,
            "quantity": quantity,
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "storage_location_sequence": storage_location_sequence,
            "exceptions": safe_eval.wrap_module(
                exceptions, ["UserError", "ValidationError"]
            ),
        }

    def _exec_code(
        self,
        storage_location_sequence,
        putaway_location,
        quant,
        package,
        product,
        quantity,
    ):
        self.ensure_one()
        if not self._code_snippet_valued():
            return False
        eval_ctx = self._get_code_snippet_eval_context(
            storage_location_sequence,
            putaway_location,
            quant,
            package,
            product,
            quantity,
        )
        snippet = self.code_snippet
        safe_eval.safe_eval(snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result")
        if not isinstance(result, bool):
            raise exceptions.UserError(
                _("code_snippet should return boolean value into `result` variable.")
            )
        if not result:
            _logger.debug(
                "Condition %s not met:\n"
                "* putaway sequence: %s\n"
                "* putaway location: %s\n"
                "* quants: %s\n"
                "* package: %s\n"
                "* product: %s\n"
                "* quantity: %s\n"
                % (
                    self.name,
                    storage_location_sequence.id,
                    putaway_location.name,
                    quant.ids,
                    package.display_name,
                    product.display_name,
                    quantity,
                )
            )
        return result

    def _code_snippet_valued(self):
        self.ensure_one()
        snippet = self.code_snippet or ""
        return bool(
            [
                not line.startswith("#")
                for line in (snippet.splitlines())
                if line.strip("")
            ]
        )

    def evaluate(
        self,
        storage_location_sequence,
        putaway_location,
        quant,
        package,
        product,
        quantity,
    ):
        self.ensure_one()
        if self.condition_type == "code":
            return self._exec_code(
                storage_location_sequence,
                putaway_location,
                quant,
                package,
                product,
                quantity,
            )
        condition_type = self.condition_type
        raise exceptions.UserError(
            _(f"Not able to evaluate condition of type {condition_type}")
        )
