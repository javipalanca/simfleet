/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "/app/";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 6);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ (function(module, exports) {

/* globals __VUE_SSR_CONTEXT__ */

// IMPORTANT: Do NOT use ES2015 features in this file.
// This module is a runtime utility for cleaner component module output and will
// be included in the final webpack user bundle.

module.exports = function normalizeComponent (
  rawScriptExports,
  compiledTemplate,
  functionalTemplate,
  injectStyles,
  scopeId,
  moduleIdentifier /* server only */
) {
  var esModule
  var scriptExports = rawScriptExports = rawScriptExports || {}

  // ES6 modules interop
  var type = typeof rawScriptExports.default
  if (type === 'object' || type === 'function') {
    esModule = rawScriptExports
    scriptExports = rawScriptExports.default
  }

  // Vue.extend constructor export interop
  var options = typeof scriptExports === 'function'
    ? scriptExports.options
    : scriptExports

  // render functions
  if (compiledTemplate) {
    options.render = compiledTemplate.render
    options.staticRenderFns = compiledTemplate.staticRenderFns
    options._compiled = true
  }

  // functional template
  if (functionalTemplate) {
    options.functional = true
  }

  // scopedId
  if (scopeId) {
    options._scopeId = scopeId
  }

  var hook
  if (moduleIdentifier) { // server build
    hook = function (context) {
      // 2.3 injection
      context =
        context || // cached call
        (this.$vnode && this.$vnode.ssrContext) || // stateful
        (this.parent && this.parent.$vnode && this.parent.$vnode.ssrContext) // functional
      // 2.2 with runInNewContext: true
      if (!context && typeof __VUE_SSR_CONTEXT__ !== 'undefined') {
        context = __VUE_SSR_CONTEXT__
      }
      // inject component styles
      if (injectStyles) {
        injectStyles.call(this, context)
      }
      // register component module identifier for async chunk inferrence
      if (context && context._registeredComponents) {
        context._registeredComponents.add(moduleIdentifier)
      }
    }
    // used by ssr in case component is cached and beforeCreate
    // never gets called
    options._ssrRegister = hook
  } else if (injectStyles) {
    hook = injectStyles
  }

  if (hook) {
    var functional = options.functional
    var existing = functional
      ? options.render
      : options.beforeCreate

    if (!functional) {
      // inject component registration as beforeCreate hook
      options.beforeCreate = existing
        ? [].concat(existing, hook)
        : [hook]
    } else {
      // for template-only hot-reload because in that case the render fn doesn't
      // go through the normalizer
      options._injectStyles = hook
      // register for functioal component in vue file
      options.render = function renderWithStyleInjection (h, context) {
        hook.call(context)
        return existing(h, context)
      }
    }
  }

  return {
    esModule: esModule,
    exports: scriptExports,
    options: options
  }
}


/***/ }),
/* 1 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//

/* harmony default export */ __webpack_exports__["a"] = ({
    data() {
        return {
            numtaxis: 0,
            numpassengers: 0,
            hideSidebar: false
        };
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
        },
        create() {
            axios.get("/generate/taxis/" + this.numtaxis + "/passengers/" + this.numpassengers);
        }
    }
});

/***/ }),
/* 2 */
/***/ (function(module, exports) {

/*
	MIT License http://www.opensource.org/licenses/mit-license.php
	Author Tobias Koppers @sokra
*/
// css base code, injected by the css-loader
module.exports = function(useSourceMap) {
	var list = [];

	// return the list of modules as css string
	list.toString = function toString() {
		return this.map(function (item) {
			var content = cssWithMappingToString(item, useSourceMap);
			if(item[2]) {
				return "@media " + item[2] + "{" + content + "}";
			} else {
				return content;
			}
		}).join("");
	};

	// import a list of modules into the list
	list.i = function(modules, mediaQuery) {
		if(typeof modules === "string")
			modules = [[null, modules, ""]];
		var alreadyImportedModules = {};
		for(var i = 0; i < this.length; i++) {
			var id = this[i][0];
			if(typeof id === "number")
				alreadyImportedModules[id] = true;
		}
		for(i = 0; i < modules.length; i++) {
			var item = modules[i];
			// skip already imported module
			// this implementation is not 100% perfect for weird media query combinations
			//  when a module is imported multiple times with different media queries.
			//  I hope this will never occur (Hey this way we have smaller bundles)
			if(typeof item[0] !== "number" || !alreadyImportedModules[item[0]]) {
				if(mediaQuery && !item[2]) {
					item[2] = mediaQuery;
				} else if(mediaQuery) {
					item[2] = "(" + item[2] + ") and (" + mediaQuery + ")";
				}
				list.push(item);
			}
		}
	};
	return list;
};

function cssWithMappingToString(item, useSourceMap) {
	var content = item[1] || '';
	var cssMapping = item[3];
	if (!cssMapping) {
		return content;
	}

	if (useSourceMap && typeof btoa === 'function') {
		var sourceMapping = toComment(cssMapping);
		var sourceURLs = cssMapping.sources.map(function (source) {
			return '/*# sourceURL=' + cssMapping.sourceRoot + source + ' */'
		});

		return [content].concat(sourceURLs).concat([sourceMapping]).join('\n');
	}

	return [content].join('\n');
}

// Adapted from convert-source-map (MIT)
function toComment(sourceMap) {
	// eslint-disable-next-line no-undef
	var base64 = btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap))));
	var data = 'sourceMappingURL=data:application/json;charset=utf-8;base64,' + base64;

	return '/*# ' + data + ' */';
}


