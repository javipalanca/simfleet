<template>
    <div id="sidebar" class="bodycontainer table-scrollable">
        <div class="sidebar-wrapper">
            <div class="panel panel-default" id="features">
                <div class="panel-heading">
                    <h3 class="panel-title">Control Panel
                        <button type="button" class="btn btn-xs btn-default pull-right" id="sidebar-hide-btn"><i
                            class="fa fa-chevron-left"></i></button>
                    </h3>
                </div>
                <div class="panel-body">
                    <table class="table table-hover" id="feature-list">
                        <thead class="">
                            <tr>
                                <th><input type="number" class="form-control" id="numtaxis" placeholder="Taxis"/></th>
                            </tr>
                            <tr>
                                <th><input type="number" class="form-control" id="numpassengers" placeholder="Passengers"/>
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    <button type="button" class="btn btn-primary" data-sort="feature-name" id="generate-btn"><i class="fa fa-legal"></i>&nbsp;&nbsp;Add
                                    </button>
                                </th>
                            </tr>
                            <tr>
                                <th>
                                    <button type="button" class="btn btn-primary" data-sort="feature-name" id="play-btn"><i class="fa fa-play"></i>&nbsp;&nbsp;Run
                                    </button>
                                </th>
                            </tr>
                        </thead>
                        <tbody class="list">
                            <tr>
                                <th>Waiting Time</th>
                                <td id="waiting"></td>
                            </tr>
                            <tr>
                                <th>Total Time</th>
                                <td id="total"></td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <div class="" id="tree"></div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>
