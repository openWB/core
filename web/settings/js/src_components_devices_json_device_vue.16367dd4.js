"use strict";
/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(self["webpackChunkopenwb_ui_settings"] = self["webpackChunkopenwb_ui_settings"] || []).push([["src_components_devices_json_device_vue"],{

/***/ "./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=script&lang=js":
/*!*****************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=script&lang=js ***!
  \*****************************************************************************************************************************************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony default export */ __webpack_exports__[\"default\"] = ({\n  name: \"DeviceJson\",\n  emits: [\"update:configuration\"],\n  props: {\n    configuration: {\n      type: Object,\n      required: true\n    },\n    componentId: {\n      required: true\n    }\n  },\n  methods: {\n    updateConfiguration(event, path = undefined) {\n      this.$emit(\"update:configuration\", {\n        value: event,\n        object: path\n      });\n    }\n  }\n});\n\n//# sourceURL=webpack://openwb-ui-settings/./src/components/devices/json/device.vue?./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use%5B0%5D!./node_modules/vue-loader/dist/index.js??ruleSet%5B0%5D.use%5B0%5D");

/***/ }),

/***/ "./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[3]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=template&id=5f82586a":
/*!*********************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[3]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=template&id=5f82586a ***!
  \*********************************************************************************************************************************************************************************************************************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"render\": function() { return /* binding */ render; }\n/* harmony export */ });\n/* harmony import */ var vue__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! vue */ \"./node_modules/vue/dist/vue.runtime.esm-bundler.js\");\n\nconst _hoisted_1 = {\n  class: \"device-json\"\n};\nconst _hoisted_2 = {\n  class: \"small\"\n};\nconst _hoisted_3 = /*#__PURE__*/(0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)(\"br\", null, null, -1 /* HOISTED */);\n\nfunction render(_ctx, _cache, $props, $setup, $data, $options) {\n  const _component_openwb_base_heading = (0,vue__WEBPACK_IMPORTED_MODULE_0__.resolveComponent)(\"openwb-base-heading\");\n  const _component_openwb_base_text_input = (0,vue__WEBPACK_IMPORTED_MODULE_0__.resolveComponent)(\"openwb-base-text-input\");\n  return (0,vue__WEBPACK_IMPORTED_MODULE_0__.openBlock)(), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementBlock)(\"div\", _hoisted_1, [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)(_component_openwb_base_heading, null, {\n    default: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(() => [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(\" Einstellungen für JSON \"), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createElementVNode)(\"span\", _hoisted_2, \"(Modul: \" + (0,vue__WEBPACK_IMPORTED_MODULE_0__.toDisplayString)(_ctx.$options.name) + \")\", 1 /* TEXT */)]),\n\n    _: 1 /* STABLE */\n  }), (0,vue__WEBPACK_IMPORTED_MODULE_0__.createVNode)(_component_openwb_base_text_input, {\n    title: \"URL\",\n    subtype: \"url\",\n    required: \"\",\n    \"model-value\": $props.configuration.url,\n    \"onUpdate:modelValue\": _cache[0] || (_cache[0] = $event => $options.updateConfiguration($event, 'configuration.url'))\n  }, {\n    help: (0,vue__WEBPACK_IMPORTED_MODULE_0__.withCtx)(() => [(0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(\" Es wird eine komplette URL erwartet mit Angaben zum Protokoll, IP oder Hostnamen, optional einem Port und einem Pfad. Die Antwort muss ein json-Objekt sein.\"), _hoisted_3, (0,vue__WEBPACK_IMPORTED_MODULE_0__.createTextVNode)(\" Beispiel: http://192.168.1.1:8080/json?data=1 \")]),\n    _: 1 /* STABLE */\n  }, 8 /* PROPS */, [\"model-value\"])]);\n}\n\n//# sourceURL=webpack://openwb-ui-settings/./src/components/devices/json/device.vue?./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use%5B0%5D!./node_modules/vue-loader/dist/templateLoader.js??ruleSet%5B1%5D.rules%5B3%5D!./node_modules/vue-loader/dist/index.js??ruleSet%5B0%5D.use%5B0%5D");

