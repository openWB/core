import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import mqtt from 'mqtt';

import { ConnectionOptions, TopicList, TopicCount } from './mqtt-store-model';

export const useMqttStore = defineStore('mqtt', () => {
  // local variables
  let mqttClient: mqtt.MqttClient | undefined = undefined;
  const mqttConnectionOptions: ConnectionOptions = {
    protocol: location.protocol == 'https:' ? 'wss' : 'ws',
    host: location.hostname,
    port: parseInt(location.port) || (location.protocol == 'https:' ? 443 : 80),
    endpoint: '/ws',
    connectTimeout: 4000,
    reconnectPeriod: 4000,
  };

  // State
  const subscriptions = ref<TopicCount>({});
  const topics = ref<TopicList>({});
  // const chartData = ref<ChartData>({});

  // Methods
  function initialize() {
    const { protocol, host, port, endpoint, ...options } =
      mqttConnectionOptions;
    const connectUrl = `${protocol}://${host}:${port}${endpoint}`;
    console.debug('connecting to broker:', connectUrl);
    try {
      mqttClient = mqtt.connect(connectUrl, options);
      mqttClient.on('connect', () => {
        console.debug('connected to broker');
      });
      mqttClient.on('error', (error) => {
        console.error('Client error', error);
      });
      mqttClient.on('message', (topic: string, message) => {
        console.debug(`Received message "${message}" from topic "${topic}"`);
        if (message.toString().length > 0) {
          let myPayload = undefined;
          try {
            myPayload = JSON.parse(message.toString());
          } catch (error) {
            console.debug(
              'Json parsing failed, fallback to string',
              topic,
              error,
            );
            myPayload = message.toString();
          }
          addTopic(topic, myPayload);
        } else {
          removeTopic(topic);
        }
      });
    } catch (error) {
      console.error('error connecting to broker:', error);
    }
  }

  function initTopic(topic: string, defaultValue: unknown = undefined): void {
    if (topic.includes('#') || topic.includes('+')) {
      console.debug('skipping init of wildcard topic:', topic);
    } else {
      addTopic(topic, defaultValue);
    }
  }

  function addTopic(topic: string, payload: unknown): void {
    console.debug('addTopic', topic, payload);
    topics.value[topic] = payload;
  }

  function removeTopic(topic: string): void {
    if (topic.includes('#') || topic.includes('+')) {
      console.debug('expanding wildcard topic for removal:', topic);
      Object.keys(getWildcardTopics.value(topic)).forEach((wildcardTopic) => {
        console.debug('removing wildcardTopic:', wildcardTopic);
        delete topics.value[wildcardTopic];
      });
    } else {
      delete topics.value[topic];
    }
  }

  function subscribe(topics: string[]): void {
    topics.forEach((topic) => {
      addSubscription(topic);
      initTopic(topic);
    });
    if (!mqttClient) {
      console.error('mqttClient is not initialized');
      return;
    }
    mqttClient.subscribe(topics, {}, (error) => {
      if (error) {
        console.error('Subscribe to topics error', error);
        return;
      }
    });
  }

  function unsubscribe(topics: string[]): void {
    topics.forEach((topic) => {
      removeSubscription(topic);
      removeTopic(topic);
    });
    if (!mqttClient) {
      console.error('mqttClient is not initialized');
      return;
    }
    mqttClient.unsubscribe(topics, (error) => {
      if (error) {
        console.error('Unsubscribe error', error);
      }
    });
  }

  function addSubscription(topic: string): void {
    // add subscription to list or increment count
    if (topic in subscriptions.value) {
      subscriptions.value[topic] += 1;
    } else {
      subscriptions.value[topic] = 1;
    }
    console.debug(
      'subscription count for topic',
      topic,
      subscriptions.value[topic],
    );
  }

  function removeSubscription(topic: string): void {
    // remove subscription from list or decrement count
    if (topic in subscriptions.value) {
      subscriptions.value[topic] -= 1;
      if (subscriptions.value[topic] <= 0) {
        delete subscriptions.value[topic];
      }
    }
    console.debug(
      'subscription count for topic',
      topic,
      subscriptions.value[topic],
    );
  }

  // Computed
  const getWildcardTopics = computed(() => {
    return (baseTopic: string, isRegex: boolean = false) => {
      let baseTopicRegex = baseTopic;
      if (!isRegex) {
        // build a valid regex based on the provided wildcard topic
        baseTopicRegex =
          '^' +
          baseTopic
            .replaceAll('/', '\\/')
            .replaceAll('+', '[^+/]+')
            .replaceAll('#', '[^#/]+') +
          '$';
      }
      // filter and return all topics matching our regex
      return Object.keys(topics.value)
        .filter((key) => {
          return key.match(baseTopicRegex);
        })
        .reduce((obj, key) => {
          return {
            ...obj,
            [key]: topics.value[key],
          };
        }, {});
    };
  });

  const getSystemTime = computed((): string | undefined => {
    console.log('openWB/system/time', topics.value['openWB/system/time']);
    if (topics.value['openWB/system/time']) {
      return new Date(
        topics.value['openWB/system/time'] * 1000,
      ).toLocaleString();
    }
    return undefined;
  });

  // exports
  return {
    topics,
    subscriptions,
    initialize,
    subscribe,
    unsubscribe,
    getSystemTime,
  };
});
