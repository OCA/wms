# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """
        UPDATE
            stock_picking
        SET
            release_policy = procurement_group.move_type
        FROM
            procurement_group
        WHERE
            stock_picking.group_id = procurement_group.id
    """
    )
