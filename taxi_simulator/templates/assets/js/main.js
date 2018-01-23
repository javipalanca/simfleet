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
            taxiIcon: L.icon({iconUrl: 'assets/img/taxi.png', iconSize: [38, 55]}),
            passengerIcon: L.icon({iconUrl: 'assets/img/passenger.png', iconSize: [38, 40]})
        }
    },
    mounted() {
       this.loadEntities();
       setInterval(function () {
            this.loadEntities();
       }.bind(this), 100);
    },
    methods: {
        loadEntities: function () {
            axios.get("/entities")
                .then(data => {
                    this.$store.commit('addTaxis', data.data.taxis);
                    this.$store.commit('addPassengers', data.data.passengers);
                    this.$store.state.waiting_time = data.data.stats.waiting;
                    this.$store.state.total_time = data.data.stats.totaltime;
                    this.$store.commit('update_simulation_status', data.data.stats);
                    this.$store.commit("update_tree", data.data.tree);
                }).catch(error => {});
        },
        set_speed: function (event, item) {
            event.target._icon.style[L.DomUtil.TRANSITION] = ('all ' + item.speed + 'ms linear');
        },
        showSidebar: function () {
            this.$refs.sidebar.hideSidebar = !this.$refs.sidebar.hideSidebar
        }
    },
    computed: {
        taxis()  {
            return this.$store.getters.get_taxis;
        },
        passengers()  {
            return this.$store.getters.get_passengers;
        },
        paths() {
            return this.$store.getters.get_paths;
        },
        treeData() {
            return this.$store.getters.tree;
        }
    }
});

