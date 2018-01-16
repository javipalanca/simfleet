import {store} from './store.js'

import SidebarComponent from './SidebarComponent.vue'

new Vue({
    el: '#container',
    store: store,
    components: {
        'v-map': Vue2Leaflet.Map,
        'v-tilelayer': Vue2Leaflet.TileLayer,
        'v-marker': Vue2Leaflet.Marker,
        SidebarComponent: SidebarComponent
    },
    data() {
        return {
            zoom: 14,
            center: [39.47, -0.37],
            url: 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>',
            marker: L.latLng(47.413220, -1.219482),
        }
    },
    mounted() {
        this.loadEntities();
           setInterval(function () {
                this.loadEntities();
           }.bind(this), 1500);
    },
    methods: {
        loadEntities: function () {
            axios.get("http://localhost:9000/entities")
                .then(data => {
                    this.$store.commit('addTaxis', data.data.taxis);
                    this.$store.commit('addPassengers', data.data.passengers);
                })
        }
    },
    computed: {
        taxis()  { return this.$store.state.taxis },
        passengers()  { return this.$store.state.passengers }
    }
});

