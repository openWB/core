import { defineStore } from "pinia";

export const useMqttStore = defineStore("mqtt", {
  state: () => ({
    settings: {
      parentChargePoint1: undefined,
      parentChargePoint2: undefined,
    },
    topics: {},
    chartData: {},
  }),
  getters: {
    /* settings getters */

    getChargePointFilter: (state) => {
      let filter = [];
      if (state.settings.parentChargePoint1 !== undefined) {
        filter.push(state.settings.parentChargePoint1);
      }
      if (state.settings.parentChargePoint2 !== undefined) {
        filter.push(state.settings.parentChargePoint2);
      }
      return filter;
    },

    /* general getters */

    getWildcardIndexList: (state) => {
      return (baseTopic, isRegex = false) => {
        let baseTopicRegex = baseTopic;
        if (!isRegex) {
          // build a valid regex based on the provided wildcard topic
          baseTopicRegex =
            "^" +
            baseTopic
              .replaceAll("/", "\\/")
              .replaceAll("+", "[^+/]+")
              .replaceAll("#", "[^#/]+") +
            "$";
        }
        // filter and return all topics matching our regex
        let myTopics = Object.keys(state.topics).filter((key) => {
          return key.match(baseTopicRegex);
        });
        myTopics.forEach((topic, index, array) => {
          array[index] = parseInt(
            topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, "")
          );
        });
        return myTopics;
      };
    },
    getWildcardTopics: (state) => {
      return (baseTopic, isRegex = false) => {
        let baseTopicRegex = baseTopic;
        if (!isRegex) {
          // build a valid regex based on the provided wildcard topic
          baseTopicRegex =
            "^" +
            baseTopic
              .replaceAll("/", "\\/")
              .replaceAll("+", "[^+/]+")
              .replaceAll("#", "[^#/]+") +
            "$";
        }
        // filter and return all topics matching our regex
        return Object.keys(state.topics)
          .filter((key) => {
            return key.match(baseTopicRegex);
          })
          .reduce((obj, key) => {
            return {
              ...obj,
              [key]: state.topics[key],
            };
          }, {});
      };
    },
    getObjectIds: (state) => {
      return (type) => {
        function getId(hierarchy) {
          let result = [];
          if (hierarchy !== undefined) {
            hierarchy.forEach((element) => {
              if (element.type == type) {
                result.push(element.id);
              }
              result = [...result, ...getId(element.children)];
            });
          }
          return result;
        }
        return getId(state.topics["openWB/counter/get/hierarchy"]);
      };
    },
    getValueBool: (state) => {
      return (topic, defaultValue = false) => {
        let value = state.topics[topic];
        if (value !== undefined) {
          return value;
        }
        return defaultValue;
      };
    },
    getValueString: (state) => {
      return (topic, unit = "W", inverted = false, defaultString = "---") => {
        var unitPrefix = "";
        var value = state.topics[topic];
        if (value === undefined) {
          return `${defaultString} ${unitPrefix}${unit}`;
        }
        if (inverted) {
          value *= -1;
        }
        var textValue = value.toLocaleString(undefined, {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        });
        if (value > 999 || value < -999) {
          textValue = (value / 1000).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          });
          unitPrefix = "k";
          if (value > 999999 || value < -999999) {
            textValue = (value / 1000000).toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });
            unitPrefix = "M";
          }
        }
        return `${textValue} ${unitPrefix}${unit}`;
      };
    },

    /* theme getters */

    getThemeConfiguration: (state) => {
      if (
        "openWB/optional/int_display/theme" in state.topics &&
        state.topics["openWB/optional/int_display/theme"] !== undefined &&
        "configuration" in state.topics["openWB/optional/int_display/theme"]
      ) {
        return state.topics["openWB/optional/int_display/theme"].configuration;
      }
      return undefined;
    },
    getDashBoardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_dashboard_view;
      }
      return true;
    },
    getChargePointsEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_charge_points_view;
      }
      return true;
    },
    getStateEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_status_view;
      }
      return true;
    },
    getGridCardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_dashboard_card_grid;
      }
      return true;
    },
    getHomeCardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration
          .enable_dashboard_card_home_consumption;
      }
      return true;
    },
    getBatteryCardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_dashboard_card_battery_sum;
      }
      return true;
    },
    getChargePointsCardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration
          .enable_dashboard_card_charge_point_sum;
      }
      return true;
    },
    getPvCardEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_dashboard_card_inverter_sum;
      }
      return true;
    },
    getLockChanges(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.lock_changes;
      }
      return true;
    },

    /* devices and components getters */

    /**
     * Parses the property "id" from the hierarchy root element.
     * @returns id of the root counter component or undefined if missing
     */
    getGridId(state) {
      let hierarchy = state.topics["openWB/counter/get/hierarchy"];
      if (hierarchy !== undefined && Object.keys(hierarchy).length > 0) {
        let index = Object.keys(
          state.topics["openWB/counter/get/hierarchy"]
        )[0];
        console.debug(
          "getGridId",
          index,
          state.topics["openWB/counter/get/hierarchy"][index]
        );
        if (
          state.topics["openWB/counter/get/hierarchy"][index].type == "counter"
        ) {
          return state.topics["openWB/counter/get/hierarchy"][index].id;
        }
      }
      return undefined;
    },
    getGridPower(state) {
      let gridId = state.getGridId;
      if (gridId === undefined) {
        return "---";
      }
      return state.getValueString(`openWB/counter/${gridId}/get/power`, "W");
    },
    getGridPowerChartData(state) {
      let gridId = state.getGridId;
      if (gridId === undefined) {
        return [];
      }
      return state.chartData[`openWB/counter/${gridId}/get/power`];
    },
    getHomePower(state) {
      return state.getValueString("openWB/counter/set/home_consumption", "W");
    },
    getHomePowerChartData(state) {
      return state.chartData["openWB/counter/set/home_consumption"];
    },
    getBatteryConfigured(state) {
      return state.getValueBool("openWB/bat/config/configured");
    },
    getBatteryPower(state) {
      return state.getValueString("openWB/bat/get/power", "W");
    },
    getBatteryPowerChartData(state) {
      return state.chartData["openWB/bat/get/power"];
    },
    getBatterySoc(state) {
      return state.getValueString("openWB/bat/get/soc", "%");
    },
    getBatterySocChartData(state) {
      return state.chartData["openWB/bat/get/soc"];
    },
    getPvConfigured(state) {
      return state.getValueBool("openWB/pv/config/configured");
    },
    getPvPower(state) {
      return state.getValueString("openWB/pv/get/power", "W", true);
    },
    getPvPowerChartData(state) {
      return state.chartData["openWB/pv/get/power"].map((point) => {
        return point * -1;
      });
    },

    /* charge point getters */

    getChargePointSumPower(state) {
      return state.getValueString("openWB/chargepoint/get/power", "W");
    },
    getChargePointSumPowerChartData(state) {
      return state.chartData["openWB/chargepoint/get/power"];
    },
    getChargePointIds(state) {
      let chargePoints = state.getObjectIds("cp");
      let filter = this.getChargePointFilter;
      if (filter.length > 0) {
        console.debug("charge points are filtered!", chargePoints, filter);
        return chargePoints.filter((chargePoint) =>
          filter.includes(chargePoint)
        );
      }
      return chargePoints;
    },
    getChargePointName(state) {
      return (chargePointId) => {
        if (
          state.topics[`openWB/chargepoint/${chargePointId}/config`] !==
          undefined
        ) {
          return state.topics[`openWB/chargepoint/${chargePointId}/config`]
            .name;
        }
        return "---";
      };
    },
    getChargePointPower(state) {
      return (chargePointId) => {
        return state.getValueString(
          `openWB/chargepoint/${chargePointId}/get/power`
        );
      };
    },
    getChargePointPowerChartData(state) {
      return (chargePointId) => {
        return state.chartData[`openWB/chargepoint/${chargePointId}/get/power`];
      };
    },
    getChargePointSetCurrent(state) {
      return (chargePointId) => {
        return state.getValueString(
          `openWB/chargepoint/${chargePointId}/set/current`,
          "A"
        );
      };
    },
    getChargePointPhasesInUse(state) {
      return (chargePointId) => {
        const phaseSymbols = ["/", "\u2460", "\u2461", "\u2462"];
        const phasesInUse =
          state.topics[`openWB/chargepoint/${chargePointId}/get/phases_in_use`];
        if (
          phasesInUse !== undefined &&
          phasesInUse >= 0 &&
          phasesInUse < phaseSymbols.length
        ) {
          return phaseSymbols[
            state.topics[
              `openWB/chargepoint/${chargePointId}/get/phases_in_use`
            ]
          ];
        }
        return "?";
      };
    },
    getChargePointPlugState(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/get/plug_state`
        );
      };
    },
    getChargePointChargeState(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/get/charge_state`
        );
      };
    },
    getChargePointManualLock(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/set/manual_lock`
        );
      };
    },
    getChargePointVehicleChangePermitted(state) {
      return (chargePointId) => {
        if (
          Array.isArray(
            state.topics[
              `openWB/chargepoint/${chargePointId}/set/change_ev_permitted`
            ]
          )
        ) {
          // topic payload is an array [bool, String]!
          return state.topics[
            `openWB/chargepoint/${chargePointId}/set/change_ev_permitted`
          ][0];
        }
        return false;
      };
    },
    getChargePointConnectedVehicleConfig(state) {
      return (chargePointId) => {
        return state.topics[
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/config`
        ];
      };
    },
    getChargePointConnectedVehicleChargeMode(state) {
      return (chargePointId) => {
        return state.translateChargeMode(
          state.getChargePointConnectedVehicleConfig(chargePointId).chargemode
        );
      };
    },
    getChargePointConnectedVehiclePriority(state) {
      return (chargePointId) => {
        return state.getChargePointConnectedVehicleConfig(chargePointId)
          .priority;
      };
    },
    getChargePointConnectedVehicleInfo(state) {
      return (chargePointId) => {
        return state.topics[
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`
        ];
      };
    },
    getChargePointConnectedVehicleId(state) {
      return (chargePointId) => {
        return state.getChargePointConnectedVehicleInfo(chargePointId).id;
      };
    },
    getChargePointConnectedVehicleChargeTemplateIndex(state) {
      return (chargePointId) => {
        return state.getChargePointConnectedVehicleConfig(chargePointId)
          .charge_template;
      };
    },
    getChargePointConnectedVehicleChargeTemplate(state) {
      return (chargePointId) => {
        let chargeTemplateId =
          state.getChargePointConnectedVehicleChargeTemplateIndex(
            chargePointId
          );
        return state.topics[
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`
        ];
      };
    },
    getChargePointConnectedVehicleEvTemplate(state) {
      return (chargePointId) => {
        return state.getChargePointConnectedVehicleConfig(chargePointId)
          .ev_template;
      };
    },
    getChargePointConnectedVehicleName(state) {
      return (chargePointId) => {
        return state.topics[
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`
        ].name;
      };
    },
    getChargePointConnectedVehicleSoc(state) {
      return (chargePointId) => {
        return state.topics[
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`
        ];
      };
    },
    getChargePointConnectedVehicleTimeChargingActive(state) {
      return (chargePointId) => {
        return state.getChargePointConnectedVehicleChargeTemplate(chargePointId)
          .time_charging.active;
      };
    },
    getChargePointConnectedVehicleTimeChargingRunning(state) {
      return (chargePointId) => {
        let running =
          state.getChargePointConnectedVehicleConfig(
            chargePointId
          ).time_charging_in_use;
        if (running !== undefined) {
          return running;
        }
        return false;
      };
    },

    /* vehicle getters */

    getVehicleList(state) {
      return state.getWildcardTopics("openWB/vehicle/+/name");
    },
    getVehicleSocConfigured(state) {
      return (vehicleId) => {
        return (
          state.topics[`openWB/vehicle/${vehicleId}/soc_module/config`].type !=
          null
        );
      };
    },
    getVehicleFaultState(state) {
      return (vehicleId) => {
        return state.topics[`openWB/vehicle/${vehicleId}/get/fault_state`];
      };
    },
  },
  actions: {
    updateSetting(setting, value) {
      if (setting in this.settings) {
        this.settings[setting] = value;
      }
    },
    initTopic(topic, defaultValue = undefined) {
      if (topic.includes("#") || topic.includes("+")) {
        console.debug("skipping init of wildcard topic:", topic);
      } else {
        this.addTopic(topic, defaultValue);
      }
    },
    /**
     * add topic with value "payload" to store
     * @param {String} topic the topic to create/update
     * @param {JSON} payload the new value as JSON object
     */
    addTopic(topic, payload) {
      console.debug("addTopic", topic, payload);
      this.topics[topic] = payload;
      // collect data for spark lines
      if (
        (topic.endsWith("home_consumption") ||
          topic.endsWith("power") ||
          topic.endsWith("soc")) &&
        payload !== undefined &&
        payload !== null
      ) {
        if (this.chartData[topic] === undefined) {
          this.chartData[topic] = [];
        }
        this.chartData[topic].push(payload);
        // limit memory usage and truncate chart data
        this.chartData[topic].slice(-128);
      }
    },
    removeTopic(topic) {
      if (topic.includes("#") || topic.includes("+")) {
        console.debug("expanding wildcard topic for removal:", topic);
        Object.keys(this.getWildcardTopics(topic)).forEach((wildcardTopic) => {
          console.debug("removing wildcardTopic:", wildcardTopic);
          delete this.topics[wildcardTopic];
        });
      } else {
        delete this.topics[topic];
      }
    },
    updateTopic(topic, payload, objectPath = undefined) {
      /**
       * helper function to update nested objects py path
       * @param {Object} object object to update
       * @param {String} path path in object
       * @param {*} value new value to set
       */
      const setPath = (object, path, value) =>
        path
          .split(".")
          .reduce(
            (o, p, i) =>
              (o[p] = path.split(".").length === ++i ? value : o[p] || {}),
            object
          );

      if (topic in this.topics) {
        if (objectPath != undefined) {
          setPath(this.topics[topic], objectPath, payload);
        } else {
          this.topics[topic] = payload;
        }
      } else {
        console.debug("topic not found: ", topic);
      }
    },
    updateState(topic, value, objectPath = undefined) {
      console.debug("updateState:", topic, value, objectPath);
      this.updateTopic(topic, value, objectPath);
    },
    translateChargeMode(mode) {
      switch (mode) {
        case "instant_charging":
          return { mode: mode, name: "Sofort", class: "danger" };
        case "pv_charging":
          return { mode: mode, name: "PV", class: "success" };
        case "scheduled_charging":
          return { mode: mode, name: "Zielladen", class: "primary" };
        case "time_charging":
          return { mode: mode, name: "Zeitladen", class: "warning" };
        case "standby":
          return { mode: mode, name: "Standby", class: "secondary" };
        case "stop":
          return { mode: mode, name: "Stop", class: "dark" };
        default:
          console.warn("unknown charge mode:", mode);
          return mode;
      }
    },
    checkChangesLockCode(code) {
      if (
        this.getThemeConfiguration &&
        this.getThemeConfiguration.lock_changes_code == code
      ) {
        return true;
      }
      return false;
    },
  },
});
