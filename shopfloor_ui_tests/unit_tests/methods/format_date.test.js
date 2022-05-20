import {DisplayUtils} from "shopfloor_mobile_base/static/wms/src/utils.js";

const display_utils = new DisplayUtils();

test("format date to 'Apr 3, 2020' format", () => {
    const options = {
        format: {
            day: "numeric",
            month: "short",
            year: "numeric",
        },
    };
    expect(display_utils.format_date_display("2020-04-03", options)).toBe(
        "Apr 3, 2020"
    );
});
