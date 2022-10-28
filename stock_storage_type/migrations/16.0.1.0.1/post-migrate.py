# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from openupgradelib import openupgrade


def _move_product_package_type(env):
    """
    stock.package.storage.type has been merged with product.package.type
    which is in core now.
    """
    # Update fields values
    query = """
        UPDATE stock_package_type
            SET height_required = (
                SELECT height_required FROM stock_package_storage_type
                    WHERE id = old_storage_type_id)
    """
    openupgrade.logged_query(env.cr, query)
    # Update ids on product template
    query = """
        UPDATE product_template
            SET package_type_id = (
                SELECT id FROM stock_package_type
                WHERE old_storage_type_id = product_package_storage_type_id
            )
            WHERE product_package_storage_type_id IS NOT NULL
    """
    openupgrade.logged_query(env.cr, query)
    # Update ids on product packaging
    query = """
        UPDATE product_packaging
            SET package_type_id = (
                SELECT id FROM stock_package_type
                WHERE old_storage_type_id = package_storage_type_id
            )
            WHERE package_storage_type_id IS NOT NULL
    """
    openupgrade.logged_query(env.cr, query)


def _move_location_storage_type(env):
    """
    Update location storage type values => capacities
    """
    # Update fields values
    query = """
        UPDATE stock_storage_category_capacity
            SET allow_new_product = (
                SELECT
                    CASE
                        WHEN do_not_mix_products = true THEN 'same'
                        WHEN only_empty = True THEN 'empty'
                        ELSE 'mixed'
                    END
                    FROM stock_location_storage_type
                    WHERE id = old_location_storage_type_id)
    """
    openupgrade.logged_query(env.cr, query)


@openupgrade.migrate()
def migrate(env, version):
    _move_product_package_type(env)
    _move_location_storage_type(env)
