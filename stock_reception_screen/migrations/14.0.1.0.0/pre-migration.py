# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        ALTER TABLE stock_reception_screen
        RENAME COLUMN current_move_line_lot_life_date
            TO current_move_line_lot_expiration_date;
        """
    )
