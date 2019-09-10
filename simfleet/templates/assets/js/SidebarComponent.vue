<template>
    <transition name="slide"
                enter-active-class="animated slideInLeft"
                leave-active-class="animated slideOutLeft">
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
                                      Run
                                </button>
                                <button type="button" class="btn btn-danger"
                                        data-sort="feature-name"
                                        @click="stop"
                                        v-if="is_running">
                                    <i class="fa fa-stop"></i>
                                    &nbsp;&nbsp;Stop
                                </button>
                                <button type="button" class="btn btn-warning"
                                        data-sort="feature-name"
                                        @click="clean">
                                    <i class="fa fa-trash-alt"></i>
                                    &nbsp;&nbsp;Clear
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
                            <th colspan="3">
                                <div class="dropdown">
                                  <button class="btn btn-info dropdown-toggle" type="button" id="dropdownMenu1"
                                          data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                                    <i class="fa fa-download"></i>&nbsp;&nbsp;Download
                                    <span class="caret"></span>
                                  </button>
                                  <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
                                    <li><a href="/download/excel/">Excel</a></li>
                                    <li><a href="/download/json/">JSON</a></li>
                                  </ul>
                                </div>

                            </th>
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
            stop() {
                axios.get("/stop");
            },
            clean() {
                axios.get("/clean");
            }
        }
    }
</script>
