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

/* harmony default export */ __webpack_exports__["a"] = ({
    data() {
        return {
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
var options = null
var ssrIdKey = 'data-vue-ssr-id'

// Force single-tag solution on IE6-9, which has a hard limit on the # of <style>
// tags it will allow on a page
var isOldIE = typeof navigator !== 'undefined' && /msie [6-9]\b/.test(navigator.userAgent.toLowerCase())

module.exports = function (parentId, list, _isProduction, _options) {
  isProduction = _isProduction

  options = _options || {}

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
  var styleElement = document.querySelector('style[' + ssrIdKey + '~="' + obj.id + '"]')

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
  if (options.ssrId) {
    styleElement.setAttribute(ssrIdKey, obj.id)
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
        transports: Array,
        customers: Array
    },
    data: function () {
        return {
            open: true,
            openTransport: true,
            openCustomer: true
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
        toggleTransport: function () {
            this.openTransport = !this.openTransport;
        },
        toggleCustomer: function () {
            this.openCustomer = !this.openCustomer;
        },
        status2str: function (status) {
            switch (status) {
                case 10:
                    return 'TRANSPORT_WAITING';
                case 11:
                    return 'TRANSPORT_MOVING_TO_CUSTOMER';
                case 12:
                    return 'TRANSPORT_IN_CUSTOMER_PLACE';
                case 13:
                    return 'TRANSPORT_MOVING_TO_DESTINATION';
                case 14:
                    return 'TRANSPORT_WAITING_FOR_APPROVAL';
                case 20:
                    return 'CUSTOMER_WAITING';
                case 21:
                    return 'CUSTOMER_IN_TRANSPORT';
                case 22:
                    return 'CUSTOMER_IN_DEST';
                case 24:
                    return 'CUSTOMER_ASSIGNED';
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
            transportIcon: L.icon({ iconUrl: 'assets/img/transport.png', iconSize: [38, 55] }),
            customerIcon: L.icon({ iconUrl: 'assets/img/customer.png', iconSize: [38, 40] }),
            stationIcon: L.icon({ iconUrl: 'assets/img/station.png', iconSize: [38, 40] })
        };
    },
    mounted() {
        this.init();
        this.loadEntities();
        setInterval(function () {
            this.loadEntities();
        }.bind(this), 100);
    },
    methods: {
        init: function () {
            axios.get("/init").then(data => {
                this.center = data.data.coords;
                this.zoom = data.data.zoom;
            });
        },
        loadEntities: function () {
            axios.get("/entities").then(data => {
                this.$store.commit('addTransports', data.data.transports);
                this.$store.commit('addCustomers', data.data.customers);
                this.$store.commit("addStations", data.data.stations);
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
        transports() {
            return this.$store.getters.get_transports;
        },
        customers() {
            return this.$store.getters.get_customers;
        },
        stations() {
            return this.$store.getters.get_stations;
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
        transports: [],
        customers: [],
        stations: [],
        paths: [],
        waiting_time: 0,
        total_time: 0,
        simulation_status: false,
        treedata: {}
    },
    mutations: {
        addTransports: (state, payload) => {
            if (payload.length > 0) {
                let new_paths = [];
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.transports, payload[i], transport_popup);

                    if (payload[i].path) {
                        new_paths.push({ latlngs: payload[i].path, color: get_color(payload[i].status) });
                    }
                }
                state.paths = new_paths;
            } else {
                state.transports = [];
                state.paths = [];
            }
        },
        addCustomers: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_item_in_collection(state.customers, payload[i], customer_popup);
                }
            } else {
                state.customers = [];
            }
        },
        addStations: (state, payload) => {
            if (payload.length > 0) {
                for (let i = 0; i < payload.length; i++) {
                    update_station_in_collection(state.stations, payload[i], station_popup);
                }
            } else {
                state.stations = [];
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
        get_transports: state => {
            return state.transports;
        },
        get_customers: state => {
            return state.customers;
        },
        get_stations: state => {
            return state.stations;
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
            return state.simulation_status && (state.customers.length || state.transports.length);
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
        item.icon_url = item.icon;
        if (item.icon) {
            item.icon = L.icon({ iconUrl: item.icon, iconSize: [38, 55] });
        } else {
            item.icon = L.icon({ iconUrl: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
                iconSize: [38, 55] });
        }
        collection.push(item);
    } else {
        collection[p].latlng = L.latLng(item.position[0], item.position[1]);
        collection[p].popup = get_popup(item);
        collection[p].speed = item.speed;
        collection[p].status = item.status;
        collection[p].icon_url = item.icon;
        if (item.icon) {
            collection[p].icon = L.icon({ iconUrl: item.icon, iconSize: [38, 55] });
        }
        collection[p].visible = item.status !== "CUSTOMER_IN_TRANSPORT" && item.status !== "CUSTOMER_IN_DEST" && item.status !== "CUSTOMER_LOCATION" && item.status !== "TRANSPORT_LOADING";
    }
};

let update_station_in_collection = function (collection, item, get_popup) {
    let p = getitem(collection, item);
    if (p === false) {
        item.latlng = L.latLng(item.position[0], item.position[1]);
        item.popup = get_popup(item);
        item.visible = true;
        item.icon_url = item.icon;
        if (item.icon) {
            item.icon = L.icon({ iconUrl: item.icon, iconSize: [38, 55] });
        }
        collection.push(item);
    } else {
        collection[p].popup = get_popup(item);
        collection[p].power = item.power;
        collection[p].places = item.places;
        collection[p].status = item.status;
        item.icon_url = item.icon;
        if (item.icon) {
            item.icon = L.icon({ iconUrl: item.icon, iconSize: [38, 55] });
        }
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
    15: "rgb(0, 255, 15)",
    "TRANSPORT_MOVING_TO_CUSTOMER": "rgb(255, 170, 0)",
    "TRANSPORT_MOVING_TO_DESTINATION": "rgb(0, 149, 255)",
    "TRANSPORT_MOVING_TO_STATION": "rgb(0, 255, 15)"
};

function get_color(status) {
    return color[status];
}

let statuses = {
    10: "TRANSPORT_WAITING",
    11: "TRANSPORT_MOVING_TO_CUSTOMER",
    12: "TRANSPORT_IN_CUSTOMER_PLACE",
    13: "TRANSPORT_MOVING_TO_DESTINY",
    14: "TRANSPORT_WAITING_FOR_APPROVAL",
    15: "TRANSPORT_MOVING_TO_STATION",
    16: "TRANSPORT_IN_STATION_PLACE",
    17: "TRANSPORT_WAITING_FOR_STATION_APPROVAL",
    18: "TRANSPORT_LOADING",
    19: "TRANSPORT_LOADED",
    //
    20: "CUSTOMER_WAITING",
    21: "CUSTOMER_IN_TRANSPORT",
    22: "CUSTOMER_IN_DEST",
    23: "CUSTOMER_LOCATION",
    24: "CUSTOMER_ASSIGNED",
    //
    30: "FREE_STATION",
    31: "BUSY_STATION"
};

function customer_popup(customer) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + customer.id + "</td></tr>" + "<tr><th>STATUS</th><td>" + customer.status + "</td></tr>" + "<tr><th>POSITION</th><td>" + customer.position + "</td></tr>" + "<tr><th>DEST</th><td>" + customer.dest + "</td></tr>" + "<tr><th>TRANSPORT</th><td>" + customer.transport + "</td></tr>" + "<tr><th>WAITING</th><td>" + customer.waiting + "</td></tr>" + "</table>";
}

function transport_popup(transport) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + transport.id + "</td></tr>" + "<tr><th>STATUS</th><td>" + transport.status + "</td></tr>" + "<tr><th>FLEETNAME</th><td>" + transport.fleet + "</td></tr>" + "<tr><th>TYPE</th><td>" + transport.service + "</td></tr>" + "<tr><th>CUSTOMER</th><td>" + transport.customer + "</td></tr>" + "<tr><th>POSITION</th><td>" + transport.position + "</td></tr>" + "<tr><th>DEST</th><td>" + transport.dest + "</td></tr>" + "<tr><th>ASSIGNMENTS</th><td>" + transport.assignments + "</td></tr>" + "<tr><th>SPEED</th><td>" + transport.speed + "</td></tr>" + "<tr><th>DISTANCE</th><td>" + transport.distance + "</td></tr>" + "<tr><th>AUTONOMY</th><td>" + transport.autonomy + " / " + transport.max_autonomy + "</td></tr>" + "</table>";
}

function station_popup(station) {
    return "<table class='table'><tbody><tr><th>NAME</th><td>" + station.id + "</td></tr>" + "<tr><th>STATUS</th><td>" + station.status + "</td></tr>" + "<tr><th>POSITION</th><td>" + station.position + "</td></tr>" + "<tr><th>POWERCHARGE</th><td>" + station.power + 'kW' + "</td></tr>" + "<tr><th>PLACES</th><td>" + station.places + "</td></tr>" + "</table>";
}

/***/ }),
/* 8 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_SidebarComponent_vue__ = __webpack_require__(1);
/* unused harmony namespace reexport */
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_2f0657f7_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_SidebarComponent_vue__ = __webpack_require__(9);
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
  __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_2f0657f7_hasScoped_false_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_SidebarComponent_vue__["a" /* default */],
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
var render = function () {var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('transition',{attrs:{"name":"slide","enter-active-class":"animated slideInLeft","leave-active-class":"animated slideOutLeft"}},[(!_vm.hideSidebar)?_c('div',{staticClass:"bodycontainer table-scrollable",attrs:{"id":"sidebar"}},[_c('div',{staticClass:"sidebar-wrapper"},[_c('div',{staticClass:"panel panel-default",attrs:{"id":"features"}},[_c('div',{staticClass:"panel-heading"},[_c('h3',{staticClass:"panel-title"},[_vm._v("Control Panel\n                    "),_c('button',{staticClass:"btn btn-xs btn-default pull-right",attrs:{"type":"button","id":"sidebar-hide-btn"},on:{"click":function($event){_vm.hideSidebar=!_vm.hideSidebar}}},[_c('i',{staticClass:"fa fa-chevron-left"})])])]),_vm._v(" "),_c('div',{staticClass:"panel-body"},[_c('table',{staticClass:"table table-hover",attrs:{"id":"feature-list"}},[_c('thead',{staticClass:"list"},[_c('tr',[_c('th',{attrs:{"colspan":"3"}},[(!_vm.is_running)?_c('button',{staticClass:"btn btn-primary",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.run}},[_c('i',{staticClass:"fa fa-play"}),_vm._v("\n                                  Run\n                            ")]):_vm._e(),_vm._v(" "),(_vm.is_running)?_c('button',{staticClass:"btn btn-primary",attrs:{"type":"button","data-sort":"feature-name","disabled":""}},[_c('i',{staticClass:"fa fa-spinner fa-spin"}),_vm._v("\n                                  Run\n                            ")]):_vm._e(),_vm._v(" "),(_vm.is_running)?_c('button',{staticClass:"btn btn-danger",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.stop}},[_c('i',{staticClass:"fa fa-stop"}),_vm._v("\n                                  Stop\n                            ")]):_vm._e(),_vm._v(" "),_c('button',{staticClass:"btn btn-warning",attrs:{"type":"button","data-sort":"feature-name"},on:{"click":_vm.clean}},[_c('i',{staticClass:"fa fa-trash-alt"}),_vm._v("\n                                  Clear\n                            ")])])])]),_vm._v(" "),_c('tbody',{staticClass:"list"},[_c('tr',[_c('th',{attrs:{"colspan":"2"}},[_vm._v("Waiting Time")]),_vm._v(" "),_c('td',{attrs:{"id":"waiting"}},[_vm._v(_vm._s(_vm.waiting))])]),_vm._v(" "),_c('tr',[_c('th',{attrs:{"colspan":"2"}},[_vm._v("Total Time")]),_vm._v(" "),_c('td',{attrs:{"id":"total"}},[_vm._v(_vm._s(_vm.totaltime))])]),_vm._v(" "),_c('tr',[_c('th',{attrs:{"colspan":"3"}},[_c('div',{staticClass:"dropdown"},[_c('button',{staticClass:"btn btn-info dropdown-toggle",attrs:{"type":"button","id":"dropdownMenu1","data-toggle":"dropdown","aria-haspopup":"true","aria-expanded":"true"}},[_c('i',{staticClass:"fa fa-download"}),_vm._v("  Download\n                                "),_c('span',{staticClass:"caret"})]),_vm._v(" "),_c('ul',{staticClass:"dropdown-menu",attrs:{"aria-labelledby":"dropdownMenu1"}},[_c('li',[_c('a',{attrs:{"href":"/download/excel/"}},[_vm._v("Excel")])]),_vm._v(" "),_c('li',[_c('a',{attrs:{"href":"/download/json/"}},[_vm._v("JSON")])])])])])]),_vm._v(" "),_c('tr',[_c('td',{attrs:{"colspan":"3"}},[_vm._t("default")],2)])])])])])])]):_vm._e()])}
var staticRenderFns = []
var esExports = { render: render, staticRenderFns: staticRenderFns }
/* harmony default export */ __webpack_exports__["a"] = (esExports);

/***/ }),
/* 10 */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_TreeView_vue__ = __webpack_require__(4);
/* unused harmony namespace reexport */
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_f0be742a_hasScoped_true_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_TreeView_vue__ = __webpack_require__(18);
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
var __vue_scopeId__ = "data-v-f0be742a"
/* moduleIdentifier (server only) */
var __vue_module_identifier__ = null
var Component = normalizeComponent(
  __WEBPACK_IMPORTED_MODULE_0__babel_loader_node_modules_vue_loader_lib_selector_type_script_index_0_TreeView_vue__["a" /* default */],
  __WEBPACK_IMPORTED_MODULE_1__node_modules_vue_loader_lib_template_compiler_index_id_data_v_f0be742a_hasScoped_true_buble_transforms_node_modules_vue_loader_lib_selector_type_template_index_0_TreeView_vue__["a" /* default */],
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
var update = __webpack_require__(3)("2ca428ad", content, true, {});

/***/ }),
/* 12 */
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__(2)(false);
// imports


