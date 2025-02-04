import { defineStore } from 'pinia';
import { ref, computed, ComputedRef } from 'vue';
import mqtt, { IClientPublishOptions } from 'mqtt';
import { QoS } from 'mqtt-packet';

// import all type definitions from the mqtt-store-model
import type {
  ConnectionOptions,
  TopicObject,
  TopicList,
  TopicCount,
  Hierarchy,
  ChargePointConnectedVehicleConfig,
  ChargeTemplateConfiguration,
  ValueObject,
  ChargePointConnectedVehicleInfo,
  Vehicle,
  ScheduledChargingPlan,
  ChargePointConnectedVehicleSoc,
  GraphDataPoint,
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
   * @param publish flag to indicate if the topic should be published to the broker
   * @returns void
   * @example
   * updateTopic('openWB/system/version', '1.2.3');
   * updateTopic('openWB/general/web_theme', 'standard', 'official');
   * updateTopic('openWB/general/web_theme', 'standard', undefined, true);
   */
  function updateTopic(
    topic: string,
    payload: unknown,
    objectPath: string | undefined = undefined,
    publish: boolean = false,
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
      if (publish) {
        sendTopicToBroker(topic, topics.value[topic]);
      }
    } else {
      console.warn('topic not found', topic);
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
  function subscribe(
    topics: string[] | string,
    defaultValue: unknown = undefined,
  ): void {
    if (!Array.isArray(topics)) {
      topics = [topics];
    }
    topics.forEach((topic) => {
      if (addSubscription(topic) == 1) {
        initTopic(topic, defaultValue);
        if (!mqttClient) {
          console.error('mqttClient is not initialized');
        } else {
          mqttClient.subscribe(topics, {}, (error) => {
            if (error) {
              console.error('Subscribe to topics error', error);
            }
          });
        }
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
      if (removeSubscription(topic) <= 0) {
        removeTopic(topic);
        if (!mqttClient) {
          console.error('mqttClient is not initialized');
        } else {
          mqttClient.unsubscribe(topic, (error) => {
            if (error) {
              console.error('Unsubscribe error', error);
            }
          });
        }
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
  function addSubscription(topic: string): number {
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
    return subscriptions.value[topic];
  }

  /**
   * Remove a subscription from the internal list of subscriptions
   * @param topic mqtt topic to remove from the list
   * @returns void
   * @example
   * removeSubscription('openWB/general/web_theme');
   * removeSubscription('openWB/general/#');
   */
  function removeSubscription(topic: string): number {
    let count = 0;
    // remove subscription from list or decrement count
    if (topic in subscriptions.value) {
      count = subscriptions.value[topic] -= 1;
      if (subscriptions.value[topic] <= 0) {
        delete subscriptions.value[topic];
      }
    }
    console.debug(
      'subscription count for topic',
      topic,
      subscriptions.value[topic],
    );
    return count;
  }

  /**
   * publishes the payload to the provided topic
   * @param topic mqtt topic to send
   * @param payload data to send, should be a valid JSON string
   * @param retain send message as retained
   * @param qos quality of service to use (0, 1, 2)
   */
  function doPublish(
    topic: string,
    payload: unknown,
    retain: boolean = true,
    qos: QoS = 2,
  ) {
    console.debug('doPublish', topic, payload);
    if (!mqttClient) {
      console.error('mqttClient is not initialized');
      return;
    }
    const options: IClientPublishOptions = {
      qos: qos,
      retain: retain,
    };
    mqttClient.publish(topic, JSON.stringify(payload), options, (error) => {
      if (error) {
        console.error('Publish error', error);
      }
    });
  }

  /**
   * replaces "openWB/" with "openWB/set/" and publishes this topic
   * @param topic mqtt topic to send
   * @param payload payload, should be a valid JSON string
   */
  function sendTopicToBroker(topic: string, payload: unknown = undefined) {
    const setTopic = topic.replace('openWB/', 'openWB/set/');
    if (payload === undefined) {
      payload = topics.value[topic];
    }
    doPublish(setTopic, payload);
  }

  /**
   * Sends a command via broker to the backend
   * @param event Command object to send
   */
  function sendCommand(event: unknown) {
    doPublish(
      'openWB/set/command/' + mqttClient?.options.clientId + '/todo',
      event,
      false,
    );
  }

  /**
   * prepares a valid command from a system event
   * @param command command to send
   * @param data data to send
   */
  function sendSystemCommand(command: string, data: unknown = {}) {
    sendCommand({
      command: command,
      data: data,
    });
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
        // check if baseTopic is already subscribed
        if (!Object.keys(subscriptions.value).includes(baseTopic)) {
          console.debug('auto subscription of wildcard topic', baseTopic);
          subscribe(baseTopic);
        }
      } else {
        // auto subscription of regex patterns not possible
        console.warn(
          'auto subscription of regex topic not possible',
          baseTopic,
        );
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
   * Get all object ids of a specific type from the hierarchy
   * @param type type of object to get the ids from
   * @returns number[]
   */
  const getObjectIds = computed(() => {
    return (type: string) => {
      function getId(hierarchy: Hierarchy[]) {
        let result: number[] = [];
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
      return getId(
        getValue.value('openWB/counter/get/hierarchy') as Hierarchy[],
      );
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
      defaultValue: unknown = undefined,
    ): unknown => {
      if (!(topic in subscriptions.value)) {
        console.debug('auto subscription of topic', topic);
        subscribe(topic, defaultValue);
      }
      let topicObject = topics.value[topic];
      if (objectPath == undefined || topicObject == undefined) {
        return topicObject;
      }
      const path = objectPath.split('.');
      for (let i = 0; i < path.length; i++) {
        if (topicObject[path[i]] == undefined) {
          console.error('path not found', topicObject, path[i]);
          return defaultValue;
        }
        topicObject = topicObject[path[i]];
      }
      console.debug('getValue', topic, objectPath, topicObject);
      return topicObject;
    };
  });

  /**
   * Get a formatted string for a value
   * @param value value to format
   * @param unit unit to use, default is 'W'
   * @param unitPrefix unit prefix to use, default is ''
   * @param scale flag to scale the value, default is true
   * @param inverted flag to invert the value, default is false
   * @param defaultString default string to use, default is '---'
   * @returns object
   */
  const getValueObject = computed(() => {
    return (
      value: number,
      unit: string = 'W',
      unitPrefix: string = '',
      scale: boolean = true,
      inverted: boolean = false,
      defaultString: string = '---',
    ) => {
      let scaled = false;
      let scaledValue = value;
      let textValue = defaultString;
      if (value === undefined) {
        console.debug(
          'value is undefined! using default',
          value,
          defaultString,
        );
      } else {
        if (inverted) {
          scaledValue = value *= -1;
        }
        textValue = value.toLocaleString(undefined, {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        });
        while (scale && (scaledValue > 999 || scaledValue < -999)) {
          scaledValue = scaledValue / 1000;
          scaled = true;
          switch (unitPrefix) {
            case '':
              unitPrefix = 'k';
              break;
            case 'k':
              unitPrefix = 'M';
              break;
            case 'M':
              unitPrefix = 'G';
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
      } as ValueObject;
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

  /**
   * Get the charge point ids
   * @returns number[]
   */
  const chargePointIds = computed(() => {
    return getObjectIds.value('cp');
  });

  /**
   * Get the charge point name identified by the charge point id
   * @param chargePointId charge point id
   * @returns string
   */
  const chargePointName = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/config`,
        'name',
      );
    };
  });

  /**
   * Get or set the charge point manual lock state identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean
   */
  const chargePointManualLock = (chargePointId: number) => {
    return computed({
      get() {
        return getValue.value(
          `openWB/chargepoint/${chargePointId}/set/manual_lock`,
        );
      },
      set(newValue: boolean) {
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/manual_lock`,
          newValue,
          undefined,
          true,
        );
      },
    });
  };

  /**
   * Get the charge point plug state identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean
   */
  const chargePointPlugState = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/plug_state`,
      );
    };
  });

  /**
   * Get the charge point charge state identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean
   */
  const chargePointChargeState = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/charge_state`,
      );
    };
  });

  /**
   * Get power sum total for all charge points
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointSumPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const power = getValue.value(
        'openWB/chargepoint/get/power',
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get the charge point power identified by the charge point id
   * @param chargePointId charge point id
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointPower = computed(() => {
    return (chargePointId: number, returnType: string = 'textValue') => {
      const power = getValue.value(
        `openWB/chargepoint/${chargePointId}/get/power`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get the charge point energy charged identified by the charge point id
   * @param chargePointId charge point id
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointEnergyCharged = computed(() => {
    return (chargePointId: number, returnType: string = 'textValue') => {
      const energyCharged = getValue.value(
        `openWB/chargepoint/${chargePointId}/get/energy_charged`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(energyCharged, 'Wh');
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, energyCharged);
    };
  });

  /**
   * Get the charge point energy charged since plugged in identified by the charge point id
   * @param chargePointId charge point id
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointEnergyChargedPlugged = computed(() => {
    return (chargePointId: number, returnType: string = 'textValue') => {
      const energyCharged = getValue.value(
        `openWB/chargepoint/${chargePointId}/set/log`,
        'imported_since_plugged',
      ) as number;
      const valueObject = getValueObject.value(energyCharged, 'Wh');
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, energyCharged);
    };
  });

  /**
   * Get the charge point number of phases in use identified by the charge point id
   */
  const chargePointPhaseNumber = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/phases_in_use`,
      ) as number;
    };
  });

  /**
   * Get the charge point charging current identified by the charge point id
   */
  const chargePointChargingCurrent = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/set/current`,
      ) as number;
    };
  });

  /**
   * Get the charge point state message identified by the charge point id
   */
  const chargePointStateMessage = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/state_str`,
      ) as string;
    };
  });

  /**
   * Get the charge point fault message identified by the charge point id
   */
  const chargePointFaultMessage = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/fault_str`,
      ) as string;
    };
  });

  /**
   * Get the charge point fault state identified by the charge point id
   */
  const chargePointFaultState = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/fault_state`,
      ) as number;
    };
  });

  /**
   * Get the charge point connected vehicle info identified by the charge point id
   * @param chargePointId charge point id
   * @returns ChargePointConnectedVehicleInfo
   */
  const chargePointConnectedVehicleInfo = (chargePointId: number) => {
    return computed({
      get() {
        return getValue.value(
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`,
        ) as ChargePointConnectedVehicleInfo;
      },
      set(newValue: ChargePointConnectedVehicleInfo) {
        updateTopic(
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`,
          newValue,
          undefined,
          true,
        );
        sendTopicToBroker(
          `openWB/chargepoint/${chargePointId}/config/ev`,
          newValue.id,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle charge mode identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleChargeMode = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.selected;
      },
      set(newValue: string) {
        console.debug('set charge mode', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.selected',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant charging current identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleInstantChargeCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.instant_charging?.current;
      },
      set(newValue: number) {
        console.debug('set instant charging current', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.instant_charging.current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant charging current identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleInstantChargeLimit = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.instant_charging?.limit?.selected;
      },
      set(newValue: string) {
        console.debug('set instant charging limit', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.instant_charging.limit.selected',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant SoC limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleInstantChargeLimitSoC = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.instant_charging?.limit?.soc;
      },
      set(newValue: number) {
        console.debug('set instant SoC limit', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.instant_charging.limit.soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant energy limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleInstantChargeEnergieLimit = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const energyValue =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.instant_charging?.limit?.amount;
        if (energyValue === undefined) {
          return;
        }
        const valueObject = getValueObject.value(
          energyValue,
          'Wh',
          '',
          true,
        ) as ValueObject;
        return valueObject.scaledValue as number;
      },
      set(newValue: number) {
        console.debug('set instant energy limit', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue * 1000,
          'chargemode.instant_charging.limit.amount',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv min current identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePVChargeMinCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_current;
      },
      set(newValue: number) {
        console.debug('set pv min current', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.pv_charging.min_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv min SoC identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePVChargeMinSoc = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_soc;
      },
      set(newValue: number) {
        console.debug('set pv min SoC', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.pv_charging.min_soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv min SoC Current identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePVChargeMinSocCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_soc_current;
      },
      set(newValue: number) {
        console.debug('set pv min SoC Current', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.pv_charging.min_soc_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv max SoC limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePVChargeMaxSoc = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.max_soc;
      },
      set(newValue: number) {
        console.debug('set pv max SoC limit', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.pv_charging.max_soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv feed in limit active identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePVChargeFeedInLimit = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.feed_in_limit;
      },
      set(newValue: boolean) {
        console.debug('set pv feed in limit active', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'chargemode.pv_charging.feed_in_limit',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle charge priority identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean | undefined
   */
  const chargePointConnectedVehiclePriority = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.prio;
      },
      set(newValue: boolean) {
        console.debug('set charge priority', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          'prio',
          true,
        );
      },
    });
  };

  /**
   * Get the charge point connected vehicle config identified by the charge point id
   * @param chargePointId charge point id
   * @returns ChargePointConnectedVehicleConfig
   */
  const chargePointConnectedVehicleConfig = (chargePointId: number) => {
    return computed(() => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/connected_vehicle/config`,
      ) as ChargePointConnectedVehicleConfig;
    });
  };

  /**
   * Get the charge point connected vehicle SoC data identified by the charge point id
   * @param chargePointId charge point id
   * @returns ChargePointConnectedVehicleSoc
   */
  const chargePointConnectedVehicleSoc = (chargePointId: number) => {
    return computed(() => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`,
      ) as ChargePointConnectedVehicleSoc;
    });
  };

  /**
   * Get the charge point connected vehicle charge template index identified by the charge point id
   * @param chargePointId charge point id
   * @returns number
   */
  const chargePointConnectedVehicleChargeTemplateIndex = (
    chargePointId: number,
  ): number | undefined => {
    return computed(() => {
      return chargePointConnectedVehicleConfig(chargePointId).value
        ?.charge_template;
    }).value;
  };

  /**
   * Get or set the charge point connected vehicle charge template identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleChargeTemplate = (chargePointId: number) => {
    return computed({
      get() {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.debug('chargeTemplateId is undefined');
          return;
        }
        return getValue.value(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
        ) as ChargeTemplateConfiguration;
      },
      set(newValue: ChargeTemplateConfiguration) {
        console.debug('set charge template', newValue, chargePointId);
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) {
          console.error('chargeTemplateId is undefined');
          return;
        }
        return updateTopic(
          `openWB/vehicle/template/charge_template/${chargeTemplateId}`,
          newValue,
          undefined,
          true,
        );
      },
    });
  };

  ////////////////////////////// Battery individual ////////////////////////////////

  /**
   * Get the battery name identified by the battery ID
   * @param batteryId battery ID
   * @returns string
   */
  const batteryName = computed(() => {
    return (batteryId: number): string => {
      const configuration = getWildcardValues.value(
        `openWB/system/device/+/component/${batteryId}/config`,
      );
      if (Object.keys(configuration).length === 0) {
        const index = batteryIds.value.indexOf(batteryId);
        return `Speicher ${index + 1}` as string; // Returns sequential name based on id index
      }
      console.log('battery configuration', configuration);
      return configuration[Object.keys(configuration)[0]].name as string;
    };
  });

  /**
   * Get the SoC, for each individual battery
   * @returns number
   */
  const batterySoc = computed(() => {
    return (batteryId: number): number | undefined => {
      const soc = getValue.value(`openWB/bat/${batteryId}/get/soc`);
      if (soc === undefined) {
        return undefined;
      }
      return soc as number;
    };
  });

  /**
   * Get the battery power identified by the battery point id
   * @param batteryId battery point id
   * @param returnType type of return value, 'textValue', 'absoluteTextValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryPower = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const power = getValue.value(
        `openWB/bat/${batteryId}/get/power`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      if (returnType === 'absoluteTextValue') {
        const absValue = Math.abs(power);
        const valueObject = getValueObject.value(absValue, 'W', '', true);
        return valueObject.textValue as string;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get the battery daily imported energy of a given battery id
   * @param batteryId charge point id
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyImported = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const energy = getValue.value(
        `openWB/bat/${batteryId}/get/daily_imported`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(energy, 'Wh', '', true);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  /**
   * Get the battery daily exported energy of a given battery id
   * @param batteryId charge point id
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyExported = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const energy = getValue.value(
        `openWB/bat/${batteryId}/get/daily_exported`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(energy, 'Wh', '', true);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  ////////////////////////////// Battery totals ////////////////////////////////

  /**
   * Get battery configured boolean true or false
   * @returns boolean
   */
  const batteryConfigured = computed(() => {
    return getValue.value('openWB/bat/config/configured', undefined) as boolean;
  });

  /**
   * Get the battery ids
   * @returns number[]
   */
  const batteryIds = computed(() => {
    return getObjectIds.value('bat') as number[];
  });

  /**
   * Get the total power of all batteries
   * @param returnType type of return value, 'textValue', 'absoluteTextValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns number | string
   */
  const batteryTotalPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const totalPower = batteryIds.value.reduce((sum, batteryId) => {
        const power = batteryPower.value(batteryId, 'value');
        return sum + (typeof power === 'number' ? power : 0);
      }, 0);
      if (returnType === 'absoluteTextValue') {
        const absValue = Math.abs(totalPower);
        const valueObject = getValueObject.value(absValue, 'W', '', true);
        return valueObject.textValue as string;
      }
      if (returnType === 'textValue') {
        const valueObject = getValueObject.value(totalPower, 'W', '', true);
        return valueObject.textValue as string;
      }
      return totalPower as string | number;
    };
  });

  /**
   * Get the SoC, averaged over all batteries
   * @returns number
   */
  const batterySocTotal = computed(() => {
    return getValue.value('openWB/bat/get/soc') as number;
  });

  /**
   * Get the battery daily imported energy total of all batteries
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyImportedTotal = computed(() => {
    return (returnType: string = 'textValue') => {
      const importedEnergy = getValue.value(
        'openWB/bat/get/daily_imported',
      ) as number;
      const valueObject = getValueObject.value(importedEnergy, 'Wh', '', true);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, importedEnergy);
    };
  });

  /**
   * Get the battery daily exported energy total of all batteries
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyExportedTotal = computed(() => {
    return (returnType: string = 'textValue') => {
      const exportedEnergy = getValue.value(
        'openWB/bat/get/daily_exported',
      ) as number;
      const valueObject = getValueObject.value(exportedEnergy, 'Wh', '', true);
      if (Object.hasOwnProperty.call(valueObject, returnType)) {
        return valueObject[returnType];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, exportedEnergy);
    };
  });

  /**
   * Get or set the PV battery charging mode
   * @param
   * @returns string
   */
  const batteryMode = () => {
    return computed({
      get() {
        return getValue.value(
          'openWB/general/chargemode_config/pv_charging/bat_mode',
        ) as string;
      },
      set(newValue: string) {
        return updateTopic(
          'openWB/general/chargemode_config/pv_charging/bat_mode',
          newValue,
          undefined,
          true,
        );
      },
    });
  };

  ////////////////////////////// vehicle data ////////////////////////////////

  /**
   * Get a list of all vehicles
   * @returns Vehicle[]
   */
  const vehicleList = () => {
    const list = getWildcardValues.value('openWB/vehicle/+/name');
    // generate an array of objects, containing vehicle index and name
    return Object.keys(list).map((key) => {
      const vehicleIndex = parseInt(key.split('/')[2]);
      return {
        id: vehicleIndex,
        name: list[key] as string,
      } as Vehicle;
    });
  };

  /**
   * Add a scheduled charging plan to currently selected vehicle of the current charge point
   * @param chargePointId charge point id
   */
  const vehicleAddScheduledChargingPlan = (chargePointId: number) => {
    const chargeTemplateId =
      chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
    if (chargeTemplateId === undefined) return;
    sendCommand({
      command: 'addChargeTemplateSchedulePlan',
      data: { template: chargeTemplateId },
    });
  };

  /**
   * Delete scheduled charging plan from currently selected vehicle of the current charge point
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   */
  const vehicleDeleteScheduledChargingPlan = (
    chargePointId: number,
    planId: string,
  ) => {
    const chargeTemplateId =
      chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
    if (chargeTemplateId === undefined) return;
    sendCommand({
      command: 'removeChargeTemplateSchedulePlan',
      data: {
        template: parseInt(chargeTemplateId.toString()),
        plan: parseInt(planId),
      },
    });
  };

  /**
   * Get charging plan/s data identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const vehicleScheduledChargingPlans = (chargePointId: number) => {
    return computed(() => {
      const chargeTemplateId =
        chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
      if (chargeTemplateId === undefined) return [];

      const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans`;
      const plans = getWildcardValues.value(`${baseTopic}/+`) as Record<
        string,
        Omit<ScheduledChargingPlan, 'id' | 'frequency.selected_days'>
      >;
      //filter used here to prevent undefined values in the plans object due to mqtt topic loading time
      return Object.keys(plans)
        .filter((planKey) => plans[planKey] && plans[planKey].frequency)
        .map((planKey) => {
          const plan = plans[planKey];
          const planId = planKey.split('/').pop() || '';
          return {
            ...plan,
            id: planId,
            frequency: {
              ...plan.frequency,
              selected_days: getSelectedDays(plan.frequency.weekly),
            },
          } as ScheduledChargingPlan;
        });
    });
  };

  /**
   * Helper function to convert a boolean array to a string array of selected days
   * @param weekly boolean array of selected days
   * @returns string[] string array of selected days
   */
  const getSelectedDays = (weekly: boolean[] | undefined): string[] => {
    const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

    return weekly
      ? (weekly
          .map((isSelected, index) => (isSelected ? weekDays[index] : null))
          .filter(Boolean) as string[]) // Filter out null values
      : [];
  };

  /**
   * Get or set the active state of the scheduled charging plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns boolean | undefined
   */
  const vehicleScheduledChargingPlanActive = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.active;
      },
      set(newValue: boolean) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'active', true);
      },
    });
  };

  /**
   * Get the next scheduled charging plan target (scheduled SoC and time) for the current active scheduled charging plans identified by the charge point id
   * @param chargePointId charge point id
   * @returns object
   */
  const vehicleScheduledChargingTarget = (
    chargePointId: number,
  ): ComputedRef<{ soc: number; time: string }> => {
    return computed(() => {
      const plans = vehicleScheduledChargingPlans(chargePointId)
        .value as ScheduledChargingPlan[];
      const activePlans = plans.filter((plan) => plan.active);
      if (activePlans.length === 0) return { soc: 0, time: 'keine' };
      // Get current time
      const now = new Date();
      const currentTime = now.getHours() * 60 + now.getMinutes(); // Convert current time to minutes
      // Sort plans considering current time
      const sortedPlans = activePlans.sort((a, b) => {
        const [hoursA, minutesA] = a.time.split(':').map(Number);
        const [hoursB, minutesB] = b.time.split(':').map(Number);
        const timeA = hoursA * 60 + minutesA; // Convert plan time to minutes
        const timeB = hoursB * 60 + minutesB;
        // Adjust times if they're earlier than current time (add 24 hours worth of minutes)
        const adjustedTimeA = timeA <= currentTime ? timeA + 24 * 60 : timeA;
        const adjustedTimeB = timeB <= currentTime ? timeB + 24 * 60 : timeB;
        return adjustedTimeA - adjustedTimeB;
      });
      const soonestPlan = sortedPlans[0];
      return {
        soc:
          soonestPlan.limit.selected === 'soc'
            ? (soonestPlan.limit.soc_scheduled as number)
            : 0,
        time: soonestPlan.time,
      };
    });
  };

  /**
   * Get or set the current for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanCurrent = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.current as number;
      },
      set(newValue: number) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'current', true);
      },
    });
  };

  /**
   * Get or set the charge limit for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns string | undefined
   */
  const vehicleScheduledChargingPlanLimitSelected = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.limit.selected;
      },
      set(newValue: string) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'limit.selected', true);
      },
    });
  };

  /**
   * Get or set the energy limit for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanEnergyAmount = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        const amount = plan?.limit.amount;
        if (amount === undefined) {
          return;
        }
        const valueObject = getValueObject.value(
          amount,
          'Wh',
          '',
          true,
        ) as ValueObject;
        return valueObject.scaledValue as string;
      },
      set(newValue: number) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue * 1000, 'limit.amount', true);
      },
    });
  };

  /**
   * Get or set the plan name for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns string | undefined
   */
  const vehicleScheduledChargingPlanName = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.name;
      },
      set(newValue: string) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'name', true);
      },
    });
  };

  /**
   * Get or set the end time for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns string | undefined
   */
  const vehicleScheduledChargingPlanTime = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.time;
      },
      set(newValue: string) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'time', true);
      },
    });
  };

  /**
   * Get or set the plan frequency for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns string | undefined
   */
  const vehicleScheduledChargingPlanFrequencySelected = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.frequency.selected;
      },
      set(newValue: 'once' | 'daily' | 'weekly') {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'frequency.selected', true);
      },
    });
  };

  /**
   * Get or set the date for one off scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns string[] | undefined
   */
  const vehicleScheduledChargingPlanOnceDate = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.frequency.once;
      },
      set(newValue: string) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'frequency.once', true);
      },
    });
  };

  /**
   * Get or set the day of the week for weekly scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns boolean[] | undefined
   */
  const vehicleScheduledChargingPlanWeeklyDays = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.frequency.weekly;
      },
      set(newValue: boolean[]) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'frequency.weekly', true);
      },
    });
  };

  /**
   * Get or set the SoC when excess PV energy is available at scheduled end time for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanSocLimit = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.limit.soc_limit;
      },
      set(newValue: number) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'limit.soc_limit', true);
      },
    });
  };

  /**
   * Get or set the SoC at scheduled end time for scheduled charge plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanSocScheduled = (
    chargePointId: number,
    planId: string,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans(chargePointId).value;
        const plan = plans.find((p) => p.id === planId);
        return plan?.limit.soc_scheduled;
      },
      set(newValue: number) {
        const chargeTemplateId =
          chargePointConnectedVehicleChargeTemplateIndex(chargePointId);
        if (chargeTemplateId === undefined) return;
        const baseTopic = `openWB/vehicle/template/charge_template/${chargeTemplateId}/chargemode/scheduled_charging/plans/${planId}`;
        updateTopic(baseTopic, newValue, 'limit.soc_scheduled', true);
      },
    });
  };

  /////////////////////////////// Grid Data /////////////////////////////////////

  /**
   * Get counter id from root of component hierarchy
   * @returns number | undefined
   */
  const getGridId = computed(() => {
    const hierarchy = getValue.value(
      'openWB/counter/get/hierarchy',
    ) as Hierarchy[];

    if (hierarchy && hierarchy.length > 0) {
      const firstElement = hierarchy[0];
      if (firstElement.type === 'counter') {
        return firstElement.id;
      }
    }
    return undefined;
  });

  /**
   * Get grid power identified from root of component hierarchy
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const getGridPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const gridId = getGridId.value;
      if (gridId === undefined) {
        return '---';
      }
      const power = getValue.value(
        `openWB/counter/${gridId}/get/power`,
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  ////////////////// Home data //////////////////////////

  /**
   * Get home power
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const getHomePower = computed(() => {
    return (returnType: string = 'textValue') => {
      const power = getValue.value(
        'openWB/counter/set/home_consumption',
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  ////////////////// PV data //////////////////////////

  /**
   * Get pv configured true or false
   * @returns boolean
   */
  const getPvConfigured = computed(() => {
    return getValue.value('openWB/pv/config/configured', undefined) as boolean;
  });

  /**
   * Get pv power
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const getPvPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const power = getValue.value(
        'openWB/pv/get/power',
        undefined,
        0,
      ) as number;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject as ValueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  ////////////////// Chart //////////////////////////

  /**
   * Get live chart data
   * @returns GraphDataPoint[]
   */
  const chartData = computed(() => {
    const list = getWildcardValues.value('openWB/graph/+');
    const result: GraphDataPoint[] = [];

    Object.entries(list).forEach(([topic, data]) => {
      if (topic.includes('alllivevaluesJson') && typeof data === 'string') {
        const lines = data.split('\n');
        lines.forEach((line) => {
          if (line && line.startsWith('{') && line.endsWith('}')) {
            const dataPoint = JSON.parse(line);
            result.push(dataPoint);
          }
        });
      }
    });
    return result.sort((a, b) => a.timestamp - b.timestamp);
  });

  // exports
  return {
    topics,
    subscriptions,
    initialize,
    updateTopic,
    updateState: updateTopic, // alias for compatibility with older code
    subscribe,
    unsubscribe,
    sendTopicToBroker,
    sendSystemCommand,
    getValue,
    systemVersion,
    systemIp,
    systemBranch,
    systemCommit,
    themeConfiguration,
    systemDateTime,
    // charge point data
    chargePointIds,
    chargePointName,
    chargePointManualLock,
    chargePointPlugState,
    chargePointChargeState,
    chargePointSumPower,
    chargePointPower,
    chargePointEnergyCharged,
    chargePointEnergyChargedPlugged,
    chargePointPhaseNumber,
    chargePointChargingCurrent,
    chargePointStateMessage,
    chargePointFaultState,
    chargePointFaultMessage,
    chargePointConnectedVehicleInfo,
    chargePointConnectedVehicleChargeMode,
    chargePointConnectedVehicleInstantChargeCurrent,
    chargePointConnectedVehicleInstantChargeLimit,
    chargePointConnectedVehicleInstantChargeLimitSoC,
    chargePointConnectedVehicleInstantChargeEnergieLimit,
    chargePointConnectedVehiclePVChargeMinCurrent,
    chargePointConnectedVehiclePVChargeMinSoc,
    chargePointConnectedVehiclePVChargeMinSocCurrent,
    chargePointConnectedVehiclePVChargeMaxSoc,
    chargePointConnectedVehiclePVChargeFeedInLimit,
    chargePointConnectedVehiclePriority,
    chargePointConnectedVehicleChargeTemplate,
    // vehicle data
    vehicleList,
    chargePointConnectedVehicleSoc,
    vehicleAddScheduledChargingPlan,
    vehicleDeleteScheduledChargingPlan,
    vehicleScheduledChargingPlans,
    vehicleScheduledChargingPlanActive,
    vehicleScheduledChargingTarget,
    vehicleScheduledChargingPlanCurrent,
    vehicleScheduledChargingPlanLimitSelected,
    vehicleScheduledChargingPlanEnergyAmount,
    vehicleScheduledChargingPlanName,
    vehicleScheduledChargingPlanTime,
    vehicleScheduledChargingPlanFrequencySelected,
    vehicleScheduledChargingPlanOnceDate,
    vehicleScheduledChargingPlanWeeklyDays,
    vehicleScheduledChargingPlanSocLimit,
    vehicleScheduledChargingPlanSocScheduled,
    // Battery data
    batteryConfigured,
    batteryIds,
    batteryName,
    batterySoc,
    batteryPower,
    batteryDailyImported,
    batteryDailyExported,
    batterySocTotal,
    batteryDailyImportedTotal,
    batteryDailyExportedTotal,
    batteryTotalPower,
    batteryMode,
    // Grid data
    getGridId,
    getGridPower,
    // Home data
    getHomePower,
    // PV data
    getPvConfigured,
    getPvPower,
    // Chart data
    chartData,
  };
});
