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
        UPDATE stock_storage_category_capacity sscc
            SET allow_new_product = (
                SELECT
                    (CASE
                        WHEN do_not_mix_lots = true THEN 'same_lot'
                        WHEN do_not_mix_products = true
                            AND do_not_mix_lots = false THEN 'same'
                        WHEN only_empty = True THEN 'empty'
                        ELSE 'mixed'
                    END)
                    FROM stock_location_storage_type
                    WHERE id = old_location_storage_type_id)
            FROM stock_location_storage_type slst
            WHERE slst.id = sscc.old_location_storage_type_id
    """
    openupgrade.logged_query(env.cr, query)


def _update_location_sequence(env):
    query = """
        UPDATE stock_storage_location_sequence ssls
            SET package_type_id = spt.id
            FROM stock_package_type spt
            WHERE spt.old_storage_type_id = ssls.package_storage_type_id
    """
    openupgrade.logged_query(env.cr, query)


def _update_quant_package(env):
    query = """
        UPDATE stock_quant_package sqp
            SET package_type_id = spt.id
            FROM stock_package_type spt
            WHERE spt.old_storage_type_id = sqp.package_storage_type_id
    """
    openupgrade.logged_query(env.cr, query)


def _update_product_template(env):
    query = """
        ALTER TABLE product_template
            DROP CONSTRAINT product_template_product_package_storage_type_id_fkey;
        UPDATE product_template pt
            SET product_package_storage_type_id = spt.id
            FROM stock_package_type spt
            WHERE spt.old_storage_type_id = pt.product_package_storage_type_id;
    """
    openupgrade.logged_query(env.cr, query)


@openupgrade.migrate()
def migrate(env, version):
    _move_product_package_type(env)
    _move_location_storage_type(env)
    _update_location_sequence(env)
    _update_quant_package(env)
    _update_product_template(env)