/***/ }),

/***/ "./src/components/devices/json/device.vue":
/*!************************************************!*\
  !*** ./src/components/devices/json/device.vue ***!
  \************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _device_vue_vue_type_template_id_5f82586a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./device.vue?vue&type=template&id=5f82586a */ \"./src/components/devices/json/device.vue?vue&type=template&id=5f82586a\");\n/* harmony import */ var _device_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./device.vue?vue&type=script&lang=js */ \"./src/components/devices/json/device.vue?vue&type=script&lang=js\");\n/* harmony import */ var _opt_openWB_dev_openwb_ui_settings_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./node_modules/vue-loader/dist/exportHelper.js */ \"./node_modules/vue-loader/dist/exportHelper.js\");\n\n\n\n\n;\nconst __exports__ = /*#__PURE__*/(0,_opt_openWB_dev_openwb_ui_settings_node_modules_vue_loader_dist_exportHelper_js__WEBPACK_IMPORTED_MODULE_2__[\"default\"])(_device_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_1__[\"default\"], [['render',_device_vue_vue_type_template_id_5f82586a__WEBPACK_IMPORTED_MODULE_0__.render],['__file',\"src/components/devices/json/device.vue\"]])\n/* hot reload */\nif (false) {}\n\n\n/* harmony default export */ __webpack_exports__[\"default\"] = (__exports__);\n\n//# sourceURL=webpack://openwb-ui-settings/./src/components/devices/json/device.vue?");

/***/ }),

/***/ "./src/components/devices/json/device.vue?vue&type=script&lang=js":
/*!************************************************************************!*\
  !*** ./src/components/devices/json/device.vue?vue&type=script&lang=js ***!
  \************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": function() { return /* reexport safe */ _node_modules_babel_loader_lib_index_js_clonedRuleSet_40_use_0_node_modules_vue_loader_dist_index_js_ruleSet_0_use_0_device_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__[\"default\"]; }\n/* harmony export */ });\n/* harmony import */ var _node_modules_babel_loader_lib_index_js_clonedRuleSet_40_use_0_node_modules_vue_loader_dist_index_js_ruleSet_0_use_0_device_vue_vue_type_script_lang_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./device.vue?vue&type=script&lang=js */ \"./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=script&lang=js\");\n \n\n//# sourceURL=webpack://openwb-ui-settings/./src/components/devices/json/device.vue?");

/***/ }),

/***/ "./src/components/devices/json/device.vue?vue&type=template&id=5f82586a":
/*!******************************************************************************!*\
  !*** ./src/components/devices/json/device.vue?vue&type=template&id=5f82586a ***!
  \******************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"render\": function() { return /* reexport safe */ _node_modules_babel_loader_lib_index_js_clonedRuleSet_40_use_0_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_3_node_modules_vue_loader_dist_index_js_ruleSet_0_use_0_device_vue_vue_type_template_id_5f82586a__WEBPACK_IMPORTED_MODULE_0__.render; }\n/* harmony export */ });\n/* harmony import */ var _node_modules_babel_loader_lib_index_js_clonedRuleSet_40_use_0_node_modules_vue_loader_dist_templateLoader_js_ruleSet_1_rules_3_node_modules_vue_loader_dist_index_js_ruleSet_0_use_0_device_vue_vue_type_template_id_5f82586a__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! -!../../../../node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!../../../../node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[3]!../../../../node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./device.vue?vue&type=template&id=5f82586a */ \"./node_modules/babel-loader/lib/index.js??clonedRuleSet-40.use[0]!./node_modules/vue-loader/dist/templateLoader.js??ruleSet[1].rules[3]!./node_modules/vue-loader/dist/index.js??ruleSet[0].use[0]!./src/components/devices/json/device.vue?vue&type=template&id=5f82586a\");\n\n\n//# sourceURL=webpack://openwb-ui-settings/./src/components/devices/json/device.vue?");

/***/ })

}]);