/***/ }),
/* 3 */
/***/ (function(module, exports, __webpack_require__) {

/*
  MIT License http://www.opensource.org/licenses/mit-license.php
  Author Tobias Koppers @sokra
  Modified by Evan You @yyx990803
*/

var hasDocument = typeof document !== 'undefined'

if (typeof DEBUG !== 'undefined' && DEBUG) {
  if (!hasDocument) {
    throw new Error(
    'vue-style-loader cannot be used in a non-browser environment. ' +
    "Use { target: 'node' } in your Webpack config to indicate a server-rendering environment."
  ) }
}

var listToStyles = __webpack_require__(13)

/*
type StyleObject = {
  id: number;
  parts: Array<StyleObjectPart>
}

type StyleObjectPart = {
  css: string;
  media: string;
  sourceMap: ?string
}
*/

var stylesInDom = {/*
  [id: number]: {
    id: number,
    refs: number,
    parts: Array<(obj?: StyleObjectPart) => void>
  }
*/}

var head = hasDocument && (document.head || document.getElementsByTagName('head')[0])
var singletonElement = null
var singletonCounter = 0
var isProduction = false
var noop = function () {}

// Force single-tag solution on IE6-9, which has a hard limit on the # of <style>
// tags it will allow on a page
var isOldIE = typeof navigator !== 'undefined' && /msie [6-9]\b/.test(navigator.userAgent.toLowerCase())

module.exports = function (parentId, list, _isProduction) {
  isProduction = _isProduction

  var styles = listToStyles(parentId, list)
  addStylesToDom(styles)

  return function update (newList) {
    var mayRemove = []
    for (var i = 0; i < styles.length; i++) {
      var item = styles[i]
      var domStyle = stylesInDom[item.id]
      domStyle.refs--
      mayRemove.push(domStyle)
    }
    if (newList) {
      styles = listToStyles(parentId, newList)
      addStylesToDom(styles)
    } else {
      styles = []
    }
    for (var i = 0; i < mayRemove.length; i++) {
      var domStyle = mayRemove[i]
      if (domStyle.refs === 0) {
        for (var j = 0; j < domStyle.parts.length; j++) {
          domStyle.parts[j]()
        }
        delete stylesInDom[domStyle.id]
      }
    }
  }
}

function addStylesToDom (styles /* Array<StyleObject> */) {
  for (var i = 0; i < styles.length; i++) {
    var item = styles[i]
    var domStyle = stylesInDom[item.id]
    if (domStyle) {
      domStyle.refs++
      for (var j = 0; j < domStyle.parts.length; j++) {
        domStyle.parts[j](item.parts[j])
      }
      for (; j < item.parts.length; j++) {
        domStyle.parts.push(addStyle(item.parts[j]))
      }
      if (domStyle.parts.length > item.parts.length) {
        domStyle.parts.length = item.parts.length
      }
    } else {
      var parts = []
      for (var j = 0; j < item.parts.length; j++) {
        parts.push(addStyle(item.parts[j]))
      }
      stylesInDom[item.id] = { id: item.id, refs: 1, parts: parts }
    }
  }
}

function createStyleElement () {
  var styleElement = document.createElement('style')
  styleElement.type = 'text/css'
  head.appendChild(styleElement)
  return styleElement
}

function addStyle (obj /* StyleObjectPart */) {
  var update, remove
  var styleElement = document.querySelector('style[data-vue-ssr-id~="' + obj.id + '"]')

  if (styleElement) {
    if (isProduction) {
      // has SSR styles and in production mode.
      // simply do nothing.
      return noop
    } else {
      // has SSR styles but in dev mode.
      // for some reason Chrome can't handle source map in server-rendered
      // style tags - source maps in <style> only works if the style tag is
      // created and inserted dynamically. So we remove the server rendered
      // styles and inject new ones.
      styleElement.parentNode.removeChild(styleElement)
    }
  }

  if (isOldIE) {
    // use singleton mode for IE9.
    var styleIndex = singletonCounter++
    styleElement = singletonElement || (singletonElement = createStyleElement())
    update = applyToSingletonTag.bind(null, styleElement, styleIndex, false)
    remove = applyToSingletonTag.bind(null, styleElement, styleIndex, true)
  } else {
    // use multi-style-tag mode in all other cases
    styleElement = createStyleElement()
    update = applyToTag.bind(null, styleElement)
    remove = function () {
      styleElement.parentNode.removeChild(styleElement)
    }
  }

  update(obj)

  return function updateStyle (newObj /* StyleObjectPart */) {
    if (newObj) {
      if (newObj.css === obj.css &&
          newObj.media === obj.media &&
          newObj.sourceMap === obj.sourceMap) {
        return
      }
      update(obj = newObj)
    } else {
      remove()
    }
  }
}

var replaceText = (function () {
  var textStore = []

  return function (index, replacement) {
    textStore[index] = replacement
    return textStore.filter(Boolean).join('\n')
  }
})()

function applyToSingletonTag (styleElement, index, remove, obj) {
  var css = remove ? '' : obj.css

  if (styleElement.styleSheet) {
    styleElement.styleSheet.cssText = replaceText(index, css)
  } else {
    var cssNode = document.createTextNode(css)
    var childNodes = styleElement.childNodes
    if (childNodes[index]) styleElement.removeChild(childNodes[index])
    if (childNodes.length) {
      styleElement.insertBefore(cssNode, childNodes[index])
    } else {
      styleElement.appendChild(cssNode)
    }
  }
}

function applyToTag (styleElement, obj) {
  var css = obj.css
  var media = obj.media
  var sourceMap = obj.sourceMap

  if (media) {
    styleElement.setAttribute('media', media)
  }

  if (sourceMap) {
    // https://developer.chrome.com/devtools/docs/javascript-debugging
    // this makes source maps inside style tags work properly in Chrome
    css += '\n/*# sourceURL=' + sourceMap.sources[0] + ' */'
    // http://stackoverflow.com/a/26603875
    css += '\n/*# sourceMappingURL=data:application/json;base64,' + btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap)))) + ' */'
  }

  if (styleElement.styleSheet) {
    styleElement.styleSheet.cssText = css
  } else {
    while (styleElement.firstChild) {
      styleElement.removeChild(styleElement.firstChild)
    }
    styleElement.appendChild(document.createTextNode(css))
  }
}


