<template>
    <ul id="treeview-ul" class="list-group" style="list-style-type: none;">
      <li>
          <div class=" bold list-group-item" @click="toggleTransport">
            <span class="icon expand-icon glyphicon"
                    :class="{'glyphicon-chevron-down': openTransport, 'glyphicon-chevron-right': !openTransport}">
            </span>
              Transports
            <span class="badge">{{transports.length}}</span>
          </div>
      </li>

      <li v-for="transport in transports" v-show="openTransport">
          <div class="list-group-item">
              <img v-bind:src="transport.icon_url" height="20px"/>  {{transport.id}}
              <status-indicator positive v-if="transport.status == 'TRANSPORT_WAITING'"></status-indicator>
              <status-indicator intermediary v-else-if="transport.status == 'TRANSPORT_WAITING_FOR_APPROVAL'"></status-indicator>
              <status-indicator negative pulse v-else-if="transport.status == 'TRANSPORT_MOVING_TO_STATION'"></status-indicator>
              <status-indicator intermediary pulse v-else-if="transport.status == 'TRANSPORT_MOVING_TO_CUSTOMER'"></status-indicator>
              <status-indicator active pulse v-else-if="transport.status == 'TRANSPORT_MOVING_TO_DESTINATION'"></status-indicator>
          </div>
      </li>

      <li>
          <div class=" bold list-group-item" @click="toggleCustomer">
            <span class="icon expand-icon glyphicon"
                    :class="{'glyphicon-chevron-down': openCustomer, 'glyphicon-chevron-right': !openCustomer}">
            </span>
              Customers
            <span class="badge">{{customers.length}}</span>
          </div>
      </li>

      <li v-for="customer in customers" v-show="openCustomer">
          <div class="list-group-item">
              <img v-bind:src="customer.icon_url" height="20px"/>  {{customer.id}}
              <status-indicator v-if="customer.status == 'CUSTOMER_WAITING'"></status-indicator>
              <status-indicator intermediary v-else-if="customer.status == 'CUSTOMER_ASSIGNED'"></status-indicator>
              <status-indicator intermediary v-else-if="customer.status == 'CUSTOMER_MOVING_TO_DEST'"></status-indicator>
              <status-indicator active pulse v-else-if="customer.status == 'CUSTOMER_IN_TRANSPORT'"></status-indicator>
              <status-indicator positive v-else-if="customer.status == 'CUSTOMER_IN_DEST'"></status-indicator>
          </div>
      </li>

    </ul>
</template>


<script>

    import StatusIndicator from './StatusIndicator'

    export default {
        name: "tree-view",
        props: {
            transports: Array,
            customers: Array
        },
        data: function () {
            return {
              open: true,
              openTransport: true,
              openCustomer: true
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
            toggleTransport: function () {
                this.openTransport = !this.openTransport
            },
            toggleCustomer: function () {
                this.openCustomer = !this.openCustomer
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
