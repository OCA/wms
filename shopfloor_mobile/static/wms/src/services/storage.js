export const Storage = {
    set apikey(value) {
        localStorage.setItem("apikey", value);
    },

    get apikey() {
        return localStorage.getItem("apikey");
    },
};