/***/ }),
/* 4 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__StatusIndicator__ = __webpack_require__(14);
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//
//




/* harmony default export */ __webpack_exports__["a"] = ({
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
        };
    },
    computed: {
        isFolder: function () {
            return this.model.children;
        }
    },
    methods: {
        toggle: function () {
            if (this.isFolder) {
                this.open = !this.open;
            }
        },
        toggleTaxi: function () {
            this.openTaxi = !this.openTaxi;
        },
        togglePass: function () {
            this.openPass = !this.openPass;
        },
        status2str: function (status) {
            switch (status) {
                case 10:
                    return 'TAXI_WAITING';
                case 11:
                    return 'TAXI_MOVING_TO_PASSENGER';
                case 12:
                    return 'TAXI_IN_PASSENGER_PLACE';
                case 13:
                    return 'TAXI_MOVING_TO_DESTINATION';
                case 14:
                    return 'TAXI_WAITING_FOR_APPROVAL';
                case 20:
                    return 'PASSENGER_WAITING';
                case 21:
                    return 'PASSENGER_IN_TAXI';
                case 22:
                    return 'PASSENGER_IN_DEST';
                case 24:
                    return 'PASSENGER_ASSIGNED';
            }
            return status;
        }
    },
    components: {
        'status-indicator': __WEBPACK_IMPORTED_MODULE_0__StatusIndicator__["a" /* default */]
    }
});

/***/ }),
/* 5 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
//
//
//
//

/* harmony default export */ __webpack_exports__["a"] = ({
  name: 'StatusIndicator'
});

