# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from psycopg2 import sql

from odoo.tools import column_exists


def migrate(cr, version):
    renames = (
        ("stock.move.line", "shopfloor_postponed", "shopfloor_priority"),
        ("stock.package.level", "shopfloor_postponed", "shopfloor_priority"),
    )
    for model, old_field, new_field in renames:
        table = model.replace(".", "_")
        if not column_exists(cr, table, old_field):
            continue
        # pylint: disable=sql-injection
        cr.execute(
            sql.SQL(
                """
                ALTER TABLE {}
                ALTER {}
                TYPE INTEGER
                USING CASE COALESCE({}, false)
                WHEN false THEN 10
                ELSE 9999
                END;
                """
            ).format(
                sql.Identifier(table),
                sql.Identifier(old_field),
                sql.Identifier(old_field),
            )
        )
        # pylint: disable=sql-injection
        cr.execute(
            sql.SQL(
                """
                ALTER TABLE {}
                RENAME {}
                TO {};
                """
            ).format(
                sql.Identifier(table),
                sql.Identifier(old_field),
                sql.Identifier(new_field),
            )
        )
        cr.execute(
            """
            UPDATE ir_model_fields
            SET name = %s
            WHERE name = %s
                AND model = %s
            """,
            (new_field, old_field, model),
        )
        cr.execute(
            """
            UPDATE ir_model_data
            SET name = %s
            WHERE name = %s
                AND model = %s
            """,
            (
                "field_{}__{}".format(table, new_field),
                "field_{}__{}".format(table, old_field),
                model,
            ),
        )
        cr.execute(
            """
            UPDATE ir_translation
            SET name = %s
            WHERE name = %s
                AND type = 'model'
            """,
            ("{},{}".format(model, new_field), "{},{}".format(model, old_field)),
        )
