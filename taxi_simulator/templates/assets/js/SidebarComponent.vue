<template>
    <transition name="slide">
    <div id="sidebar" class="bodycontainer table-scrollable" v-if="!hideSidebar">
        <div class="sidebar-wrapper">
            <div class="panel panel-default" id="features">
                <div class="panel-heading">
                    <h3 class="panel-title">Control Panel
                        <button type="button" class="btn btn-xs btn-default pull-right"
                                id="sidebar-hide-btn" @click="hideSidebar=!hideSidebar">
                            <i class="fa fa-chevron-left"></i>
                        </button>
                    </h3>
                </div>
                <div class="panel-body">
                    <table class="table table-hover" id="feature-list">
                        <thead class="list">
                        <tr>
                            <th>
                                <label for="numtaxis">Num. Taxis</label>
                                <input v-model="numtaxis" type="number"
                                       class="form-control" id="numtaxis"
                                       placeholder="Taxis"/>
                            </th>
                            <th>
                                <label for="numpassengers">Num. Passengers</label>
                                <input v-model="numpassengers" type="number"
                                       class="form-control" id="numpassengers"
                                       placeholder="Passengers"/>
                            </th>
                            <th>
                                <button type="button" class="btn btn-primary" data-sort="feature-name"
                                        id="generate-btn" @click="create">
                                    <i class="fa fa-legal"></i>&nbsp;&nbsp;Add
                                </button>
                            </th>
                        </tr>
                        <tr>
                            <th colspan="3">
                                <button type="button" class="btn btn-primary"
                                        data-sort="feature-name"
                                        @click="run"
                                        v-if="!is_running">
                                    <i class="fa fa-play"></i>
                                    &nbsp;&nbsp;Run
                                </button>
                                <button type="button" class="btn btn-primary"
                                        data-sort="feature-name"
                                        v-if="is_running"
                                        disabled>
                                    <i class="fa fa-spinner fa-spin"></i>
                                      Running
                                </button>
                            </th>
                        </tr>
                        </thead>
                        <tbody class="list">
                        <tr>
                            <th colspan="2">Waiting Time</th>
                            <td id="waiting">{{ waiting }}</td>
                        </tr>
                        <tr>
                            <th colspan="2">Total Time</th>
                            <td id="total">{{ totaltime }}</td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <slot></slot>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    </transition>
</template>

<script>
    export default {
        data() {
            return {
                numtaxis: 0,
                numpassengers: 0,
                hideSidebar: false
            }
        },
        computed: {
            waiting() {
                return this.$store.getters.get_waiting_time;
            },
            totaltime() {
                return this.$store.getters.get_total_time;
            },
            is_running() {
                return this.$store.getters.status;
            }
        },
        methods: {
            run() {
                axios.get("/run");
            },
            create() {
                let backport = $("#backport").val();
                axios.get("http://127.0.0.1:" + backport + "/generate/taxis/" + this.numtaxis + "/passengers/" + this.numpassengers);
            }
        }
    }
</script>

<style>
    .slide-enter-active, .slide-leave-active {
        transition: 350ms;
    }
    .slide-enter, .slide-leave {
        transform: translate(-100%, 0);
    }
    .slide-leave-to {
      transform: translate(-100%, 0);
    }
</style>