/***/ }),
/* 6 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__store_js__ = __webpack_require__(7);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__SidebarComponent_vue__ = __webpack_require__(8);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2__TreeView__ = __webpack_require__(10);





Vue.use(vueDirectiveTooltip);

new Vue({
    el: '#app',
    store: __WEBPACK_IMPORTED_MODULE_0__store_js__["a" /* store */],
    components: {
        'v-map': Vue2Leaflet.Map,
        'v-tilelayer': Vue2Leaflet.TileLayer,
        'v-marker': Vue2Leaflet.Marker,
        'v-polyline': Vue2Leaflet.Polyline,
        'v-popup': Vue2Leaflet.Popup,
        SidebarComponent: __WEBPACK_IMPORTED_MODULE_1__SidebarComponent_vue__["a" /* default */],
        'tree-view': __WEBPACK_IMPORTED_MODULE_2__TreeView__["a" /* default */]
    },
    data() {
        return {
            zoom: 14,
            center: [39.47, -0.37],
            url: 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            taxiIcon: L.icon({ iconUrl: 'assets/img/taxi.png', iconSize: [38, 55] }),
            passengerIcon: L.icon({ iconUrl: 'assets/img/passenger.png', iconSize: [38, 40] })
        };
    },
    mounted() {
        this.loadEntities();
        setInterval(function () {
            this.loadEntities();
        }.bind(this), 100);
    },
    methods: {
        loadEntities: function () {
            axios.get("/entities").then(data => {
                this.$store.commit('addTaxis', data.data.taxis);
                this.$store.commit('addPassengers', data.data.passengers);
                this.$store.state.waiting_time = data.data.stats.waiting;
                this.$store.state.total_time = data.data.stats.totaltime;
                this.$store.commit('update_simulation_status', data.data.stats);
                this.$store.commit("update_tree", data.data.tree);
            }).catch(error => {});
        },
        set_speed: function (event, item) {
            event.target._icon.style[L.DomUtil.TRANSITION] = 'all ' + item.speed + 'ms linear';
        },
        showSidebar: function () {
            this.$refs.sidebar.hideSidebar = !this.$refs.sidebar.hideSidebar;
        }
    },
    computed: {
        taxis() {
            return this.$store.getters.get_taxis;
        },
        passengers() {
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

/***/ }),
/* 7 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Vue.use(Vuex);

const store = new Vuex.Store({
    state: {
        taxis: [],
        passengers: [],
        paths: [],
        waiting_time: 0,
        total_time: 0,
        simulation_status: false,
        treedata: {}
    },
    mutations: {
        addTaxis: (state, payload) => {
            if (payload.length > 0) {
                let new_paths = [];
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.taxis, payload[i], taxi_popup);

                    if (payload[i].path) {
                        new_paths.push({ latlngs: payload[i].path, color: get_color(payload[i].status) });
                    }
                }
                state.paths = new_paths;
            } else {
                state.taxis = [];
                state.paths = [];
            }
        },
        addPassengers: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.passengers, payload[i], passenger_popup);
                }
            } else {
                state.passengers = [];
            }
        },
        update_simulation_status: (state, stats) => {
            if (!stats.is_running) state.simulation_status = false;else {
                state.simulation_status = !stats.finished;
            }
        },
        update_tree: (state, payload) => {
            state.treedata = payload;
        }
    },
    getters: {
        get_taxis: state => {
            return state.taxis;
        },
        get_passengers: state => {
            return state.passengers;
        },
        get_paths: state => {
            return state.paths;
        },
        get_waiting_time: state => {
            return state.waiting_time;
        },
        get_total_time: state => {
            return state.total_time;
        },
        status: state => {
            return state.simulation_status && (state.passengers.length || state.taxis.length);
        },
        tree: state => {
            return state.treedata;
        }
    }
});
/* harmony export (immutable) */ __webpack_exports__["a"] = store;


let update_item_in_collection = function (collection, item, get_popup) {
    let p = getitem(collection, item);
    if (p === false) {
        item.latlng = L.latLng(item.position[0], item.position[1]);
        item.popup = get_popup(item);
        item.visible = true;
        collection.push(item);
    } else {
        collection[p].latlng = L.latLng(item.position[0], item.position[1]);
        collection[p].popup = get_popup(item);
        collection[p].speed = item.speed;
        collection[p].status = item.status;
        collection[p].visible = item.status !== "PASSENGER_IN_TAXI" && item.status !== "PASSENGER_IN_DEST" && item.status !== "PASSENGER_LOCATION";
    }
};

let getitem = function (collection, item) {
    for (let j = 0; j < collection.length; j++) {
        if (collection[j].id === item.id) {
            return j;
        }
    }
    return false;
};

let color = {
    11: "rgb(255, 170, 0)",
    13: "rgb(0, 149, 255)",
    "TAXI_MOVING_TO_PASSENGER": "rgb(255, 170, 0)",
    "TAXI_MOVING_TO_DESTINATION": "rgb(0, 149, 255)"
};

function get_color(status) {
    return color[status];
}

let statuses = {
    10: "TAXI_WAITING",
    11: "TAXI_MOVING_TO_PASSENGER",
    12: "TAXI_IN_PASSENGER_PLACE",
    13: "TAXI_MOVING_TO_DESTINY",
    14: "TAXI_WAITING_FOR_APPROVAL",
    //
    20: "PASSENGER_WAITING",
    21: "PASSENGER_IN_TAXI",
    22: "PASSENGER_IN_DEST",
    23: "PASSENGER_LOCATION",
    24: "PASSENGER_ASSIGNED"
};

