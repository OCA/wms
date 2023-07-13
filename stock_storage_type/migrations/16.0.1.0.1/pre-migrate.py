# Copyright 2022 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from openupgradelib import openupgrade


def _move_product_package_type(env):
    """
    stock.package.storage.type has been merged with product.package.type
    which is in core now.
    """
    query = "ALTER TABLE stock_package_type ADD COLUMN old_storage_type_id integer"
    openupgrade.logged_query(env.cr, query)
    # Insert data from old model to new
    query = """
        INSERT INTO stock_package_type (name, old_storage_type_id)
            (SELECT name, id FROM stock_package_storage_type sspt)
        RETURNING id, old_storage_type_id
    """
    openupgrade.logged_query(env.cr, query)
    openupgrade.merge_models(
        env.cr,
        "stock.package.storage.type",
        "stock.package.type",
        "old_storage_type_id",
    )
    # Update possible xml ids
    query = """
        UPDATE ir_model_data
            SET model = 'stock.package.type'
            WHERE model = 'stock.package.storage.type'
    """
    openupgrade.logged_query(env.cr, query)


def _move_location_storage_type(env):
    """
    stock.storage.location.type has been merged with stock.storage.category.capacity
    which is in core now.
    """
    query = """
        ALTER TABLE stock_storage_category_capacity
            ADD COLUMN old_location_storage_type_id integer
    """
    openupgrade.logged_query(env.cr, query)

    _create_categories(env)

    openupgrade.merge_models(
        env.cr,
        "stock.location.storage.type",
        "stock.storage.category.capacity",
        "old_location_storage_type_id",
    )
    # Update possible xml ids
    query = """
        UPDATE ir_model_data
            SET model = 'stock.storage.category.capacity'
            WHERE model = 'stock.location.storage.type'
    """
    openupgrade.logged_query(env.cr, query)


def _create_categories(env):
    """
    Iterate on locations that have the field location_storage_type_ids
    filled in and create a storage category for each combination.
    Don't duplicate capacities that have the same:
        - category
        - package type
    """
    query = """
        SELECT DISTINCT(location_id) FROM stock_location_location_storage_type_rel;
    """
    openupgrade.logged_query(env.cr, query)
    result = env.cr.fetchall()
    ids = [r[0] for r in result]
    existing_location_type_ids = {}
    for location_id in ids:
        query = """
            SELECT id, name FROM stock_location_storage_type
                WHERE id in (
                    SELECT location_storage_type_id
                        FROM stock_location_location_storage_type_rel
                        WHERE location_id = %s
                    )
        """
        openupgrade.logged_query(env.cr, query, (location_id,))
        result = env.cr.fetchall()
        location_type_ids = {res[0] for res in result}
        name = "/".join([res[1] for res in result])
        category_id = None
        for category, existing_location_type in existing_location_type_ids.items():
            if all(
                location_type_id in existing_location_type
                for location_type_id in location_type_ids
            ):
                # All ids are found in the existing category
                category_id = category
                break
        if category_id is None:
            query = """
                INSERT INTO stock_storage_category (name, allow_new_product)
                    VALUES (%s, 'mixed')
                    RETURNING id
            """
            openupgrade.logged_query(env.cr, query, (name,))
            result = env.cr.fetchone()
            category_id = result[0]

        # Update the location by setting the category
        query = """
            UPDATE stock_location
                SET storage_category_id = %s
                WHERE id = %s
                AND storage_category_id IS NULL;
        """
        openupgrade.logged_query(
            env.cr,
            query,
            (
                category_id,
                location_id,
            ),
        )

        # Get all the linked package storage types (former package_storage_type_ids)
        query = """
            SELECT spt.id, rel.location_storage_type_id
                FROM stock_location_package_storage_type_rel rel
                JOIN stock_package_type spt
                    ON spt.old_storage_type_id = rel.package_storage_type_id
                WHERE location_storage_type_id IN %s
        """
        openupgrade.logged_query(env.cr, query, (tuple(list(location_type_ids)),))
        results = env.cr.fetchall()
        for result in results:
            query = """
                INSERT INTO stock_storage_category_capacity
                (storage_category_id, quantity, package_type_id, old_location_storage_type_id)
                VALUES (%s, 1, %s, %s)
                ON CONFLICT (storage_category_id, package_type_id) DO NOTHING
            """
            openupgrade.logged_query(
                env.cr,
                query,
                (
                    category_id,
                    result[0],
                    result[1],
                ),
            )
        existing_location_type_ids[category_id] = location_type_ids


@openupgrade.migrate()
def migrate(env, version):
    _move_product_package_type(env)
    _move_location_storage_type(env)
