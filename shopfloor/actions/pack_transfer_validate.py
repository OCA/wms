from odoo.addons.component.core import Component


# TODO think BETTER about how we want to share the common methods / workflows
class PackTransferValidateAction(Component):
    """Pack Transfer shared business logic

    This component is shared by the "validate" action of the processes:

    * single_pack_putaway
    * single_pack_transfer
    """

    _name = "shopfloor.pack.transfer.validate.action"
    _inherit = "shopfloor.process.action"
    _usage = "pack.transfer.validate"

    def is_move_state_valid(self, move):
        return move.state != "cancel"

    def is_dest_location_valid(self, move, scanned_location):
        """Forbid a dest location to be used"""
        return scanned_location.is_sublocation_of(
            move.picking_id.picking_type_id.default_location_dest_id
        )

    def is_dest_location_to_confirm(self, move, scanned_location):
        """Destination that could be used but need confirmation"""
        move_dest_location = move.move_line_ids[0].location_dest_id
        return not scanned_location.is_sublocation_of(move_dest_location)

    def set_destination_and_done(self, move, scanned_location):
        move.move_line_ids[0].location_dest_id = scanned_location.id
        move._action_done()