function passenger_popup(passenger) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + passenger.id + "</td></tr>" + "<tr><th>STATUS</th><td>" + passenger.status + "</td></tr>" + "<tr><th>POSITION</th><td>" + passenger.position + "</td></tr>" + "<tr><th>DEST</th><td>" + passenger.dest + "</td></tr>" + "<tr><th>TAXI</th><td>" + passenger.taxi + "</td></tr>" + "<tr><th>WAITING</th><td>" + passenger.waiting + "</td></tr>" + "</table>";
}

function taxi_popup(taxi) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + taxi.id + "</td></tr>" + "<tr><th>STATUS</th><td>" + taxi.status + "</td></tr>" + "<tr><th>PASSENGER</th><td>" + taxi.passenger + "</td></tr>" + "<tr><th>POSITION</th><td>" + taxi.position + "</td></tr>" + "<tr><th>DEST</th><td>" + taxi.dest + "</td></tr>" + "<tr><th>ASSIGNMENTS</th><td>" + taxi.assignments + "</td></tr>" + "<tr><th>SPEED</th><td>" + taxi.speed + "</td></tr>" + "<tr><th>DISTANCE</th><td>" + taxi.distance + "</td></tr>" + "</table>";
}

/***/ }),
/* 8 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_SidebarComponent_vue__ = __webpack_require__(1);
/* unused harmony namespace reexport */
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_89537608_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_SidebarComponent_vue__ = __webpack_require__(9);
var normalizeComponent = __webpack_require__(0)
/* script */


/* template */

/* template functional */
var __vue_template_functional__ = false
/* styles */
var __vue_styles__ = null
/* scopeId */
var __vue_scopeId__ = null
/* moduleIdentifier (server only) */
var __vue_module_identifier__ = null
var Component = normalizeComponent(
  __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_SidebarComponent_vue__["a" /* default */],
  __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_89537608_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_SidebarComponent_vue__["a" /* default */],
  __vue_template_functional__,
  __vue_styles__,
  __vue_scopeId__,
  __vue_module_identifier__
)

/* harmony default export */ __webpack_exports__["a"] = (Component.exports);


/***/ }),
/* 9 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
var render = function () {var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('transition',{attrs:{"name":"slide","enter-active-class":"animated slideInLeft","leave-active-class":"animated slideOutLeft"}},[(!_vm.hideSidebar)?_c('div',{staticClass:"bodycontainer table-scrollable",attrs:{"id":"sidebar"}},[_c('div',{staticClass:"sidebar-wrapper"},[_c('div',{staticClass:"panel panel-default",attrs:{"id":"features"}},[_c('div',{staticClass:"panel-heading"},[_c('h3',{staticClass:"panel-title"},[_vm._v("Control Panel\n                    "),_c('button',{staticClass:"btn btn-xs btn-default pull-right",attrs:{"type":"button","id":"sidebar-hide-btn"},on:{"click":function($event){_vm.hideSidebar=!_vm.hideSidebar}}},[_c('i',{staticClass:"fa fa-chevron-left"})])])]),_vm._v(" "),_c('div',{staticClass:"panel-body"},[_c('table',{staticClass:"table table-hover",attrs:{"id":"feature-list"}},[_c('thead',{staticClass:"list"},[_c('tr',[_c('th',[_c('label',{attrs:{"for":"numtaxis"}},[_vm._v("Num. Taxis")]),_vm._v(" "),_c('input',{directives:[{name:"model",rawName:"v-model",value:(_vm.numtaxis),expression:"numtaxis"}],staticClass:"form-control",attrs:{"type":"number","min":"0","id":"numtaxis","placeholder":"Taxis"},domProps:{"value":(_vm.numtaxis)},on:{"input":function($event){if($event.target.composing){ return; }_vm.numtaxis=$event.target.value}}})]),_vm._v(" "),_c('th',[_c('label',{attrs:{"for":"numpassengers"}},[_vm._v("Num. Passengers")]),_vm._v(" "),_c('input',{directives:[{name:"model",rawName:"v-model",value:(_vm.numpassengers),expression:"numpassengers"}],staticClass:"form-control",attrs:{"type":"number","min":"0","id":"numpassengers","placeholder":"Passengers"},domProps:{"value":(_vm.numpassengers)},on:{"input":function($event){if($event.target.composing){ return; }_vm.numpassengers=$event.target.value}}})]),_vm._v(" "),_c('th',[_c('button',{staticClass:"btn btn-primary",attrs:{"type":"button","data-sort":"feature-name","id":"generate-btn"},on:{"click":_vm.create}},[_c('i',{staticClass:"far fa-address-book"}),_vm._v("  Add\n                            ")])])]),_vm._v(" "),_c('tr',[_c('th',{attrs:{"colspan":"3"}},[(!_vm.is_running)?_c('button',{staticClass:"btn btn-primary",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.run}},[_c('i',{staticClass:"fa fa-play"}),_vm._v("\n                                  Run\n                            ")]):_vm._e(),_vm._v(" "),(_vm.is_running)?_c('button',{staticClass:"btn btn-primary",attrs:{"type":"button","data-sort":"feature-name","disabled":""}},[_c('i',{staticClass:"fa fa-spinner fa-spin"}),_vm._v("\n                                  Run\n                            ")]):_vm._e(),_vm._v(" "),(_vm.is_running)?_c('button',{staticClass:"btn btn-danger",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.stop}},[_c('i',{staticClass:"fa fa-stop"}),_vm._v("\n                                  Stop\n                            ")]):_vm._e(),_vm._v(" "),_c('button',{staticClass:"btn btn-warning",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.clean}},[_c('i',{staticClass:"fa fa-trash-alt"}),_vm._v("\n                                  Clear\n                            ")])])])]),_vm._v(" "),_c('tbody',{staticClass:"list"},[_c('tr',[_c('th',{attrs:{"colspan":"2"}},[_vm._v("Waiting Time")]),_vm._v(" "),_c('td',{attrs:{"id":"waiting"}},[_vm._v(_vm._s(_vm.waiting))])]),_vm._v(" "),_c('tr',[_c('th',{attrs:{"colspan":"2"}},[_vm._v("Total Time")]),_vm._v(" "),_c('td',{attrs:{"id":"total"}},[_vm._v(_vm._s(_vm.totaltime))])]),_vm._v(" "),_c('tr',[_c('th',{attrs:{"colspan":"3"}},[_c('div',{staticClass:"dropdown"},[_c('button',{staticClass:"btn btn-info dropdown-toggle",attrs:{"type":"button","id":"dropdownMenu1","data-toggle":"dropdown","aria-haspopup":"true","aria-expanded":"true"}},[_c('i',{staticClass:"fa fa-download"}),_vm._v("  Download\n                                "),_c('span',{staticClass:"caret"})]),_vm._v(" "),_c('ul',{staticClass:"dropdown-menu",attrs:{"aria-labelledby":"dropdownMenu1"}},[_c('li',[_c('a',{attrs:{"href":"/download/excel/"}},[_vm._v("Excel")])]),_vm._v(" "),_c('li',[_c('a',{attrs:{"href":"/download/json/"}},[_vm._v("JSON")])])])])])]),_vm._v(" "),_c('tr',[_c('td',{attrs:{"colspan":"3"}},[_vm._t("default")],2)])])])])])])]):_vm._e()])}
var staticRenderFns = []
var esExports = { render: render, staticRenderFns: staticRenderFns }
/* harmony default export */ __webpack_exports__["a"] = (esExports);

