import { defineStore } from "pinia";

export const useMqttStore = defineStore("mqtt", {
  state: () => ({
    settings: {
      localIp: undefined,
      localBranch: undefined,
      localCommit: undefined,
      localVersion: undefined,
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
            topic.match(/(?:\/)([0-9]+)(?=\/)*/g)[0].replace(/[^0-9]+/g, ""),
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
        console.warn("topic not found! using default", topic, defaultValue);
        return defaultValue;
      };
    },
    getValueString: (state) => {
      return (
        topic,
        unit = "W",
        unitPrefix = "",
        scale = true,
        inverted = false,
        defaultString = "---",
        topicElement = undefined,
      ) => {
        var scaled = false;
        var value = state.topics[topic];
        if (
          value === undefined ||
          (topicElement !== undefined && value[topicElement] === undefined)
        ) {
          console.warn("topic not found! using default", topic, defaultString);
          textValue = defaultString;
        } else {
          if (topicElement !== undefined) {
            value = value[topicElement];
          }
          if (inverted) {
            value *= -1;
          }
          var textValue = value.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          });
          var scaledValue = value;
          while (scale && (scaledValue > 999 || scaledValue < -999)) {
            scaledValue = scaledValue / 1000;
            scaled = true;
            switch (unitPrefix) {
              case "":
                unitPrefix = "k";
                break;
              case "k":
                unitPrefix = "M";
                break;
              case "M":
                unitPrefix = "G";
                break;
            }
          }
          textValue = scaledValue.toLocaleString(undefined, {
            minimumFractionDigits: scaled ? 2 : 0,
            maximumFractionDigits: scaled ? 2 : 0,
          });
        }
        return {
          textValue: `${textValue} ${unitPrefix}${unit}`,
          value: value,
          unit: unit,
          scaledValue: scaledValue,
          scaledUnit: `${unitPrefix}${unit}`,
        };
      };
    },
    getChartData: (state) => {
      return (topic) => {
        if (state.chartData[topic] === undefined) {
          return [];
        }
        return state.chartData[topic];
      };
    },
    getDisplayStandby: (state) => {
      return state.topics["openWB/optional/int_display/standby"];
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
    getEnergyFlowEnabled(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.enable_energy_flow_view;
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
    getSimpleChargePointView(state) {
      if (state.getThemeConfiguration) {
        return state.getThemeConfiguration.simple_charge_point_view;
      }
      return false;
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
          state.topics["openWB/counter/get/hierarchy"],
        )[0];
        console.debug(
          "getGridId",
          index,
          state.topics["openWB/counter/get/hierarchy"][index],
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
      return (returnType = "textValue") => {
        let gridId = state.getGridId;
        if (gridId === undefined) {
          return "---";
        }
        let power = state.getValueString(
          `openWB/counter/${gridId}/get/power`,
          "W",
        );
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getGridPowerChartData(state) {
      let gridId = state.getGridId;
      if (gridId === undefined) {
        return [];
      }
      return state.getChartData(`openWB/counter/${gridId}/get/power`);
    },
    getHomePower(state) {
      return (returnType = "textValue") => {
        let power = state.getValueString(
          "openWB/counter/set/home_consumption",
          "W",
        );
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getHomePowerChartData(state) {
      return state.getChartData("openWB/counter/set/home_consumption");
    },
    getBatteryConfigured(state) {
      return state.getValueBool("openWB/bat/config/configured");
    },
    getBatteryPower(state) {
      return (returnType = "textValue") => {
        let power = state.getValueString("openWB/bat/get/power", "W");
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getBatteryPowerChartData(state) {
      return state.getChartData("openWB/bat/get/power");
    },
    getBatterySoc(state) {
      return (returnType = "textValue") => {
        let soc = state.getValueString("openWB/bat/get/soc", "%", "", false);
        if (Object.hasOwnProperty.call(soc, returnType)) {
          return soc[returnType];
        }
        if (returnType == "object") {
          return soc;
        }
        console.error("returnType not found!", returnType, soc);
      };
    },
    getBatterySocChartData(state) {
      return state.getChartData("openWB/bat/get/soc");
    },
    getPvConfigured(state) {
      return state.getValueBool("openWB/pv/config/configured");
    },
    getPvPower(state) {
      return (returnType = "textValue") => {
        var power = state.getValueString(
          "openWB/pv/get/power",
          "W",
          "",
          true,
          true,
        );
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getPvPowerChartData(state) {
      return state.getChartData("openWB/pv/get/power").map((point) => {
        return point * -1;
      });
    },

    /* charge point getters */

    getChargePointSumPower(state) {
      return (returnType = "textValue") => {
        var power = state.getValueString("openWB/chargepoint/get/power", "W");
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getChargePointSumPowerChartData(state) {
      return state.getChartData("openWB/chargepoint/get/power");
    },
    getChargePointIds(state) {
      let chargePoints = state.getObjectIds("cp");
      let filter = this.getChargePointFilter;
      if (filter.length > 0) {
        console.debug("charge points are filtered!", chargePoints, filter);
        return chargePoints.filter((chargePoint) =>
          filter.includes(chargePoint),
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
      return (chargePointId, returnType = "textValue") => {
        var power = state.getValueString(
          `openWB/chargepoint/${chargePointId}/get/power`,
          "W",
        );
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
      };
    },
    getChargePointImportedSincePlugged(state) {
      return (chargePointId) => {
        return {
          energy: state.getValueString(
            `openWB/chargepoint/${chargePointId}/set/log`,
            "Wh",
            "",
            true,
            false,
            "---",
            "imported_since_plugged",
          ).textValue,
          range: state.getValueString(
            `openWB/chargepoint/${chargePointId}/set/log`,
            "m",
            "k",
            false,
            false,
            "---",
            "range_charged",
          ).textValue,
        };
      };
    },
    getChargePointPowerChartData(state) {
      return (chargePointId) => {
        return state.getChartData(
          `openWB/chargepoint/${chargePointId}/get/power`,
        );
      };
    },
    getChargePointSetCurrent(state) {
      return (chargePointId, returnType = "textValue") => {
        let power = state.getValueString(
          `openWB/chargepoint/${chargePointId}/set/current`,
          "A",
        );
        if (Object.hasOwnProperty.call(power, returnType)) {
          return power[returnType];
        }
        if (returnType == "object") {
          return power;
        }
        console.error("returnType not found!", returnType, power);
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
        console.warn(
          "topic not found!",
          `openWB/chargepoint/${chargePointId}/get/phases_in_use`,
        );
        return "?";
      };
    },
    getChargePointPlugState(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/get/plug_state`,
        );
      };
    },
    getChargePointChargeState(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/get/charge_state`,
        );
      };
    },
    getChargePointManualLock(state) {
      return (chargePointId) => {
        return state.getValueBool(
          `openWB/chargepoint/${chargePointId}/set/manual_lock`,
        );
      };
    },
    getChargepointTagState(state) {
      return (chargePointId) => {
        if (
          ![undefined, null, ""].includes(
            state.topics[`openWB/chargepoint/${chargePointId}/set/rfid`],
          )
        ) {
          return 2;
        } else {
          if (
            ![undefined, null, ""].includes(
              state.topics[`openWB/chargepoint/${chargePointId}/get/rfid`],
            )
          ) {
            return 1;
          }
        }
        return 0;
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
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.translateChargeMode(
            state.getChargePointConnectedVehicleChargeTemplate(chargePointId)
              .chargemode.selected,
          );
        }
        return undefined;
      };
    },
    getChargePointConnectedVehiclePriority(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).prio;
        }
        return undefined;
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
        if (state.getChargePointConnectedVehicleInfo(chargePointId)) {
          return state.getChargePointConnectedVehicleInfo(chargePointId).id;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleChargeTemplateIndex(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleConfig(chargePointId)) {
          return state.getChargePointConnectedVehicleConfig(chargePointId)
            .charge_template;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleChargeTemplate(state) {
      return (chargePointId) => {
        let chargeTemplateId =
          state.getChargePointConnectedVehicleChargeTemplateIndex(
            chargePointId,
          );
        return state.topics[
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`
        ];
      };
    },
    getChargePointConnectedVehicleEvTemplate(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleConfig(chargePointId)) {
          return state.getChargePointConnectedVehicleConfig(chargePointId)
            .ev_template;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleName(state) {
      return (chargePointId) => {
        if (
          state.topics[
            `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`
          ]
        ) {
          return state.topics[
            `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`
          ].name;
        }
        return undefined;
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
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).time_charging.active;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleTimeChargingRunning(state) {
      return (chargePointId) => {
        let running =
          state.getChargePointConnectedVehicleConfig(
            chargePointId,
          ).time_charging_in_use;
        if (running !== undefined) {
          return running;
        }
        return false;
      };
    },
    getChargePointConnectedVehicleInstantChargingCurrent(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.instant_charging.current;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleInstantChargingLimit(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.instant_charging.limit;
        }
        return { selected: undefined };
      };
    },
    getChargePointConnectedVehiclePvChargingFeedInLimit(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.pv_charging.feed_in_limit;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehiclePvChargingMinCurrent(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.pv_charging.min_current;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehiclePvChargingMinSoc(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.pv_charging.min_soc;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehiclePvChargingMinSocCurrent(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.pv_charging.min_soc_current;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehiclePvChargingMaxSoc(state) {
      return (chargePointId) => {
        if (state.getChargePointConnectedVehicleChargeTemplate(chargePointId)) {
          return state.getChargePointConnectedVehicleChargeTemplate(
            chargePointId,
          ).chargemode.pv_charging.max_soc;
        }
        return undefined;
      };
    },
    getChargePointConnectedVehicleScheduledChargingPlans(state) {
      return (chargePointId) => {
        let chargeTemplateId =
          state.getChargePointConnectedVehicleChargeTemplateIndex(
            chargePointId,
          );
        return state.getWildcardTopics(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/+`,
        );
      };
    },
    getChargePointConnectedVehicleTimeChargingPlans(state) {
      return (chargePointId) => {
        let chargeTemplateId =
          state.getChargePointConnectedVehicleChargeTemplateIndex(
            chargePointId,
          );
        return state.getWildcardTopics(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}/time_charging/plans/+`,
        );
      };
    },

    /* vehicle getters */

    getVehicleList(state) {
      return state.getWildcardTopics("openWB/vehicle/+/name");
    },
    getVehicleName(state) {
      return (vehicleId) => {
        return state.topics[`openWB/vehicle/${vehicleId}/name`];
      };
    },
    getVehicleSocConfigured(state) {
      return (vehicleId) => {
        return (
          state.topics[`openWB/vehicle/${vehicleId}/soc_module/config`].type !=
          null
        );
      };
    },
    getVehicleSocIsManual(state) {
      return (vehicleId) => {
        return (
          state.topics[`openWB/vehicle/${vehicleId}/soc_module/config`].type ==
          "manual"
        );
      };
    },
    getVehicleFaultState(state) {
      return (vehicleId) => {
        if (state.topics[`openWB/vehicle/${vehicleId}/get/fault_state`]) {
          return state.topics[`openWB/vehicle/${vehicleId}/get/fault_state`];
        }
        return 0;
      };
    },

    /* system getters */

    getSystemTime(state) {
      if (state.topics["openWB/system/time"]) {
        return new Date(
          state.topics["openWB/system/time"] * 1000,
        ).toLocaleString();
      }
      return undefined;
    },
    getSystemIp(state) {
      if (state.settings.localIp !== undefined) {
        return state.settings.localIp;
      }
      if (state.topics["openWB/system/ip_address"]) {
        return state.topics["openWB/system/ip_address"];
      }
      return undefined;
    },
    getSystemVersion(state) {
      if (state.settings.localVersion !== undefined) {
        return state.settings.localVersion;
      }
      if (state.topics["openWB/system/version"]) {
        return state.topics["openWB/system/version"];
      }
      return undefined;
    },
    getSystemBranch(state) {
      if (state.settings.localBranch !== undefined) {
        return state.settings.localBranch;
      }
      if (state.topics["openWB/system/current_branch"]) {
        return state.topics["openWB/system/current_branch"];
      }
      return undefined;
    },
    getSystemCurrentCommit(state) {
      if (state.settings.localCommit !== undefined) {
        return state.settings.localCommit;
      }
      if (state.topics["openWB/system/current_commit"]) {
        return state.topics["openWB/system/current_commit"];
      }
      return undefined;
    },

    /* rfid */
    getRfidEnabled() {
      return this.getValueBool("openWB/optional/rfid/active");
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
            object,
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
    updateChartData() {
      // collect data for spark lines
      for (const [topic, payload] of Object.entries(this.topics)) {
        if (
          topic.endsWith("home_consumption") ||
          topic.endsWith("power") ||
          topic.endsWith("soc")
        ) {
          if (this.chartData[topic] === undefined) {
            this.chartData[topic] = [];
          }
          if (payload !== undefined && payload !== null) {
            this.chartData[topic].push(payload);
            // limit memory usage and truncate chart data
            this.chartData[topic].slice(-128);
          }
        }
      }
    },
    updateState(topic, value, objectPath = undefined) {
      console.debug("updateState:", topic, value, objectPath);
      this.updateTopic(topic, value, objectPath);
    },
    chargeModeList() {
      var chargeModes = [
        { id: "instant_charging" },
        { id: "pv_charging" },
        { id: "scheduled_charging" },
        { id: "standby" },
        { id: "stop" },
      ];
      chargeModes.forEach((mode) => {
        mode.label = this.translateChargeMode(mode.id).label;
        mode.class = this.translateChargeMode(mode.id).class;
      });
      return chargeModes;
    },
    translateChargeMode(mode) {
      switch (mode) {
        case "instant_charging":
          return { mode: mode, label: "Sofort", class: "danger" };
        case "pv_charging":
          return { mode: mode, label: "PV", class: "success" };
        case "scheduled_charging":
          return { mode: mode, label: "Zielladen", class: "primary" };
        case "time_charging":
          return { mode: mode, label: "Zeitladen", class: "warning" };
        case "standby":
          return { mode: mode, label: "Standby", class: "secondary" };
        case "stop":
          return { mode: mode, label: "Stop", class: "dark" };
        default:
          console.warn("unknown charge mode:", mode);
          return { mode: mode, label: mode, class: mode };
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
    formatDate(
      dateString,
      format = { year: "numeric", month: "2-digit", day: "2-digit" },
    ) {
      let date = new Date(dateString);
      return date.toLocaleDateString(undefined, format);
    },
    formatDateRange(dateArray, separator = "-") {
      const endFormat = { year: "numeric", month: "2-digit", day: "2-digit" };
      let beginFormat = { day: "2-digit" }; // always display day
      const beginDate = new Date(dateArray[0]);
      const endDate = new Date(dateArray[1]);
      if (beginDate.getFullYear() == endDate.getFullYear()) {
        if (beginDate.getMonth() != endDate.getMonth()) {
          // add display of month if different and year is identical
          beginFormat.month = endFormat.month;
        }
      } else {
        // display full date if year is different
        beginFormat = endFormat;
      }
      return `${this.formatDate(
        dateArray[0],
        beginFormat,
      )}${separator}${this.formatDate(dateArray[1], endFormat)}`;
    },
    formatWeeklyScheduleDays(weekDays) {
      const days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
      let planDays = [];
      weekDays.forEach(function (dayValue, index) {
        if (dayValue == true) {
          planDays.push(days[index]);
        }
      });
      return planDays.join(",");
    },
  },
});
