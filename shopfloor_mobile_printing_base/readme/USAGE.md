Use this in your component template:

` <label-printer v-on:print_labels="state.print_labels($event)" buttonLabel="<The label>"/> `

Implement the `print_labels()` (or whatever you call it) method on your component level:

```
const Reception = process_registry.extend("reception", {
    template: new_template,
    "methods._get_states": function () {
        let states = _get_states.bind(this)();
        const set_destination = states.set_destination;

        const self = this;
        set_destination.print_labels = function (quantity) {
            self.wait_call(
            self.odoo.call("print_labels", {
                picking_id: self.state.data.picking.id,
                selected_line_id: self.state.data.selected_move_line[0].id,
                quantity: quantity,
            })
            );
        };
        return states;
    },
});
```

See `shopfloor_printing_base` for backend implementation.