/***/ }),
/* 10 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_TreeView_vue__ = __webpack_require__(4);
/* unused harmony namespace reexport */
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_abc6a0e0_hasScoped_true_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_TreeView_vue__ = __webpack_require__(18);
function injectStyle (ssrContext) {
  __webpack_require__(11)
}
var normalizeComponent = __webpack_require__(0)
/* script */


/* template */

/* template functional */
var __vue_template_functional__ = false
/* styles */
var __vue_styles__ = injectStyle
/* scopeId */
var __vue_scopeId__ = "data-v-abc6a0e0"
/* moduleIdentifier (server only) */
var __vue_module_identifier__ = null
var Component = normalizeComponent(
  __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_TreeView_vue__["a" /* default */],
  __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_abc6a0e0_hasScoped_true_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_TreeView_vue__["a" /* default */],
  __vue_template_functional__,
  __vue_styles__,
  __vue_scopeId__,
  __vue_module_identifier__
)

/* harmony default export */ __webpack_exports__["a"] = (Component.exports);


/***/ }),
/* 11 */
/***/ (function(module, exports, __webpack_require__) {

// style-loader: Adds some css to the DOM by adding a <style> tag

// load the styles
var content = __webpack_require__(12);
if(typeof content === 'string') content = [[module.i, content, '']];
if(content.locals) module.exports = content.locals;
// add the styles to the DOM
var update = __webpack_require__(3)("5d098929", content, true);

/***/ }),
/* 12 */
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__(2)(false);
// imports


// module
exports.push([module.i, ".item[data-v-abc6a0e0]{cursor:pointer}.bold[data-v-abc6a0e0]{font-weight:700}ul[data-v-abc6a0e0]{-webkit-padding-start:0;list-style-type:none}.list-group-item[data-v-abc6a0e0]{border-radius:0;position:relative;display:block;padding:10px 15px;margin-bottom:-2px;background-color:#fff;border:1px solid #ddd}.status-indicator[data-v-abc6a0e0]{float:right}", ""]);

// exports


