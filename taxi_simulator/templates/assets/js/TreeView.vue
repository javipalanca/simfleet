<template>
  <li>
    <div :class="{bold: isFolder}" @click="toggle">
      {{model.name}}
      <span v-if="isFolder">[{{open ? '-' : '+'}}]</span>
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
              open: false
            }
        },
        computed: {
            isFolder: function () {
              return this.model.children &&
                this.model.children.length
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
  padding-left: 1em;
  line-height: 1.5em;
  list-style-type: dot;
}
</style>
