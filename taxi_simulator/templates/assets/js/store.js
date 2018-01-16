Vue.use(Vuex);


export const store = new Vuex.Store({
    state: {
        taxis: [],
        passengers: []
    },
    mutations: {
        addTaxis: (state, payload) => {
            state.taxis = payload;
        },
        addPassengers: (state, payload) => {
          state.passengers = payload;
        }
    }
});


