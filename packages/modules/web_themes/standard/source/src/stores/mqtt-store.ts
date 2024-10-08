import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import mqtt from 'mqtt';

import {
  ConnectionOptions,
  TopicObject,
  TopicList,
  TopicCount,
} from './mqtt-store-model';

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

  // General functions and methods for the store - BEGIN
  /**
   * Initialize the MQTT client
   * @returns void
   * @throws Error
   * @example
   * initialize();
   */
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

  /**
   * Initialize a topic with a default value
   * Wildcard topics are skipped
   * @param topic mqtt topic to initialize
   * @param defaultValue value to initialize the topic with
   * @returns void
   * @example
   * initTopic('openWB/general/web_theme', undefined);
   */
  function initTopic(topic: string, defaultValue: unknown = undefined): void {
    if (topic.includes('#') || topic.includes('+')) {
      console.debug('skipping init of wildcard topic:', topic);
    } else {
      addTopic(topic, defaultValue);
    }
  }

  /**
   * Add a topic to the store
   * @param topic mqtt topic to add
   * @param payload value to use for the topic
   * @returns void
   * @example
   * addTopic('openWB/general/web_theme', 'standard');
   */
  function addTopic(topic: string, payload: unknown): void {
    console.debug('addTopic', topic, payload);
    topics.value[topic] = payload;
  }

  /**
   * Update a topic in the store
   * optionally update only part of a nested object in the topic referenced by objectPath
   * @param topic the mqtt topic to update
   * @param payload the new value to set
   * @param objectPath the path in the object to update (optional)
   * @returns void
   * @example
   * updateTopic('openWB/system/version', '1.2.3');
   * updateTopic('openWB/general/web_theme', false, 'official');
   */
  function updateTopic(
    topic: string,
    payload: unknown,
    objectPath: string | undefined = undefined,
  ) {
    /**
     * helper function to update nested objects py path
     * @param object object to update
     * @param path path in object
     * @param value new value to set
     * @returns void
     */
    const setPath = (
      object: TopicObject,
      path: string,
      value: unknown,
    ): void => {
      const keys = path.split('.');
      keys.reduce((acc: unknown, key: string, index: number) => {
        if (index === keys.length - 1) {
          (acc as TopicObject)[key] = value;
          return value;
        }
        return (acc as TopicObject)[key];
      }, object);
    };

    if (topic in topics.value) {
      if (objectPath != undefined) {
        setPath(topics.value[topic], objectPath, payload);
      } else {
        topics.value[topic] = payload;
      }
    } else {
      console.debug('topic not found', topic);
    }
  }

  /**
   * Remove a topic from the store
   * Wildcard topics are expanded and removed
   * @param topic mqtt topic to remove
   * @returns void
   * @example
   * removeTopic('openWB/general/web_theme');
   */
  function removeTopic(topic: string): void {
    if (topic.includes('#') || topic.includes('+')) {
      console.debug('expanding wildcard topic for removal:', topic);
      Object.keys(getWildcardValues.value(topic)).forEach((wildcardTopic) => {
        console.debug('removing wildcardTopic:', wildcardTopic);
        delete topics.value[wildcardTopic];
      });
    } else {
      delete topics.value[topic];
    }
  }

  /**
   * Subscribe to a single or list of mqtt topics
   * @param topics mqtt topics to subscribe to
   * @returns void
   * @example
   * subscribe('openWB/general/web_theme');
   * subscribe(['openWB/general/web_theme', 'openWB/system/time']);
   * subscribe('openWB/general/#');
   * subscribe('openWB/general/+');
   */
  function subscribe(topics: string[] | string): void {
    if (!Array.isArray(topics)) {
      topics = [topics];
    }
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

  /**
   * Unsubscribe from a single or list of mqtt topics
   * @param topics mqtt topics to unsubscribe from
   * @returns void
   * @example
   * unsubscribe('openWB/general/web_theme');
   * unsubscribe(['openWB/general/web_theme', 'openWB/system/time']);
   * unsubscribe('openWB/general/#');
   * unsubscribe('openWB/general/+');
   */
  function unsubscribe(topics: string[] | string): void {
    if (!Array.isArray(topics)) {
      topics = [topics];
    }
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

  /**
   * Add a subscription to the internal list of subscriptions
   * @param topic mqtt topic to add to the list
   * @returns void
   * @example
   * addSubscription('openWB/general/web_theme');
   * addSubscription('openWB/general/#');
   */
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

  /**
   * Remove a subscription from the internal list of subscriptions
   * @param topic mqtt topic to remove from the list
   * @returns void
   * @example
   * removeSubscription('openWB/general/web_theme');
   * removeSubscription('openWB/general/#');
   */
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
  // General functions and methods for the store - END

  // Computed
  /**
   * Get all topics matching a wildcard topic
   * @param baseTopic mqtt topic to match against
   * @param isRegex flag to indicate if the baseTopic is a regex
   * @returns TopicList
   * @example
   * getWildcardValues('openWB/general/#');
   * getWildcardValues('openWB/pv/[0-9]+/config/m,ax_ac_out', true);
   */
  const getWildcardValues = computed(() => {
    return (baseTopic: string, isRegex: boolean = false): TopicList => {
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

  /**
   * Get the value of a topic or a nested object in the topic
   * @param topic mqtt topic to get the value from
   * @param objectPath path in the object to get the value from
   * @returns unknown
   * @example
   * getTopic('openWB/system/version');
   * getTopic('openWB/general/web_theme', 'official');
   */
  const getValue = computed(() => {
    return (
      topic: string,
      objectPath: string | undefined = undefined,
    ): unknown => {
      if (!(topic in topics.value)) {
        console.warn('topic not found', topic);
        console.warn('auto subscription of topic', topic);
        subscribe(topic);
        return undefined;
      }
      let topicObject = topics.value[topic];
      if (objectPath == undefined || topicObject == undefined) {
        return topicObject;
      }
      const path = objectPath.split('.');
      for (let i = 0; i < path.length; i++) {
        if (topicObject[path[i]] == undefined) {
          console.warn('path not found', topicObject, path[i]);
          return undefined;
        }
        topicObject = topicObject[path[i]];
      }
      return topicObject;
    };
  });

  /**
   * Get the theme configuration
   * @returns object | undefined
   */
  const themeConfiguration = computed(() => {
    return getValue.value('openWB/general/web_theme', 'configuration') as
      | object
      | undefined;
  });

  /**
   * Get the system version
   * @returns string | undefined
   */
  const systemVersion = computed(() => {
    return getValue.value('openWB/system/version') as string | undefined;
  });

  /**
   * Get the system IP address
   * @returns string | undefined
   */
  const systemIp = computed(() => {
    return getValue.value('openWB/system/ip_address') as string | undefined;
  });

  /**
   * Get the system branch
   * @returns string | undefined
   */
  const systemBranch = computed(() => {
    return getValue.value('openWB/system/current_branch') as string | undefined;
  });

  /**
   * Get the system commit
   * @returns string | undefined
   */
  const systemCommit = computed(() => {
    const myTopic = 'openWB/system/current_commit';
    return getValue.value(myTopic) as string | undefined;
  });

  /**
   * Get the system time from the mqtt topics
   * @param returnType type of return value, 'locale-string', 'number' or 'date'
   * @returns string | number | Date | undefined
   */
  const systemDateTime = computed(() => {
    return (
      returnType: string = 'Date',
    ): string | number | Date | undefined => {
      const timestamp = getValue.value('openWB/system/time') as
        | number
        | undefined;
      if (timestamp == undefined) {
        return undefined;
      }
      const systemDateTime = new Date(timestamp * 1000);
      switch (returnType) {
        case 'locale-string':
          return systemDateTime.toLocaleString();
        case 'number':
          return systemDateTime.getTime();
        case 'date':
        default:
          return systemDateTime;
      }
    };
  });

  const getChargePoints = computed(()=>{
    return getWildcardValues.value('openWB/chargepoint/+/config');
  });

  const getChargePointNames = computed(() => {
    const chargePoints = getWildcardValues.value('openWB/chargepoint/+/config');
    // Extract the name from each charge point's config
    return Object.values(chargePoints).map((config) => config?.name);
  });

  // exports
  return {
    topics,
    // subscriptions, // do not expose internal data
    initialize,
    updateTopic,
    updateState: updateTopic, // alias for compatibility with older code
    subscribe,
    unsubscribe,
    getValue,
    systemVersion,
    systemIp,
    systemBranch,
    systemCommit,
    themeConfiguration,
    systemDateTime,
    getChargePoints,
    getChargePointNames,
  };
});
