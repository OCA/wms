/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

/* eslint-disable valid-jsdoc */
/* eslint-disable no-implicit-globals */
/* eslint-disable strict */

// Credit https://stackoverflow.com/questions/43792026

var _oldFetch = fetch;

/**
 * Patch `fetch` to trigger events on start and end request.
 */
window.fetch = function() {
    // Create hooks
    var fetchStart = new Event("fetchStart", {
        view: document,
        bubbles: true,
        cancelable: false,
    });
    var fetchEnd = new Event("fetchEnd", {
        view: document,
        bubbles: true,
        cancelable: false,
    });

    // Pass the supplied arguments to the real fetch function
    var fetchCall = _oldFetch.apply(this, arguments);

    // Trigger the fetchStart event
    document.dispatchEvent(fetchStart);

    fetchCall
        .then(function() {
            // Trigger the fetchEnd event
            document.dispatchEvent(fetchEnd);
        })
        .catch(function() {
            // Trigger the fetchEnd event
            document.dispatchEvent(fetchEnd);
        });

    return fetchCall;
};
