# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api, fields

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_capacity_allow_new_product_to_category_allow_new_product_rules(env)


def migrate_capacity_allow_new_product_to_category_allow_new_product_rules(env):
    _logger.info(
        "Migrate '<capacity>.allow_new_product' values to "
        "category allow_new_product rules..."
    )
    query = """
        SELECT sscc.id, storage_category_id, sscc.allow_new_product, package_type_id
        FROM stock_storage_category_capacity sscc
        LEFT JOIN stock_storage_category ssc
            ON sscc.storage_category_id = ssc.id
        WHERE sscc.allow_new_product != ssc.allow_new_product;
    """
    env.cr.execute(query)
    capacities = env.cr.dictfetchall()
    condition_model = env["stock.storage.category.allow_new_product.cond"]
    for capacity in capacities:
        _logger.info("row = %s", capacity)
        package_type = env["stock.package.type"].browse(capacity["package_type_id"])
        package_type_name = package_type.name if package_type else "Any package type"
        condition_name = f"[MIG] {package_type_name}"
        condition = condition_model.search([("name", "=", condition_name)], limit=1)
        if not condition:
            if package_type:
                code_snippet = f"""
result = False
if package_type and package_type.id == {package_type.id}:
    result = True
                """
            else:
                code_snippet = """
result = False
if not package_type:
    result = True
                """
            vals = {
                "name": condition_name,
                "code_snippet": code_snippet,
            }
            condition = condition_model.create(vals)
        # Bind the condition with the category through a allow_new_product rule
        category = env["stock.storage.category"].browse(capacity["storage_category_id"])
        vals = {
            "allow_new_product": capacity["allow_new_product"],
            "condition_ids": [fields.Command.link(condition.id)],
        }
        category.write({"allow_new_product_ids": [fields.Command.create(vals)]})
