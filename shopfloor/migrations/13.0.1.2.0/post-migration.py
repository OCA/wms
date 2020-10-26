# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger("shopfloor." + __name__)


def _compute_logs_new_values(env):
    log_entries = env["shopfloor.log"].search([])
    for entry in log_entries:
        new_vals = {}
        for fname in ("params", "headers", "result"):
            if not entry[fname]:
                continue
            # make it json-like
            replace_map = [
                ("{'", '{"'),
                ("'}", '"}'),
                ("':", '":'),
                (": '", ': "'),
                ("',", '",'),
                (", '", ', "'),
                ("False", "false"),
                ("True", "true"),
                ("None", "null"),
                ("\\xa0", " "),
            ]
            json_val = entry[fname]
            for to_replace, replace_with in replace_map:
                json_val = json_val.replace(to_replace, replace_with)
            try:
                val = json.loads(json_val)
            except Exception:
                # fail gracefully and do not break the whole thing
                # just for not being able to convert a value.
                # We don't use these values as json yet, no harm.
                _logger.warning(
                    "`%s` JSON convert failed for record %d", (fname, entry.id)
                )
            else:
                new_vals[fname] = json.dumps(val, indent=4, sort_keys=True)
        if entry.error and not entry.exception_name:
            exception_details = _get_exception_details(entry)
            if exception_details:
                new_vals.update(exception_details)
        entry.write(new_vals)


def _get_exception_details(entry):
    for line in reversed(entry.error.splitlines()):
        if "Error:" in line:
            name, msg = line.split(":", 1)
            return {
                "exception_name": name.strip(),
                "exception_message": msg.strip("() "),
            }


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _compute_logs_new_values(env)