/***/ }),
/* 13 */
/***/ (function(module, exports) {

/**
 * Translates the list format produced by css-loader into something
 * easier to manipulate.
 */
module.exports = function listToStyles (parentId, list) {
  var styles = []
  var newStyles = {}
  for (var i = 0; i < list.length; i++) {
    var item = list[i]
    var id = item[0]
    var css = item[1]
    var media = item[2]
    var sourceMap = item[3]
    var part = {
      id: parentId + ':' + i,
      css: css,
      media: media,
      sourceMap: sourceMap
    }
    if (!newStyles[id]) {
      styles.push(newStyles[id] = { id: id, parts: [part] })
    } else {
      newStyles[id].parts.push(part)
    }
  }
  return styles
}


/***/ }),
/* 14 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_StatusIndicator_vue__ = __webpack_require__(5);
/* unused harmony namespace reexport */
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_2702793e_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_StatusIndicator_vue__ = __webpack_require__(17);
function injectStyle (ssrContext) {
  __webpack_require__(15)
}
var normalizeComponent = __webpack_require__(0)
/* script */


/* template */

/* template functional */
var __vue_template_functional__ = false
/* styles */
var __vue_styles__ = injectStyle
/* scopeId */
var __vue_scopeId__ = null
/* moduleIdentifier (server only) */
var __vue_module_identifier__ = null
var Component = normalizeComponent(
  __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_StatusIndicator_vue__["a" /* default */],
  __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_2702793e_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_StatusIndicator_vue__["a" /* default */],
  __vue_template_functional__,
  __vue_styles__,
  __vue_scopeId__,
  __vue_module_identifier__
)

/* harmony default export */ __webpack_exports__["a"] = (Component.exports);


/***/ }),
/* 15 */
/***/ (function(module, exports, __webpack_require__) {

// style-loader: Adds some css to the DOM by adding a <style> tag

// load the styles
var content = __webpack_require__(16);
if(typeof content === 'string') content = [[module.i, content, '']];
if(content.locals) module.exports = content.locals;
// add the styles to the DOM
var update = __webpack_require__(3)("26b830bb", content, true);

/***/ }),
/* 16 */
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__(2)(false);
// imports


// module
exports.push([module.i, "body{--status-indicator-size:10px;--status-indicator-animation-duration:2s;--status-indicator-color:#d8e2e9;--status-indicator-color-semi:rgba(216,226,233,.5);--status-indicator-color-transparent:rgba(216,226,233,0);--status-indicator-color-active:#0095ff;--status-indicator-color-active-semi:rgba(0,149,255,.5);--status-indicator-color-active-transparent:rgba(0,149,255,0);--status-indicator-color-positive:#4bd28f;--status-indicator-color-positive-semi:rgba(75,210,143,.5);--status-indicator-color-positive-transparent:rgba(75,210,143,0);--status-indicator-color-intermediary:#fa0;--status-indicator-color-intermediary-semi:rgba(255,170,0,.5);--status-indicator-color-intermediary-transparent:rgba(255,170,0,0);--status-indicator-color-negative:#ff4d4d;--status-indicator-color-negative-semi:rgba(255,77,77,.5);--status-indicator-color-negative-transparent:rgba(255,77,77,0)}@keyframes status-indicator-pulse{0%{box-shadow:0 0 0 0 var(--status-indicator-color-semi)}70%{box-shadow:0 0 0 var(--status-indicator-size) var(--status-indicator-color-transparent)}to{box-shadow:0 0 0 0 var(--status-indicator-color-transparent)}}@keyframes status-indicator-pulse-active{0%{box-shadow:0 0 0 0 var(--status-indicator-color-active-semi)}70%{box-shadow:0 0 0 var(--status-indicator-size) var(--status-indicator-color-active-transparent)}to{box-shadow:0 0 0 0 var(--status-indicator-color-active-transparent)}}@keyframes status-indicator-pulse-positive{0%{box-shadow:0 0 0 0 var(--status-indicator-color-positive-semi)}70%{box-shadow:0 0 0 var(--status-indicator-size) var(--status-indicator-color-positive-transparent)}to{box-shadow:0 0 0 0 var(--status-indicator-color-positive-transparent)}}@keyframes status-indicator-pulse-intermediary{0%{box-shadow:0 0 0 0 var(--status-indicator-color-intermediary-semi)}70%{box-shadow:0 0 0 var(--status-indicator-size) var(--status-indicator-color-intermediary-transparent)}to{box-shadow:0 0 0 0 var(--status-indicator-color-intermediary-transparent)}}@keyframes status-indicator-pulse-negative{0%{box-shadow:0 0 0 0 var(--status-indicator-color-negative-semi)}70%{box-shadow:0 0 0 var(--status-indicator-size) var(--status-indicator-color-negative-transparent)}to{box-shadow:0 0 0 0 var(--status-indicator-color-negative-transparent)}}.status-indicator{display:inline-block;border-radius:50%;cursor:pointer;width:var(--status-indicator-size);height:var(--status-indicator-size);background-color:var(--status-indicator-color)}.status-indicator[pulse]{animation-name:status-indicator-pulse;animation-duration:var(--status-indicator-animation-duration);animation-timing-function:ease-in-out;animation-iteration-count:infinite;animation-direction:normal;animation-delay:0;animation-fill-mode:none}.status-indicator[active]{background-color:var(--status-indicator-color-active)}.status-indicator[active][pulse]{animation-name:status-indicator-pulse-active}.status-indicator[positive]{background-color:var(--status-indicator-color-positive)}.status-indicator[positive],.status-indicator[positive][pulse]{animation-name:status-indicator-pulse-positive}.status-indicator[intermediary]{background-color:var(--status-indicator-color-intermediary)}.status-indicator[intermediary][pulse]{animation-name:status-indicator-pulse-intermediary}.status-indicator[negative]{background-color:var(--status-indicator-color-negative)}.status-indicator[negative],.status-indicator[negative][pulse]{animation-name:status-indicator-pulse-negative}", ""]);

