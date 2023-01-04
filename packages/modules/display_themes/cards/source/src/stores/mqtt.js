import { defineStore } from "pinia";

export const useMqttStore = defineStore("mqtt", {
  state: () => ({
    topics: {},
    chartData: {},
  }),
  getters: {
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
    getValueBool: (state) => {
      return (topic) => {
        let value = state.topics[topic];
        if (value !== undefined) {
          return value;
        }
        return false;
      };
    },
    getValueString: (state) => {
      return (topic, unit = "W", inverted = false) => {
        var unitPrefix = "";
        var value = state.topics[topic];
        if (value === undefined) {
          return `--- ${unitPrefix}${unit}`;
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
  },
  actions: {
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
        payload !== undefined
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
  },
});
