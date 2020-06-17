import {demotools} from "./demo.core.js";

let lines = [];
let pickings = [];
const count = 8;
const move_lines = demotools.makePickingLines(
    {},
    {lines_count: demotools.getRandomInt(5), line_random_pack: true}
);

const DEMO_LOCATION_CONTENT_TRANSFER = {
    start_or_recover: {
        next_state: "start_recovered",
        message: {
            message_type: "info",
            body: "Recovered previous session.",
        },
        data: {
            start_recovered: {
                move_line: demotools.makeSingleLineOperation(),
                // TODO: we'll get this from backend
                // "package_level": level_data
            },
        },
    },
};

demotools.add_case("location_content_transfer", DEMO_LOCATION_CONTENT_TRANSFER);
