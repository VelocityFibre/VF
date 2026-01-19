"use strict";
(() => {
var exports = {};
exports.id = 3424;
exports.ids = [3424];
exports.modules = {

20145: (module) => {
module.exports = require("next/dist/compiled/next-server/pages-api.runtime.prod.js")
},

71802: (module, __unused_webpack_exports, __webpack_require__) => {
module.exports = __webpack_require__(20145)
},

47153: (__unused_webpack_module, exports) => {
var RouteKind;
Object.defineProperty(exports, "x", {
    enumerable: !0,
    get: function() {
        return RouteKind
    }
}),
function(e) {
    e.PAGES = "PAGES",
    e.PAGES_API = "PAGES_API",
    e.APP_PAGE = "APP_PAGE",
    e.APP_ROUTE = "APP_ROUTE"
}(RouteKind || (RouteKind = {}))
},

56249: (__unused_webpack_module, exports) => {
Object.defineProperty(exports, "l", {
    enumerable: !0,
    get: function() {
        return function getExport(e, t) {
            return t in e ? e[t] : "then" in e && "function" == typeof e.then ? e.then(e => getExport(e, t)) : "function" == typeof e && "default" === t ? e : void 0
        }
    }
})
},

17398: (__unused_webpack_module, __webpack_exports__, __webpack_require__) => {
__webpack_require__.r(__webpack_exports__);
__webpack_require__.d(__webpack_exports__, {
    config: () => (config),
    default: () => (handler),
    routeModule: () => (routeModule)
});
var _pages_api_route_module__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(71802);
var _route_kind__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(47153);
var _helpers__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(56249);

// Handler function
const handler = async function(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    const { jobId } = req.query;

    if (!jobId || typeof jobId !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Job ID is required'
      });
    }

    // TODO: Implement history tracking in database schema
    // For now, return empty array
    return res.status(200).json({
      success: true,
      data: []
    });

  } catch (error) {
    console.error('Error fetching history:', error);

    return res.status(500).json({
      success: false,
      error: 'Failed to fetch history',
      message: error.message
    });
  }
};

const config = undefined;

const routeModule = new _pages_api_route_module__WEBPACK_IMPORTED_MODULE_0__.PagesAPIRouteModule({
    definition: {
        kind: _route_kind__WEBPACK_IMPORTED_MODULE_1__.x.PAGES_API,
        page: "/api/foto-reviews/[jobId]/history",
        pathname: "/api/foto-reviews/[jobId]/history",
        bundlePath: "",
        filename: ""
    },
    userland: { default: handler, config }
});

}

};

// Webpack runtime
var __webpack_require__ = require("../../../../webpack-api-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = (__webpack_exec__(17398));
module.exports = __webpack_exports__;

})();