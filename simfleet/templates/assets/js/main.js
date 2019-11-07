import {store} from './store.js'

import SidebarComponent from './SidebarComponent.vue'
import TreeView from './TreeView'

Vue.use(vueDirectiveTooltip);

new Vue({
    el: '#app',
    store: store,
    components: {
        'v-map': Vue2Leaflet.Map,
        'v-tilelayer': Vue2Leaflet.TileLayer,
        'v-marker': Vue2Leaflet.Marker,
        'v-polyline': Vue2Leaflet.Polyline,
        'v-popup': Vue2Leaflet.Popup,
        SidebarComponent: SidebarComponent,
        'tree-view': TreeView,
    },
    data() {
        return {
            zoom: 14,
            center: [39.47, -0.37],
            url: 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            transportIcon: L.icon({iconUrl: 'assets/img/transport.png', iconSize: [38, 55]}),
            customerIcon: L.icon({iconUrl: 'assets/img/customer.png', iconSize: [38, 40]}),
            stationIcon: L.icon({iconUrl: 'assets/img/station.png', iconSize: [38, 40]})
        }
    },
    mounted() {
        this.init();
        this.loadEntities();
        setInterval(function () {
            this.loadEntities();
        }.bind(this), 100);
    },
    methods: {
        init: function () {
            axios.get("/init")
                .then(data => {
                    this.center = data.data.coords;
                    this.zoom = data.data.zoom;
                });
        },
        loadEntities: function () {
            axios.get("/entities")
                .then(data => {
                    this.$store.commit('addTransports', data.data.transports);
                    this.$store.commit('addCustomers', data.data.customers);
                    this.$store.commit("addStations", data.data.stations);
                    this.$store.state.waiting_time = data.data.stats.waiting;
                    this.$store.state.total_time = data.data.stats.totaltime;
                    this.$store.commit('update_simulation_status', data.data.stats);
                    this.$store.commit("update_tree", data.data.tree);
                }).catch(error => {
            });
        },
        set_speed: function (event, item) {
            event.target._icon.style[L.DomUtil.TRANSITION] = ('all ' + item.speed + 'ms linear');
        },
        showSidebar: function () {
            this.$refs.sidebar.hideSidebar = !this.$refs.sidebar.hideSidebar
        }
    },
    computed: {
        transports() {
            return this.$store.getters.get_transports;
        },
        customers() {
            return this.$store.getters.get_customers;
        },
        stations() {
            return this.$store.getters.get_stations;
        },
        paths() {
            return this.$store.getters.get_paths;
        },
        treeData() {
            return this.$store.getters.tree;
        }
    }
});

