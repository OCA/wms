# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import textwrap

from odoo import _, api, exceptions, fields, models


class StockStorageConditionMixin(models.AbstractModel):
    _name = "stock.storage.condition.mixin"
    _description = "Mixin to implement storage condition."

    name = fields.Char(required=True)
    condition_type = fields.Selection(
        selection=[("code", "Execute code")], default="code", required=True
    )
    code_snippet = fields.Text(required=True)
    code_snippet_docs = fields.Text(
        compute="_compute_code_snippet_docs",
        default=lambda self: self._default_code_snippet_docs(),
    )
    active = fields.Boolean(default=True)

    @api.constrains("condition_type", "code_snippet")
    def _check_condition_type_code(self):
        for rec in self.filtered(lambda c: c.condition_type == "code"):
            if not rec._code_snippet_valued():
                raise exceptions.UserError(
                    _(
                        "Condition type is set to `Code`: "
                        "you must provide a piece of code"
                    )
                )

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

    def _compute_code_snippet_docs(self):
        for rec in self:
            rec.code_snippet_docs = textwrap.dedent(rec._default_code_snippet_docs())

    def _default_code_snippet_docs(self):
        """Return the documentation (e.g. available variables) for `code_snippet`."""
        raise NotImplementedError

    def _get_code_snippet_eval_context(self, *args, **kwargs):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        raise NotImplementedError

    def _exec_code(self, *args, **kwargs):
        raise NotImplementedError

    def evaluate(self, *args, **kwargs):
        """Evaluate and return the result of the condition."""
        raise NotImplementedError
