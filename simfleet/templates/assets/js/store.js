Vue.use(Vuex);

export const store = new Vuex.Store({
    state: {
        transports: [],
        customers: [],
        stations: [],
        vehicles: [],
        paths: [],
        total_time: 0,
        simulation_status: false,
        treedata: {}
    },
    mutations: {
        addTransports: (state, payload) => {
        if (payload.length > 0) {
            let new_paths = [];
            for (let i = 0; i < payload.length; i++) {
                update_item_in_collection(state.transports, payload[i], transport_popup);

                // Ahora el path se dibuja siempre que exista, sin depender del estado
                if (payload[i].path) {
                    new_paths.push({
                        latlngs: payload[i].path,
                        color: "rgb(255, 170, 0)"  // Color naranja para todos los paths
                    });
                }
            }
            state.paths = new_paths;
        } else {
            state.transports = [];
            state.paths = [];
        }
    },
        addCustomers: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.customers, payload[i], customer_popup);
                }
            } else {
                state.customers = [];
            }
        },
        addStations: (state, payload) => {
            if (payload.length >0) {
                for (let i = 0; i < payload.length; i++) {
                    update_station_in_collection(state.stations, payload[i], station_popup);
                }
            } else {
                state.stations = [];
            }
        },
        addVehicles: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.vehicles, payload[i], vehicle_popup); // Usa una función similar a la de transports


                }
            } else {
                state.vehicles = [];
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
        get_transports: (state) => {
            return state.transports;
        },
        get_customers: (state) => {
            return state.customers;
        },
        get_stations: (state) => {
            return state.stations;
        },
        get_vehicles: (state) => {
            return state.vehicles;
        },
        get_paths: (state) => {
            return state.paths;
        },
        get_total_time: (state) => {
            return state.total_time;
        },
        status: (state) => {
            return state.simulation_status && (state.customers.length || state.transports.length || state.vehicles.length);
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
        item.icon_url = item.icon;
        if(item.icon) {
            item.icon = L.icon({iconUrl: item.icon, iconSize: [38, 55]});
        }
        else {
            item.icon = L.icon({iconUrl: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
                iconSize: [38, 55]});
        }
        collection.push(item)
    }
    else {
        collection[p].latlng = L.latLng(item.position[0], item.position[1]);
        collection[p].popup = get_popup(item);
        collection[p].speed = item.speed;
        collection[p].status = item.status;
        collection[p].icon_url = item.icon;
        if(item.icon) {
            collection[p].icon = L.icon({iconUrl: item.icon, iconSize: [38, 55]});
        }
        collection[p].visible = item.status !== "CUSTOMER_IN_TRANSPORT" &&
                                item.status !== "CUSTOMER_IN_DEST" &&
                                item.status !== "CUSTOMER_LOCATION" &&
                                item.status !== "TRANSPORT_LOADING";
    }
};

let update_station_in_collection = function (collection, item, get_popup) {
    let p = getitem(collection, item);
    if (p === false) {
        item.latlng = L.latLng(item.position[0], item.position[1]);
        item.popup = get_popup(item);
        item.visible = true;
        item.icon_url = item.icon;
        if(item.icon) {
            item.icon = L.icon({iconUrl: item.icon, iconSize: [38, 55]});
        }
        collection.push(item)
    }
    else {
        collection[p].popup = get_popup(item);
        collection[p].status = item.status;
        item.icon_url = item.icon;
        if(item.icon) {
            item.icon = L.icon({iconUrl: item.icon, iconSize: [38, 55]});
        }
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

let statuses = {
    10: "TRANSPORT_WAITING",
    11: "TRANSPORT_MOVING_TO_CUSTOMER",
    12: "TRANSPORT_IN_CUSTOMER_PLACE",
    13: "TRANSPORT_MOVING_TO_DESTINY",
    14: "TRANSPORT_WAITING_FOR_APPROVAL",
    15: "TRANSPORT_MOVING_TO_STATION",
    16: "TRANSPORT_IN_STATION_PLACE",
    17: "TRANSPORT_WAITING_FOR_STATION_APPROVAL",
    18: "TRANSPORT_LOADING",
    19: "TRANSPORT_LOADED",
    //
    20: "CUSTOMER_WAITING",
    21: "CUSTOMER_IN_TRANSPORT",
    22: "CUSTOMER_IN_DEST",
    23: "CUSTOMER_LOCATION",
    24: "CUSTOMER_ASSIGNED",
    //
    30: "FREE_STATION",
    31: "BUSY_STATION",
};


function customer_popup(customer) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + customer.id + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + customer.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + customer.dest + "</td></tr>" +
        "</table>"
}

function transport_popup(transport) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + transport.id + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + transport.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + transport.dest + "</td></tr>" +
        "<tr><th>ASSIGNMENTS</th><td>" + transport.assignments + "</td></tr>" +
        "<tr><th>SPEED</th><td>" + transport.speed + "</td></tr>" +
        "<tr><th>DISTANCE</th><td>" + transport.distance + "</td></tr>" +
        "</table>"
}

function station_popup(station) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + station.id + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + station.position + "</td></tr>" +
        "</table>"
}

function vehicle_popup(vehicle) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + vehicle.id + "</td></tr>" +
        "<tr><th>POSITION</th><td>" + vehicle.position + "</td></tr>" +
        "<tr><th>DEST</th><td>" + vehicle.dest + "</td></tr>" +
        "<tr><th>SPEED</th><td>" + vehicle.speed + "</td></tr>" +
        "<tr><th>DISTANCE</th><td>" + vehicle.distance + "</td></tr>" +
        "</table>"
}