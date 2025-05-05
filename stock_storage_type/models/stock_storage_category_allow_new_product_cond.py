# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

from odoo import _, exceptions, models
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class StockStorageCategoryAllowNewProductCond(models.Model):
    _inherit = "stock.storage.condition.mixin"
    _name = "stock.storage.category.allow_new_product.cond"
    _description = "Stock Storage Category Allow New Product Condition"

    _sql_constraints = [
        (
            "name",
            "EXCLUDE (name WITH =) WHERE (active = True)",
            "Storage Category Allow New Product Condition name must be unique",
        )
    ]

    def _default_code_snippet_docs(self):
        return """
        Available vars:
        * condition (recordset)
        * storage_category (recordset)
        * product (recordset)
        * package_type (recordset)
        * package (recordset)
        * quants (recordset)
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
        storage_category,
        product,
        package_type,
        package,
        quants,
    ):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        self.ensure_one()
        return {
            "env": self.env,
            "user": self.env.user,
            "condition": self,
            "storage_category": storage_category,
            "product": product,
            "package_type": package_type,
            "package": package,
            "quants": quants,
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "exceptions": safe_eval.wrap_module(
                exceptions, ["UserError", "ValidationError"]
            ),
        }

    def _exec_code(
        self,
        storage_category,
        product,
        package_type,
        package,
        quants,
    ):
        self.ensure_one()
        if not self._code_snippet_valued():
            return False
        eval_ctx = self._get_code_snippet_eval_context(
            storage_category,
            product,
            package_type,
            package,
            quants,
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
                "* storage_category: %s\n"
                "* product: %s\n"
                "* package_type: %s\n"
                "* package: %s\n"
                "* quants: %s\n",
                self.name,
                storage_category.ids,
                package_type and package_type.id or None,
                package and package.id or None,
                product.id,
                quants and quants.ids or None,
            )
        return result

    def evaluate(
        self,
        storage_category,
        product,
        package_type,
        package,
        quants,
    ):
        self.ensure_one()
        if self.condition_type == "code":
            return self._exec_code(
                storage_category,
                product,
                package_type,
                package,
                quants,
            )
        condition_type = self.condition_type
        raise exceptions.UserError(
            _(f"Not able to evaluate condition of type {condition_type}")
        )
