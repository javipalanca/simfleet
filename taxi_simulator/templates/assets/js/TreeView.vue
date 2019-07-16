<template>
    <ul id="treeview-ul" class="list-group" style="list-style-type: none;">
      <li>
          <div class=" bold list-group-item" @click="toggleTaxi">
            <span class="icon expand-icon glyphicon"
                    :class="{'glyphicon-chevron-down': openTaxi, 'glyphicon-chevron-right': !openTaxi}">
            </span>
              Taxis
            <span class="badge">{{taxis.length}}</span>
          </div>
      </li>

      <li v-for="o in taxis" v-show="openTaxi">
          <div class="list-group-item" v-tooltip.top="{content: status2str(o.status), delay:100}">
              <span  class="fa fa-taxi" ></span>  {{ o.id }}
              <status-indicator positive v-if="o.status == 'TRANSPORT_WAITING'"></status-indicator>
              <status-indicator intermediary v-else-if="o.status == 'TRANSPORT_WAITING_FOR_APPROVAL'"></status-indicator>
              <status-indicator intermediary pulse v-else-if="o.status == 'TRANSPORT_MOVING_TO_CUSTOMER'"></status-indicator>
              <status-indicator active pulse v-else-if="o.status == 'TRANSPORT_MOVING_TO_DESTINATION'"></status-indicator>
          </div>
      </li>

      <li>
          <div class=" bold list-group-item" @click="togglePass">
            <span class="icon expand-icon glyphicon"
                    :class="{'glyphicon-chevron-down': openPass, 'glyphicon-chevron-right': !openPass}">
            </span>
              Passengers
            <span class="badge">{{passengers.length}}</span>
          </div>
      </li>

      <li v-for="passenger in passengers" v-show="openPass">
          <div class="list-group-item" v-tooltip.top="{content: status2str(passenger.status), delay:100}">
              <span  class="fa fa-user" ></span>  {{passenger.id}}
              <status-indicator v-if="passenger.status == 'CUSTOMER_WAITING'"></status-indicator>
              <status-indicator intermediary v-else-if="passenger.status == 'CUSTOMER_ASSIGNED'"></status-indicator>
              <status-indicator active pulse v-else-if="passenger.status == 'CUSTOMER_IN_TRANSPORT'"></status-indicator>
              <status-indicator positive v-else-if="passenger.status == 'CUSTOMER_IN_DEST'"></status-indicator>
          </div>
      </li>

    </ul>
</template>


<script>

    import StatusIndicator from './StatusIndicator'

    export default {
        name: "tree-view",
        props: {
            taxis: Array,
            passengers: Array
        },
        data: function () {
            return {
              open: true,
              openTaxi: true,
              openPass: true
            }
        },
        computed: {
            isFolder: function () {
              return this.model.children
            }
        },
        methods: {
            toggle: function () {
              if (this.isFolder) {
                this.open = !this.open
              }
            },
            toggleTaxi: function () {
                this.openTaxi = !this.openTaxi
            },
            togglePass: function () {
                this.openPass = !this.openPass
            },
            status2str: function(status) {
                switch(status){
                    case 10: return 'TRANSPORT_WAITING';
                    case 11: return 'TRANSPORT_MOVING_TO_CUSTOMER';
                    case 12: return 'TRANSPORT_IN_CUSTOMER_PLACE';
                    case 13: return 'TRANSPORT_MOVING_TO_DESTINATION';
                    case 14: return 'TRANSPORT_WAITING_FOR_APPROVAL';
                    case 20: return 'CUSTOMER_WAITING';
                    case 21: return 'CUSTOMER_IN_TRANSPORT';
                    case 22: return 'CUSTOMER_IN_DEST';
                    case 24: return 'CUSTOMER_ASSIGNED';
                }
                return status;
            }
        },
        components: {
            'status-indicator': StatusIndicator,
        }
    }
</script>

<style scoped>
.item {
  cursor: pointer;
}
.bold {
  font-weight: bold;
}
ul {
  /*padding-left: 1em;
  line-height: 1.5em;*/
  -webkit-padding-start: 0;
  list-style-type: none;
}

.list-group-item{
    border-radius: 0;

    position: relative;
    display: block;
    padding: 10px 15px;
    margin-bottom: -2px;
    background-color: #fff;
    border: 1px solid #ddd;
}

.status-indicator {
    float: right;
}
</style>
