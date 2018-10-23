Vue.use(Vuex);

export const store = new Vuex.Store({
    state: {
        taxis: [],
        passengers: [],
        paths: [],
        waiting_time: 0,
        total_time: 0,
        simulation_status: false,
        treedata: {}
    },
    mutations: {
        addTaxis: (state, payload) => {
            if (payload.length > 0) {
                let new_paths = [];
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.taxis, payload[i], taxi_popup);

                    if (payload[i].path) {
                        new_paths.push({latlngs: payload[i].path, color: get_color(payload[i].status)})
                    }
                }
                state.paths = new_paths;
            } else {
                state.taxis = [];
                state.paths = [];
            }
        },
        addPassengers: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.passengers, payload[i], passenger_popup);
                }
            } else {
                state.passengers = [];
            }
        },
        update_simulation_status: (state, stats) => {
            if (!stats.is_running) state.simulation_status = false;
            else {
                state.simulation_status = !stats.finished;
            }
        },
        update_tree: (state, payload) => {
            state.treedata = payload;
        }
    },
    getters: {
        get_taxis: (state) => {
            return state.taxis;
        },
        get_passengers: (state) => {
            return state.passengers;
        },
        get_paths: (state) => {
            return state.paths;
        },
        get_waiting_time: (state) => {
            return state.waiting_time;
        },
        get_total_time: (state) => {
            return state.total_time;
        },
        status: (state) => {
            return state.simulation_status && (state.passengers.length || state.taxis.length);
        },
        tree: (state) => {
            return state.treedata;
        }
    }
});

let update_item_in_collection = function (collection, item, get_popup) {
    let p = getitem(collection, item);
    if (p === false) {
        item.latlng = L.latLng(item.position[0], item.position[1]);
        item.popup = get_popup(item);
        item.visible = true;
        collection.push(item)
    }
    else {
        collection[p].latlng = L.latLng(item.position[0], item.position[1]);
        collection[p].popup = get_popup(item);
        collection[p].speed = item.speed;
        collection[p].status = item.status;
        collection[p].visible = item.status !== "PASSENGER_IN_TAXI" &&
                                item.status !== "PASSENGER_IN_DEST" &&
                                item.status !== "PASSENGER_LOCATION";
    }
};

let getitem = function (collection, item) {
    for (let j = 0; j < collection.length; j++) {
        if (collection[j].id === item.id) {
            return j;
        }
    }
    return false;
};

let color = {
    11: "rgb(255, 170, 0)",
    13: "rgb(0, 149, 255)",
    "TAXI_MOVING_TO_PASSENGER": "rgb(255, 170, 0)",
    "TAXI_MOVING_TO_DESTINATION": "rgb(0, 149, 255)",
};

function get_color(status) {
    return color[status];
}

let statuses = {
    10: "TAXI_WAITING",
    11: "TAXI_MOVING_TO_PASSENGER",
    12: "TAXI_IN_PASSENGER_PLACE",
    13: "TAXI_MOVING_TO_DESTINY",
    14: "TAXI_WAITING_FOR_APPROVAL",
    //
    20: "PASSENGER_WAITING",
    21: "PASSENGER_IN_TAXI",
    22: "PASSENGER_IN_DEST",
    23: "PASSENGER_LOCATION",
    24: "PASSENGER_ASSIGNED"
};


function passenger_popup(passenger) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + passenger.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + passenger.status + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + passenger.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + passenger.dest + "</td></tr>" +
        "<tr><th>TAXI</th><td>" + passenger.taxi + "</td></tr>" +
        "<tr><th>WAITING</th><td>" + passenger.waiting + "</td></tr>" +
        "</table>"
}

function taxi_popup(taxi) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + taxi.id + "</td></tr>" +
        "<tr><th>STATUS</th><td>" + taxi.status + "</td></tr>" +
        "<tr><th>PASSENGER</th><td>" + taxi.passenger + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + taxi.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + taxi.dest + "</td></tr>" +
        "<tr><th>ASSIGNMENTS</th><td>" + taxi.assignments + "</td></tr>" +
        "<tr><th>SPEED</th><td>" + taxi.speed + "</td></tr>" +
        "<tr><th>DISTANCE</th><td>" + taxi.distance + "</td></tr>" +
        "</table>"
}
