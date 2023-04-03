Use Inventory > Operations > Release Channels to access to the dashboard.

Each channel has a dashboard with statistics about the number of transfers
to release and of the progress of the released transfers.

When clicking on the "box" button, transfers are released automatically, to
reach a total of <Max Transfers to release> (option configured in the channel
settings).

The availability of a release channel depends on its state. A release channel
can be in one of the following states:

  - Open: the channel is available and can be used to release transfers. New
    transfer are assigned automatically to this channel.
  - Locked: the channel is available but the release of transfers from the channel
    is no more possible. New transfers are still automatically assigned to this
  - Asleep: the channel is not available and cannot be used to release
    transfers. It is also no more possible to assign transfers to this channel.

New release channels are by default "Open". You can change its state by using
the "Lock" and "Sleep" buttons. When the "Sleep" button is used, in addition to
the state change, not completed transfers assigned to the channel are unassigned
from the channel. When the "Lock" button is used, only the state change is changed.
A locked channel can be unlocked by using the "Unlock" button.
A asleep channel can be waken up by using the "Wake up" button. When the "Wake up"
button is used, in addition to the state change, the system looks for pending
transfers requiring a release and try to assign them to a channel in the
"Open" or "Locked" state.
