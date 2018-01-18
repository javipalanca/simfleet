<template>
  <li>
    <div v-show="model.name !== 'Agents'"
      :class="{bold: isFolder}"
      class="list-group-item"
      @click="toggle">
      <span class="icon expand-icon glyphicon"
            v-if="isFolder"
            :class="{'glyphicon-chevron-down': open, 'glyphicon-chevron-right': !open}">
      </span>
      <span v-if="!isFolder" class="fa" :class="model.icon"></span>
      {{model.name}}
      <span class="badge" v-if="isFolder">{{model.count}}</span>
    </div>
    <ul v-show="open" v-if="isFolder">
      <tree-view
        class="item"
        v-for="model in model.children"
        :model="model">
      </tree-view>
    </ul>
  </li>
</template>

<script>
    export default {
        name: "tree-view",
        props: {
            model: Object
        },
        data: function () {
            return {
              open: true
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
            }
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
</style>
