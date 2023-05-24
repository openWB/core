<script>
import { RouterView } from "vue-router";
import mqtt from "mqtt";

import DateTime from "@/components/DateTime.vue";
import NavBar from "@/components/NavBar.vue";
import LockNavItem from "@/components/LockNavItem.vue";

import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "openwbThemeStandardApp",
  components: {
    RouterView,
    DateTime,
    NavBar,
    LockNavItem,
  },
  data() {
    return {
      client: {
        connected: false,
      },
      connection: {
        protocol: location.protocol == "https:" ? "wss" : "ws",
        host: location.hostname,
        port:
          parseInt(location.port) || (location.protocol == "https:" ? 443 : 80),
        endpoint: "/ws",
        connectTimeout: 4000,
        reconnectPeriod: 4000,
      },
      mqttTopicsToSubscribe: [
        "openWB/optional/int_display/theme",
        "openWB/counter/get/hierarchy",
        "openWB/counter/set/home_consumption",
        "openWB/counter/+/get/power",
        "openWB/bat/config/configured",
        "openWB/bat/get/power",
        "openWB/bat/get/soc",
        "openWB/chargepoint/get/power",
        "openWB/pv/config/configured",
        "openWB/pv/get/power",
        "openWB/chargepoint/+/get/power",
        "openWB/chargepoint/+/get/plug_state",
        "openWB/chargepoint/+/get/charge_state",
        "openWB/chargepoint/+/get/phases_in_use",
        "openWB/chargepoint/+/set/current",
        "openWB/chargepoint/+/set/manual_lock",
        "openWB/chargepoint/+/set/change_ev_permitted",
        "openWB/chargepoint/+/config",
        "openWB/chargepoint/+/get/connected_vehicle/+",
        "openWB/vehicle/+/name",
        "openWB/vehicle/+/soc_module/config",
        "openWB/vehicle/+/get/fault_state",
        "openWB/vehicle/template/charge_template/#",
      ],
      mqttStore: useMqttStore(),
      chartInterval: "",
    };
  },
  computed: {
    changesLocked() {
      return (
        this.mqttStore.getLockChanges && this.mqttStore.settings.changesLocked
      );
    },
  },
  methods: {
    /**
     * Establishes a connection to the configured broker
     */
    createConnection() {
      const { protocol, host, port, endpoint, ...options } = this.connection;
      const connectUrl = `${protocol}://${host}:${port}${endpoint}`;
      console.debug("connecting to broker:", connectUrl);
      try {
        this.client = mqtt.connect(connectUrl, options);
      } catch (error) {
        console.error("mqtt.connect error", error);
      }
      this.client.on("connect", () => {
        console.debug(
          "Connection succeeded! ClientId: ",
          this.client.options.clientId
        );
      });
      this.client.on("error", (error) => {
        console.error("Connection failed", error);
      });
      this.client.on("message", (topic, message) => {
        console.debug(`Received message "${message}" from topic "${topic}"`);
        if (message.toString().length > 0) {
          let myPayload = undefined;
          try {
            myPayload = JSON.parse(message.toString());
          } catch (error) {
            console.debug("Json parsing failed, fallback to string: ", topic);
            myPayload = message.toString();
          }
          this.mqttStore.addTopic(topic, myPayload);
        } else {
          this.mqttStore.removeTopic(topic);
        }
      });
    },
    doSubscribe(topics) {
      topics.forEach((topic) => {
        this.mqttStore.initTopic(topic);
      });
      this.client.subscribe(topics, {}, (error) => {
        if (error) {
          console.error("Subscribe to topics error", error);
          return;
        }
      });
    },
    doUnsubscribe(topics) {
      topics.forEach((topic) => {
        this.mqttStore.removeTopic(topic);
      });
      this.client.unsubscribe(topics, (error) => {
        if (error) {
          console.error("Unsubscribe error", error);
        }
      });
    },
    doPublish(topic, payload, retain = true, qos = 2) {
      console.debug("doPublish", topic, payload);
      let options = {
        qos: qos,
        retain: retain,
      };
      this.client.publish(topic, JSON.stringify(payload), options, (error) => {
        if (error) {
          console.error("Publish error", error);
        }
      });
    },
    sendTopicToBroker(topic, payload = undefined) {
      let setTopic = topic.replace("openWB/", "openWB/set/");
      if (payload === undefined) {
        payload = this.mqttStore.topics[topic];
      }
      this.doPublish(setTopic, payload);
    },
  },
  created() {
    this.createConnection();
  },
  mounted() {
    // add url parameters to store
    let uri = window.location.search;
    if (uri != "") {
      console.debug("search", uri);
      let params = new URLSearchParams(uri);
      params.forEach((value, key) => {
        this.mqttStore.updateSetting(key, parseInt(value));
      });
    }
    // subscribe our topics
    this.doSubscribe(this.mqttTopicsToSubscribe);
    // timer for chart data
    this.chartInterval = setInterval(this.mqttStore.updateChartData, 5000);
  },
  beforeUnmount() {
    // unsubscribe our topics
    this.doUnsubscribe(this.mqttTopicsToSubscribe);
    // clear timer for chart data
    clearInterval(this.chartInterval);
  },
};
</script>

<template>
  <i-layout vertical>
    <i-layout-aside class="_position:fixed">
      <i-container fluid class="_margin-bottom:1">
        <i-row center>
          <i-column>
            <DateTime />
          </i-column>
        </i-row>
      </i-container>
      <LockNavItem />
      <NavBar :changesLocked="changesLocked" />
    </i-layout-aside>

    <i-layout-content>
      <RouterView :changesLocked="changesLocked" />
    </i-layout-content>
  </i-layout>
</template>

<style scoped>
.layout-aside {
  ----width: 10rem !important;
}

.layout-content {
  margin-left: calc(10rem + var(--spacing));
  margin-right: var(--spacing);
}

hr {
  border-color: var(--color--primary);
  margin: var(--spacing) 0;
}
</style>