// module
exports.push([module.i, ".item[data-v-f0be742a]{cursor:pointer}.bold[data-v-f0be742a]{font-weight:700}ul[data-v-f0be742a]{-webkit-padding-start:0;list-style-type:none}.list-group-item[data-v-f0be742a]{border-radius:0;position:relative;display:block;padding:10px 15px;margin-bottom:-2px;background-color:#fff;border:1px solid #ddd}.status-indicator[data-v-f0be742a]{float:right}", ""]);

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
var update = __webpack_require__(3)("2990344a", content, true, {});

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
var render = function () {var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('ul',{staticClass:"list-group",staticStyle:{"list-style-type":"none"},attrs:{"id":"treeview-ul"}},[_c('li',[_c('div',{staticClass:" bold list-group-item",on:{"click":_vm.toggleTransport}},[_c('span',{staticClass:"icon expand-icon glyphicon",class:{'glyphicon-chevron-down': _vm.openTransport, 'glyphicon-chevron-right': !_vm.openTransport}}),_vm._v("\n          Transports\n        "),_c('span',{staticClass:"badge"},[_vm._v(_vm._s(_vm.transports.length))])])]),_vm._v(" "),_vm._l((_vm.transports),function(transport){return _c('li',{directives:[{name:"show",rawName:"v-show",value:(_vm.openTransport),expression:"openTransport"}]},[_c('div',{directives:[{name:"tooltip",rawName:"v-tooltip.top",value:({content: _vm.status2str(transport.status), delay:100}),expression:"{content: status2str(transport.status), delay:100}",modifiers:{"top":true}}],staticClass:"list-group-item"},[_c('img',{attrs:{"src":transport.icon_url,"height":"20px"}}),_vm._v("  "+_vm._s(transport.id)+"\n          "),(transport.status == 'TRANSPORT_WAITING')?_c('status-indicator',{attrs:{"positive":""}}):(transport.status == 'TRANSPORT_WAITING_FOR_APPROVAL')?_c('status-indicator',{attrs:{"intermediary":""}}):(transport.status == 'TRANSPORT_MOVING_TO_CUSTOMER')?_c('status-indicator',{attrs:{"intermediary":"","pulse":""}}):(transport.status == 'TRANSPORT_MOVING_TO_DESTINATION')?_c('status-indicator',{attrs:{"active":"","pulse":""}}):_vm._e()],1)])}),_vm._v(" "),_c('li',[_c('div',{staticClass:" bold list-group-item",on:{"click":_vm.toggleCustomer}},[_c('span',{staticClass:"icon expand-icon glyphicon",class:{'glyphicon-chevron-down': _vm.openCustomer, 'glyphicon-chevron-right': !_vm.openCustomer}}),_vm._v("\n          Customers\n        "),_c('span',{staticClass:"badge"},[_vm._v(_vm._s(_vm.customers.length))])])]),_vm._v(" "),_vm._l((_vm.customers),function(customer){return _c('li',{directives:[{name:"show",rawName:"v-show",value:(_vm.openCustomer),expression:"openCustomer"}]},[_c('div',{directives:[{name:"tooltip",rawName:"v-tooltip.top",value:({content: _vm.status2str(customer.status), delay:100}),expression:"{content: status2str(customer.status), delay:100}",modifiers:{"top":true}}],staticClass:"list-group-item"},[_c('img',{attrs:{"src":customer.icon_url,"height":"20px"}}),_vm._v("  "+_vm._s(customer.id)+"\n          "),(customer.status == 'CUSTOMER_WAITING')?_c('status-indicator'):(customer.status == 'CUSTOMER_ASSIGNED')?_c('status-indicator',{attrs:{"intermediary":""}}):(customer.status == 'CUSTOMER_IN_TRANSPORT')?_c('status-indicator',{attrs:{"active":"","pulse":""}}):(customer.status == 'CUSTOMER_IN_DEST')?_c('status-indicator',{attrs:{"positive":""}}):_vm._e()],1)])})],2)}
var staticRenderFns = []
var esExports = { render: render, staticRenderFns: staticRenderFns }
/* harmony default export */ __webpack_exports__["a"] = (esExports);

/***/ })
/******/ ]);
//# sourceMappingURL=app.js.map