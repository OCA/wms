import {shallowMount} from "@vue/test-utils";
import {Searchbar} from "shopfloor_mobile_base/static/wms/src/components/searchbar/searchbar.js";
import MockRoot from "../mocks/root.js";

const root_config = {};

describe("Searchbar component", () => {
    let wrapper;

    beforeEach(() => {
        // We run this before each test to make sure
        // the state is reset. If the state needs to be maintained,
        // move it outside of beforeEach.
        wrapper = shallowMount(Searchbar, {
            Vuetify,
            parentComponent: {
                // Mocking $root requires a special procedure,
                // which is why it cannot go in the mocks object:
                // https://github.com/vuejs/vue-test-utils/issues/481
                data() {
                    return MockRoot(root_config);
                },
            },
        });
    });

    it("Resets input on search", () => {
        expect(wrapper.vm.entered).toBe("");
        wrapper.vm.entered = "search text";
        expect(wrapper.vm.entered).toBe("search text");
        wrapper.vm.search();
        expect(wrapper.vm.entered).toBe("");
    });

    it("The input is correctly trimmed", () => {
        // setProps can be called once after mounting to set specific props for the component.
        wrapper.setProps({autotrim: true});
        wrapper.vm.entered = "  to trim  ";
        // We use $nextTick as watchers are deferred to the next update cycle.
        wrapper.vm.$nextTick(() => {
            expect(wrapper.vm.entered).toBe("to trim");
        });
    });

    it("The input is not trimmed if autotrim is disabled", () => {
        wrapper.setProps({autotrim: false});
        wrapper.vm.entered = "  not to trim  ";
        wrapper.vm.$nextTick(() => {
            expect(wrapper.vm.entered).toBe("  not to trim  ");
        });
    });
});