// exports


/***/ }),
/* 17 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
var render = function () {var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('span',{staticClass:"status-indicator"})}
var staticRenderFns = []
var esExports = { render: render, staticRenderFns: staticRenderFns }
/* harmony default export */ __webpack_exports__["a"] = (esExports);

/***/ }),
/* 18 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
var render = function () {var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('ul',{staticClass:"list-group",staticStyle:{"list-style-type":"none"},attrs:{"id":"treeview-ul"}},[_c('li',[_c('div',{staticClass:" bold list-group-item",on:{"click":_vm.toggleTaxi}},[_c('span',{staticClass:"icon expand-icon glyphicon",class:{'glyphicon-chevron-down': _vm.openTaxi, 'glyphicon-chevron-right': !_vm.openTaxi}}),_vm._v("\n          Taxis\n        "),_c('span',{staticClass:"badge"},[_vm._v(_vm._s(_vm.taxis.length))])])]),_vm._v(" "),_vm._l((_vm.taxis),function(o){return _c('li',{directives:[{name:"show",rawName:"v-show",value:(_vm.openTaxi),expression:"openTaxi"}]},[_c('div',{directives:[{name:"tooltip",rawName:"v-tooltip.top",value:({content: _vm.status2str(o.status), delay:100}),expression:"{content: status2str(o.status), delay:100}",modifiers:{"top":true}}],staticClass:"list-group-item"},[_c('span',{staticClass:"fa fa-taxi"}),_vm._v("  "+_vm._s(o.id)+"\n          "),(o.status == 'TAXI_WAITING')?_c('status-indicator',{attrs:{"positive":""}}):(o.status == 'TAXI_WAITING_FOR_APPROVAL')?_c('status-indicator',{attrs:{"intermediary":""}}):(o.status == 'TAXI_MOVING_TO_PASSENGER')?_c('status-indicator',{attrs:{"intermediary":"","pulse":""}}):(o.status == 'TAXI_MOVING_TO_DESTINATION')?_c('status-indicator',{attrs:{"active":"","pulse":""}}):_vm._e()],1)])}),_vm._v(" "),_c('li',[_c('div',{staticClass:" bold list-group-item",on:{"click":_vm.togglePass}},[_c('span',{staticClass:"icon expand-icon glyphicon",class:{'glyphicon-chevron-down': _vm.openPass, 'glyphicon-chevron-right': !_vm.openPass}}),_vm._v("\n          Passengers\n        "),_c('span',{staticClass:"badge"},[_vm._v(_vm._s(_vm.passengers.length))])])]),_vm._v(" "),_vm._l((_vm.passengers),function(passenger){return _c('li',{directives:[{name:"show",rawName:"v-show",value:(_vm.openPass),expression:"openPass"}]},[_c('div',{directives:[{name:"tooltip",rawName:"v-tooltip.top",value:({content: _vm.status2str(passenger.status), delay:100}),expression:"{content: status2str(passenger.status), delay:100}",modifiers:{"top":true}}],staticClass:"list-group-item"},[_c('span',{staticClass:"fa fa-user"}),_vm._v("  "+_vm._s(passenger.id)+"\n          "),(passenger.status == 'PASSENGER_WAITING')?_c('status-indicator'):(passenger.status == 'PASSENGER_ASSIGNED')?_c('status-indicator',{attrs:{"intermediary":""}}):(passenger.status == 'PASSENGER_IN_TAXI')?_c('status-indicator',{attrs:{"active":"","pulse":""}}):(passenger.status == 'PASSENGER_IN_DEST')?_c('status-indicator',{attrs:{"positive":""}}):_vm._e()],1)])})],2)}
var staticRenderFns = []
var esExports = { render: render, staticRenderFns: staticRenderFns }
/* harmony default export */ __webpack_exports__["a"] = (esExports);

/***/ })
/******/ ]);
//# sourceMappingURL=app.js.map