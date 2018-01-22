<!--template>
  <li>
    <div v-show="model.name !== 'Agents'"
      :class="{bold: isFolder}"
      class="list-group-item"
      @click="toggle">
      <span class="icon expand-icon glyphicon"
            v-if="isFolder"
            :class="{'glyphicon-chevron-down': open, 'glyphicon-chevron-right': !open}">
      </span>
      <span v-tooltip.top="{content: status2str(model.status), delay:500, triggers: ['focus']}" v-if="!isFolder">
            <span  class="fa" :class="model.icon"></span>
      {{model.name}}
      </span>
      <span v-else>{{model.name}}</span>
      <span class="badge" v-if="isFolder">{{model.count}}</span>
      <status-indicator positive v-if="model.status == 10"></status-indicator>
      <status-indicator intermediary v-else-if="model.status == 14"></status-indicator>
      <status-indicator negative pulse v-else-if="model.status == 11 || model.status == 13"></status-indicator>
      <status-indicator v-else-if="model.status == 20"></status-indicator>
      <status-indicator intermediary v-else-if="model.status == 24"></status-indicator>
      <status-indicator active pulse v-else-if="model.status == 21"></status-indicator>
      <status-indicator active v-else-if="model.status == 22"></status-indicator>
    </div>
    <transition name="child">
    <ul v-show="open" v-if="isFolder">
      <tree-view
        class="item"
        v-for="model in model.children"
        :model="model">
      </tree-view>
    </ul>
    </transition>
  </li>
</template-->

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
          <status-indicator positive v-if="o.status == 10"></status-indicator>
          <status-indicator intermediary v-else-if="o.status == 14"></status-indicator>
          <status-indicator negative pulse v-else-if="o.status == 11 || o.status == 13"></status-indicator>
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
          <status-indicator v-if="passenger.status == 20"></status-indicator>
          <status-indicator intermediary v-else-if="passenger.status == 24"></status-indicator>
          <status-indicator active pulse v-else-if="passenger.status == 21"></status-indicator>
          <status-indicator active v-else-if="passenger.status == 22"></status-indicator>
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
                    case 10: return 'TAXI_WAITING';
                    case 11: return 'TAXI_MOVING_TO_PASSENGER';
                    case 12: return 'TAXI_IN_PASSENGER_PLACE';
                    case 13: return 'TAXI_MOVING_TO_DESTINY';
                    case 14: return 'TAXI_WAITING_FOR_APPROVAL';
                    case 20: return 'PASSENGER_WAITING';
                    case 21: return 'PASSENGER_IN_TAXI';
                    case 22: return 'PASSENGER_IN_DEST';
                    case 24: return 'PASSENGER_ASSIGNED';
                }
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
