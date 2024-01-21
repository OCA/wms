A "Deliver" button for locked release channels is added.

When this new button is pressed:
  - The release channel change its state to "delivering".
  - A background task (job queue) is planned to:
      - Validate the shippings related to the release channel.
      - Create the shipment advices.
      - Processes the shipment advices.

At the end of the background task:
  - The release channel status moves to "delivered" if no errors are detected.
  - Otherwise appropriate error messages are displayed and a button to retry
    is shown to the user.
