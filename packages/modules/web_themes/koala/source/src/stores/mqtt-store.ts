import { defineStore } from 'pinia';
import { ref, computed, ComputedRef } from 'vue';
import mqtt, { IClientOptions, IClientPublishOptions } from 'mqtt';
import { QoS } from 'mqtt-packet';
import { useQuasar } from 'quasar';

// import all type definitions from the mqtt-store-model
import type {
  TopicObject,
  TopicList,
  TopicCount,
  Hierarchy,
  ChargePointConnectedVehicleConfig,
  ChargeTemplateConfiguration,
  ValueObject,
  ChargePointConnectedVehicleInfo,
  Vehicle,
  VehicleInfo,
  ScheduledChargingPlan,
  ChargePointConnectedVehicleSoc,
  GraphDataPoint,
  BatteryConfiguration,
  CounterConfiguration,
  ThemeConfiguration,
  VehicleActivePlan,
  TimeChargingPlan,
  VehicleChargeTarget,
  CalculatedSocState,
  SystemCommandEvent,
} from './mqtt-store-model';

export const useMqttStore = defineStore('mqtt', () => {
  const $q = useQuasar();
  let mqttUser = null;
  let mqttPass = null;
  if ($q.cookies.has('mqtt')) {
    [mqttUser, mqttPass] = decodeURIComponent($q.cookies.get('mqtt')).split(
      ':',
    ) || [null, null];
  } else {
    $q.notify({
      type: 'warning',
      message: 'Anonyme Anmeldung!',
      progress: true,
    });
  }

  // local variables
  let mqttClient: mqtt.MqttClient | undefined = undefined;
  const mqttConnectionOptions: IClientOptions = {
    protocol: location.protocol == 'https:' ? 'wss' : 'ws',
    protocolVersion: 5,
    host: location.hostname,
    port: parseInt(location.port) || (location.protocol == 'https:' ? 443 : 80),
    path: '/ws',
    username: mqttUser,
    password: mqttPass,
    connectTimeout: 4000,
    reconnectPeriod: 4000,
    resubscribe: true,
    properties: {
      requestResponseInformation: true,
      requestProblemInformation: true,
    },
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
    const { protocol, host, port, path, ...options } = mqttConnectionOptions;
    const connectUrl = `${protocol}://${host}:${port}${path}`;
    console.debug('connecting to broker:', connectUrl);
    try {
      mqttClient = mqtt.connect(connectUrl, options);
      mqttClient.on('connect', () => {
        console.debug('connected to broker');
        $q.notify({
          type: 'positive',
          message: `Anmeldung ${mqttUser ? 'als Benutzer "' + mqttUser + '" ' : ''}erfolgreich`,
          progress: true,
        });
      });
      mqttClient.on('error', (error) => {
        console.error('Client error', error);
        $q.notify({
          type: 'negative',
          message:
            'Es ist ein Fehler aufgetreten!' +
            (error instanceof mqtt.ErrorWithReasonCode
              ? `(${(error as mqtt.ErrorWithReasonCode).code})`
              : ''),
          caption: (error as Error).message,
          progress: true,
        });
        // handle not authorized error (code 137)
        if (
          (error as mqtt.ErrorWithReasonCode).code === 137 &&
          mqttUser != null
        ) {
          mqttClient.end();
          if ($q.cookies.has('mqtt')) {
            $q.cookies.remove('mqtt', { path: '/' });
            console.warn('removed mqtt cookie due to error');
            $q.notify({
              type: 'warning',
              message: 'Die Anmeldeinformationen wurden entfernt.',
              timeout: 0,
              closeBtn: 'Seite neu laden',
              onDismiss: () => {
                this.router.go(0);
              },
            });
          }
        }
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
      $q.notify({
        type: 'negative',
        message: 'Verbindungsfehler!',
        caption: (error as Error).message,
        progress: true,
      });
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
      const originalValue = JSON.parse(JSON.stringify(getValue.value(topic)));
      if (objectPath != undefined) {
        setPath(topics.value[topic], objectPath, payload);
      } else {
        topics.value[topic] = payload;
      }
      if (publish) {
        console.debug(
          'publish topic',
          topic,
          topics.value[topic],
          originalValue,
        );
        sendTopicToBroker(topic, topics.value[topic], originalValue);
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
    silent: boolean = false,
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
              console.error('Subscribe to topics error', topic, error);
              if (!silent) {
                if (mqttUser) {
                  $q.notify({
                    type: 'negative',
                    message: `Fehler beim Abonnieren der Daten "${topic}"`,
                    caption: error.message,
                    progress: true,
                  });
                } else {
                  $q.notify({
                    type: 'warning',
                    message:
                      'Fehler beim Abonnieren von Daten. Möglicherweise ist eine Anmeldung erforderlich.',
                    caption: error.message,
                    progress: true,
                  });
                }
              }
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
              console.error('Unsubscribe error', topic, error);
              $q.notify({
                type: 'negative',
                message: `Fehler beim Abbestellen der Daten "${topic}"`,
                caption: error.message,
                progress: true,
              });
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
   * @returns Promise<boolean> success status
   */
  async function doPublish(
    topic: string,
    payload: unknown,
    retain: boolean = true,
    qos: QoS = 2,
  ): Promise<boolean> {
    console.debug('doPublish', topic, payload);
    if (!mqttClient) {
      console.error('mqttClient is not initialized');
      return Promise.resolve(false);
    }
    const options: IClientPublishOptions = {
      qos: qos,
      retain: retain,
    };
    // Fehlerbehandlung mit Promise und Rückgabewert
    try {
      try {
        await mqttClient.publishAsync(topic, JSON.stringify(payload), options);
        console.debug('Publish successful', topic);
        return true;
      } catch (error) {
        console.error('Publish error', topic, error);
        $q.notify({
          type: 'negative',
          message: `Fehler beim Senden der Daten "${topic}"`,
          caption: error.message,
          progress: true,
        });
        return false;
      }
    } catch (error: unknown) {
      console.error('Publish exception', topic, error);
      let message = '';
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = String(error);
      }
      $q.notify({
        type: 'negative',
        message: `Fehler beim Senden der Daten "${topic}"`,
        caption: message,
        progress: true,
      });
      return Promise.resolve(false);
    }
  }

  /**
   * replaces "openWB/" with "openWB/set/" and publishes this topic
   * @param topic mqtt topic to send
   * @param payload payload, should be a valid JSON string
   * @param originalValue original value to restore on failure
   * @returns Promise<boolean> success status
   */
  async function sendTopicToBroker(
    topic: string,
    payload: unknown = undefined,
    originalValue?: unknown,
  ): Promise<boolean> {
    const setTopic = topic.replace('openWB/', 'openWB/set/');
    if (payload === undefined) {
      payload = topics.value[topic];
    }
    const success = await doPublish(setTopic, payload);
    if (!success && originalValue !== undefined) {
      console.warn(
        'restoring original value due to publish failure',
        topic,
        originalValue,
      );
      topics.value[topic] = originalValue;
    }
    return success;
  }

  /**
   * Sends a command via broker to the backend
   * @param event Command object to send
   */
  function sendCommand(event: SystemCommandEvent) {
    console.log(
      'sendCommand',
      `openWB/set/command/${mqttClient?.options.clientId}/todo/${event.command}`,
      event,
    );
    doPublish(
      `openWB/set/command/${mqttClient?.options.clientId}/todo/${event.command}`,
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
    return (
      baseTopic: string,
      isRegex: boolean = false,
      autoSubscribe: boolean = true,
    ): TopicList => {
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
        if (
          !Object.keys(subscriptions.value).includes(baseTopic) &&
          autoSubscribe
        ) {
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
   * getValue('openWB/system/version');
   * getValue('openWB/general/web_theme', 'official');
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
        if (!Object.hasOwn(topicObject, path[i])) {
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
   * @param decimalPlaces number of decimal places to use, default is 0 or 2 for scaled values
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
      decimalPlaces: number = 0,
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
        let outputDecimalPlaces = 0;
        if (scaled) {
          outputDecimalPlaces = decimalPlaces > 0 ? decimalPlaces : 2;
        } else {
          const hasDecimalPlaces = scaledValue !== Math.floor(scaledValue);
          outputDecimalPlaces = hasDecimalPlaces ? decimalPlaces : 0;
        }
        textValue = scaledValue.toLocaleString(undefined, {
          minimumFractionDigits: outputDecimalPlaces,
          maximumFractionDigits: outputDecimalPlaces,
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
      | ThemeConfiguration
      | undefined;
  });

  /**
   * Check if user management is active
   * Defaults to true if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const userManagementActive: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/user_management_active',
        undefined,
        true,
      ) === true
    );
  });

  /**
   * Check if access is allowed
   * Defaults to false if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const accessAllowed: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/access_allowed',
        undefined,
        false,
      ) === true
    );
  });

  /**
   * Check if settings are accessible
   * Defaults to false if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const settingsAccessible: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/settings_accessible',
        undefined,
        false,
      ) === true
    );
  });

  /**
   * Check if status is accessible
   * Defaults to false if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const statusAccessible: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/status_accessible',
        undefined,
        false,
      ) === true
    );
  });

  /**
   * Check if charge log is accessible
   * Defaults to false if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const chargeLogAccessible: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/charge_log_accessible',
        undefined,
        false,
      ) === true
    );
  });

  /**
   * Check if chart is accessible
   * Defaults to false if the value is not set as this may be due to insufficient permissions
   * @returns boolean
   */
  const chartAccessible: ComputedRef<boolean> = computed(() => {
    return (
      getValue.value(
        'openWB/system/security/chart_accessible',
        undefined,
        false,
      ) === true
    );
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
    return getObjectIds.value('cp').filter((id) => {
      return chargePointAccessible.value(id);
    });
  });

  const chargePointAccessible = computed(() => {
    return (chargePointId: number) => {
      return chargePointName.value(chargePointId) !== undefined;
    };
  });

  /**
   * Get the charge point name identified by the charge point id
   * @param chargePointId charge point id
   * @returns string | undefined
   */
  const chargePointName = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/config`,
        'name',
      ) as string | undefined;
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
      return (
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/plug_state`,
        ) as boolean) || false
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
      return (
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/charge_state`,
        ) as boolean) || false
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
      const power =
        (getValue.value(
          'openWB/chargepoint/get/power',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get daily imported energy sum total for all charge points
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointDailyImported = computed(() => {
    return (returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          'openWB/chargepoint/get/daily_imported',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  /**
   * Get daily exported energy sum total for all charge points
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const chargePointDailyExported = computed(() => {
    return (returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          'openWB/chargepoint/get/daily_exported',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
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
      const power =
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/power`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
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
      const energyCharged =
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/energy_charged`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energyCharged, 'Wh');
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
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
      const energyCharged =
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/set/log`,
          'imported_since_plugged',
        ) as number) || 0;
      const valueObject = getValueObject.value(energyCharged, 'Wh');
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energyCharged);
    };
  });

  /**
   * Get the charge point number of phases in use identified by the charge point id
   */
  const chargePointPhaseNumber = computed(() => {
    return (chargePointId: number) => {
      return (
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/phases_in_use`,
        ) as number) || 0
      );
    };
  });

  const chargePointChargingCurrent = computed(() => {
    return (chargePointId: number, returnType: string = 'textValue') => {
      const current =
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/set/current`,
        ) as number) || 0;
      const valueObject = getValueObject.value(
        current,
        'A',
        '',
        true,
        false,
        '---',
        2,
      );
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      console.error('returnType not found!', returnType, current);
    };
  });

  /**
   * Get the charge point state message identified by the charge point id
   */
  const chargePointStateMessage = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/state_str`,
      ) as string | undefined;
    };
  });

  /**
   * Get the charge point fault message identified by the charge point id
   */
  const chargePointFaultMessage = computed(() => {
    return (chargePointId: number) => {
      return getValue.value(
        `openWB/chargepoint/${chargePointId}/get/fault_str`,
      ) as string | undefined;
    };
  });

  /**
   * Get the charge point fault state identified by the charge point id
   */
  const chargePointFaultState = computed(() => {
    return (chargePointId: number) => {
      return (
        (getValue.value(
          `openWB/chargepoint/${chargePointId}/get/fault_state`,
        ) as number) || 0
      );
    };
  });

  /**
   * trigger a force SOC update for the connected vehicle
   * @param chargePointId charge point id
   * @returns void
   */
  const chargePointConnectedVehicleForceSocUpdate = (chargePointId: number) => {
    const vehicleId = chargePointConnectedVehicleInfo(chargePointId).value?.id;
    if (vehicleId !== undefined) {
      vehicleForceSocUpdate(vehicleId);
    }
  };

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
        ) as ChargePointConnectedVehicleInfo | undefined;
      },
      set(newValue: ChargePointConnectedVehicleInfo) {
        updateTopic(
          `openWB/chargepoint/${chargePointId}/get/connected_vehicle/info`,
          newValue,
          undefined,
          false,
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
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.instant_charging.current',
          true,
        );
      },
    });
  };

  /**
   * Get charge point charge type (AC/DC) identified by the charge point id
   * @param chargePointId charge point id
   * @returns string | undefined
   */
  const chargePointChargeType = (chargePointId: number) =>
    computed(() => {
      const templateId = getValue.value(
        `openWB/chargepoint/${chargePointId}/config`,
        'template',
      ) as number | undefined;
      if (templateId === undefined) return undefined;
      return getValue.value(
        `openWB/chargepoint/template/${templateId}`,
        'charging_type',
      ) as string | undefined;
    });

  /**
   * Get boolean value for DC charging enabled / disabled
   * @returns boolean
   */
  const dcChargingEnabled = computed(() => {
    return (getValue.value('openWB/optional/dc_charging') as boolean) || 0;
  });

  /**
   * Converts DC current to power in Watt
   * This function assumes a 3-phase system with a voltage of 230V
   * and calculates the AC power based on the formula: P = I * V * 3 / 1000
   * where P is power in Kilowatts, I is current in Amperes,
   * and V is voltage in Volts.
   * The result is rounded to the nearest integer.
   * @param dcCurrent DC current in Ampere
   * @returns number
   */
  const convertDcCurrentToPower = (dcCurrent: number): number => {
    return Math.round((dcCurrent * 3 * 230) / 1000);
  };

  /**
   * Converts power in Kilowatts to DC current in Ampere.
   * This function assumes a 3-phase system with a voltage of 230V
   * and calculates the DC current based on the formula: I = P * 1000 / (V * 3)
   * where P is power in Watts, I is current in Amperes,
   * and V is voltage in Volts.
   * The result is rounded to the nearest integer.
   * @param power Power in Kilowatts
   * @returns number
   */
  const convertPowerToDcCurrent = (power: number): number => {
    return Math.round((power * 1000) / (230 * 3));
  };

  /**
   * Get or set the charge point connected vehicle instant charging DC power identified by the charge point id
   * @param chargePointId charge point id
   * @returns number
   */
  const chargePointConnectedVehicleInstantDcChargePower = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const dcCurrent =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.instant_charging?.dc_current;
        if (dcCurrent !== undefined) {
          return convertDcCurrentToPower(dcCurrent);
        } else {
          return 0;
        }
      },
      set(newValue: number) {
        console.debug('set instant charging power', newValue, chargePointId);
        const newPower = convertPowerToDcCurrent(newValue);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newPower,
          'chargemode.instant_charging.dc_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant charging phases identified by the charge point id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const chargePointConnectedVehicleInstantChargePhases = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.instant_charging?.phases_to_use;
      },
      set(newValue: number) {
        console.debug('set instant charging phases', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.instant_charging.phases_to_use',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle instant charging limit identified by the charge point id
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
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
  const chargePointConnectedVehicleInstantChargeLimitEnergy = (
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
        const valueObject = getValueObject.value(energyValue, 'Wh', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        console.debug('set instant energy limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
  const chargePointConnectedVehiclePvChargeMinCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_current;
      },
      set(newValue: number) {
        console.debug('set pv min current', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.min_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle PV charging DC power identified by the charge point id
   * @param chargePointId charge point id
   * @returns number
   */
  const chargePointConnectedVehiclePvDcChargePower = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const dcMinCurrent =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.pv_charging?.dc_min_current;
        if (dcMinCurrent !== undefined) {
          return convertDcCurrentToPower(dcMinCurrent);
        } else {
          return 0;
        }
      },
      set(newValue: number) {
        console.debug('set instant charging power', newValue, chargePointId);
        const newPower = convertPowerToDcCurrent(newValue);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newPower,
          'chargemode.pv_charging.dc_min_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle PV charging DC minimum SoC Power identified by the charge point id
   * @param chargePointId charge point id
   * @returns number
   */
  const chargePointConnectedVehiclePvDcMinSocPower = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const dcMinSocCurrent =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.pv_charging?.dc_min_soc_current;
        if (dcMinSocCurrent !== undefined) {
          return Math.round((dcMinSocCurrent * 3 * 230) / 1000);
        } else {
          return 0;
        }
      },
      set(newValue: number) {
        console.debug('set instant charging power', newValue, chargePointId);
        const newPower = (newValue * 1000) / 230 / 3;
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newPower,
          'chargemode.pv_charging.dc_min_soc_current',
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
  const chargePointConnectedVehiclePvChargeMinSoc = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_soc;
      },
      set(newValue: number) {
        console.debug('set pv min SoC', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
  const chargePointConnectedVehiclePvChargeMinSocCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.min_soc_current;
      },
      set(newValue: number) {
        console.debug('set pv min SoC Current', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.min_soc_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv charging phases identified by the charge point id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const chargePointConnectedVehiclePvChargePhases = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.phases_to_use;
      },
      set(newValue: number) {
        console.debug('set pv charging phases', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.phases_to_use',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv charging phases for min soc identified by the charge point id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const chargePointConnectedVehiclePvChargePhasesMinSoc = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.phases_to_use_min_soc;
      },
      set(newValue: number) {
        console.debug(
          'set pv charging phases min soc',
          newValue,
          chargePointId,
        );
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.phases_to_use_min_soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv charging limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePvChargeLimit = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.limit?.selected;
      },
      set(newValue: string) {
        console.debug('set pv charging limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.limit.selected',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv SoC limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePvChargeLimitSoC = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.limit?.soc;
      },
      set(newValue: number) {
        console.debug('set pv SoC limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.limit.soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle pv energy limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehiclePvChargeLimitEnergy = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const energyValue =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.pv_charging?.limit?.amount;
        if (energyValue === undefined) {
          return;
        }
        const valueObject = getValueObject.value(energyValue, 'Wh', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        console.debug('set pv energy limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue * 1000,
          'chargemode.pv_charging.limit.amount',
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
  const chargePointConnectedVehiclePvChargeFeedInLimit = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.pv_charging?.feed_in_limit;
      },
      set(newValue: boolean) {
        console.debug('set pv feed in limit active', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.pv_charging.feed_in_limit',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco charging current identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleEcoChargeCurrent = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.eco_charging?.current;
      },
      set(newValue: number) {
        console.debug('set eco current', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.eco_charging.current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco charging power identified by the charge point id
   * @param chargePointId charge point id
   * @returns number
   */
  const chargePointConnectedVehicleEcoChargeDcPower = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const dcCurrent =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.eco_charging?.dc_current;
        if (dcCurrent !== undefined) {
          return convertDcCurrentToPower(dcCurrent);
        } else {
          return 0;
        }
      },
      set(newValue: number) {
        console.debug('set eco power', newValue, chargePointId);
        const newPower = convertPowerToDcCurrent(newValue);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newPower,
          'chargemode.eco_charging.dc_current',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco charging phases identified by the charge point id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const chargePointConnectedVehicleEcoChargePhases = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.eco_charging?.phases_to_use;
      },
      set(newValue: number) {
        console.debug('set eco charging phases', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.eco_charging.phases_to_use',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco charging limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleEcoChargeLimit = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.eco_charging?.limit?.selected;
      },
      set(newValue: string) {
        console.debug('set eco charging limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.eco_charging.limit.selected',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco SoC limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleEcoChargeLimitSoC = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.chargemode?.eco_charging?.limit?.soc;
      },
      set(newValue: number) {
        console.debug('set eco SoC limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'chargemode.eco_charging.limit.soc',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco energy limit identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleEcoChargeLimitEnergy = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const energyValue =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.eco_charging?.limit?.amount;
        if (energyValue === undefined) {
          return;
        }
        const valueObject = getValueObject.value(energyValue, 'Wh', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        console.debug('set eco energy limit', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue * 1000,
          'chargemode.eco_charging.limit.amount',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle eco charging max price identified by the charge point id
   * @param chargePointId charge point id
   * @returns string | undefined
   */
  const chargePointConnectedVehicleEcoChargeMaxPrice = (
    chargePointId: number,
  ) => {
    return computed({
      get() {
        const maxPrice =
          chargePointConnectedVehicleChargeTemplate(chargePointId).value
            ?.chargemode?.eco_charging?.max_price;
        if (maxPrice === undefined) {
          return;
        }
        return maxPrice * 100000;
      },
      set(newValue: number) {
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          parseFloat((newValue / 100000).toFixed(7)),
          'chargemode.eco_charging.max_price',
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
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'prio',
          true,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle time charging identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean | undefined
   */
  const chargePointConnectedVehicleTimeCharging = (chargePointId: number) => {
    return computed({
      get() {
        return chargePointConnectedVehicleChargeTemplate(chargePointId).value
          ?.time_charging.active;
      },
      set(newValue: boolean) {
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
          newValue,
          'time_charging.active',
          true,
        );
      },
    });
  };

  /**
   * Get the charge point connected vehicle bidi enabled state from vehicle template identified by the charge point id
   * @param chargePointId charge point id
   * @returns boolean
   */
  const chargePointConnectedVehicleBidiEnabled = (chargePointId: number) => {
    return computed(() => {
      const connectedVehicleEvTemplateId =
        chargePointConnectedVehicleConfig(chargePointId).value.ev_template;
      return getValue.value(
        `openWB/vehicle/template/ev_template/${connectedVehicleEvTemplateId}`,
        'bidi',
      ) as boolean;
    });
  };

  /**
   * Get or set the plan name for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanName = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.name;
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(chargePointId, planId, 'name', newValue);
      },
    });
  };

  /**
   * Add a new time charging plan for a charge point
   * @param chargePointId charge point id
   * @returns void
   */
  const addTimeChargingPlanForChargePoint = (chargePointId: number) => {
    const templateId =
      chargePointConnectedVehicleChargeTemplate(chargePointId).value?.id;
    if (templateId !== undefined) {
      sendSystemCommand('addChargeTemplateTimeChargingPlan', {
        template: templateId,
        chargepoint: chargePointId,
        changed_in_theme: true,
      });
    }
  };

  /**
   * Remove a time charging plan for a charge point
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns void
   */
  const removeTimeChargingPlanForChargePoint = (
    chargePointId: number,
    planId: number,
  ) => {
    const templateId =
      chargePointConnectedVehicleChargeTemplate(chargePointId).value?.id;
    sendSystemCommand('removeChargeTemplateTimeChargingPlan', {
      template: templateId,
      plan: planId,
      chargepoint: chargePointId,
      changed_in_theme: true,
    });
  };

  /**
   * Helper function to update a subtopic of a time charging plan
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @param propertyPath path to the property to update
   * @param newValue new value to set
   * @returns void
   */
  const updateTimeChargingPlanSubtopic = <T>(
    chargePointId: number,
    planId: number,
    propertyPath: string,
    newValue: T,
  ): void => {
    const plans = vehicleTimeChargingPlans.value(chargePointId);
    const planIndex = plans.findIndex((plan) => plan.id === planId);
    if (planIndex === -1) return;
    const objectPath = `time_charging.plans.${planIndex}.${propertyPath}`;
    updateTopic(
      `openWB/chargepoint/${chargePointId}/set/charge_template`,
      newValue,
      objectPath,
      true,
    );
  };

  /**
   * Get or set the active state of the time charging plan identified by the time charge plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns boolean | undefined
   */
  const vehicleTimeChargingPlanActive = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.active;
      },
      set(newValue: boolean) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'active',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the start time for the time charging plan identified by the time charge plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanStartTime = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.time?.[0];
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'time.0',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the start time for the time charging plan identified by the time charge plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanEndTime = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.time?.[1];
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'time.1',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the current for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns number | undefined
   */
  const vehicleTimeChargingPlanCurrent = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.current;
      },
      set(newValue: number) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'current',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the limit selected mode for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanLimitSelected = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.limit?.selected;
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.selected',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the SoC limit for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns number | undefined
   */
  const vehicleTimeChargingPlanSocLimit = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.limit?.soc;
      },
      set(newValue: number) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.soc',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the energy amount limit for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns number | undefined
   */
  const vehicleTimeChargingPlanEnergyAmount = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        const amount = plan?.limit?.amount;
        if (amount === undefined) {
          return;
        }
        const valueObject = getValueObject.value(amount, 'Wh', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        const amountKiloWattHours = newValue * 1000;
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.amount',
          amountKiloWattHours,
        );
      },
    });
  };

  /**
   * Get or set the frequency mode for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanFrequencySelected = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.frequency?.selected;
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.selected',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the "valid from" date for the time charging plan identified by the time charging plan id (once)
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanOnceDateStart = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.frequency?.once?.[0];
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.once.0',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the "valid to" date for the time charging plan identified by the time charging plan id (once)
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns string | undefined
   */
  const vehicleTimeChargingPlanOnceDateEnd = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.frequency?.once?.[1];
      },
      set(newValue: string) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.once.1',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the number of phases for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns number | undefined
   */
  const vehicleTimeChargingPlanPhases = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.phases_to_use;
      },
      set(newValue: number) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'phases_to_use',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the weekly days array for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns boolean[] | undefined
   */
  const vehicleTimeChargingPlanWeeklyDays = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed<boolean[]>({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.frequency?.weekly ?? Array(7).fill(false);
      },
      set(newValue: boolean[]) {
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.weekly',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the DC charging power for the time charging plan identified by the time charging plan id
   * @param chargePointId charge point id
   * @param planId time charging plan id
   * @returns boolean[] | undefined
   */
  const vehicleTimeChargingPlanDcPower = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleTimeChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        const current = plan?.dc_current;
        const power = convertDcCurrentToPower(current);
        const valueObject = getValueObject.value(power, 'W', '', true);
        return valueObject.scaledValue;
      },
      set(newValue) {
        const current = convertPowerToDcCurrent(newValue);
        updateTimeChargingPlanSubtopic(
          chargePointId,
          planId,
          'dc_current',
          current,
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
      ) as ChargePointConnectedVehicleConfig | undefined;
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
      ) as ChargePointConnectedVehicleSoc | undefined;
    });
  };

  /**
   * Get or set the manual SoC for a vehicle connected to a charge point
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const chargePointConnectedVehicleSocManual = (chargePointId: number) => {
    return computed({
      get() {
        const vehicleInfo =
          chargePointConnectedVehicleInfo(chargePointId).value;
        const vehicleId = vehicleInfo?.id;
        const topic = `openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`;
        const socState = getValue.value(topic) as
          | CalculatedSocState
          | undefined;
        return socState?.manual_soc ?? socState?.soc_start ?? 0;
      },
      set(newValue: number) {
        const vehicleInfo =
          chargePointConnectedVehicleInfo(chargePointId).value;
        if (!vehicleInfo) {
          console.warn('No vehicle connected to charge point', chargePointId);
          return;
        }
        const vehicleId = vehicleInfo.id;
        doPublish(
          `openWB/set/vehicle/${vehicleId}/soc_module/calculated_soc_state/manual_soc`,
          newValue,
        );
        // Also update the charge point connected vehicle soc
        const cpTopic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`;
        const cpSoc = getValue.value(cpTopic) as { soc?: number };
        if (cpSoc && cpSoc.soc !== undefined) {
          updateTopic(cpTopic, newValue, 'soc', true);
        }
      },
    });
  };

  /**
   * Get the charge point connected vehicle SoC type identified by the charge point id
   * @param chargePointId charge point id
   * @returns string | null | undefined
   */
  const chargePointConnectedVehicleSocType = (chargePointId: number) => {
    return computed(() => {
      const vehicleId =
        chargePointConnectedVehicleInfo(chargePointId).value?.id;
      if (vehicleId === undefined) return undefined;
      return vehicleSocType.value(vehicleId);
    });
  };

  /**
   * Get or set the charge point connected vehicle charge template identified by the charge point id
   * @param chargePointId charge point id
   * @returns object | undefined
   */
  const chargePointConnectedVehicleChargeTemplate = (chargePointId: number) => {
    return computed({
      get() {
        return getValue.value(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
        ) as ChargeTemplateConfiguration | undefined;
      },
      set(newValue: ChargeTemplateConfiguration) {
        console.debug('set charge template', newValue, chargePointId);
        return updateTopic(
          `openWB/chargepoint/${chargePointId}/set/charge_template`,
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
   * @returns string || undefined
   */
  const batteryName = computed(() => {
    return (batteryId: number): string => {
      const configurations = getWildcardValues.value(
        `openWB/system/device/+/component/${batteryId}/config`,
      ) as { [key: string]: BatteryConfiguration };
      if (Object.keys(configurations).length === 0) {
        return undefined;
      }
      return Object.values(configurations)[0].name;
    };
  });

  /**
   * Get the SoC, for each individual battery
   * @returns number
   */
  const batterySoc = computed(() => {
    return (batteryId: number): number | undefined => {
      return (getValue.value(`openWB/bat/${batteryId}/get/soc`) as number) || 0;
    };
  });

  /**
   * Get the battery power identified by the battery point id
   * @param batteryId battery ID
   * @param returnType type of return value, 'textValue', 'absoluteTextValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryPower = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const power =
        (getValue.value(
          `openWB/bat/${batteryId}/get/power`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      if (returnType === 'absoluteTextValue') {
        const absValue = Math.abs(power);
        const valueObject = getValueObject.value(absValue, 'W', '', true);
        return valueObject.textValue;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get the battery daily imported energy of a given battery id
   * @param batteryId battery ID
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyImported = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          `openWB/bat/${batteryId}/get/daily_imported`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh', '', true);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  /**
   * Get the battery daily exported energy of a given battery id
   * @param batteryId battery ID
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyExported = computed(() => {
    return (batteryId: number, returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          `openWB/bat/${batteryId}/get/daily_exported`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh', '', true);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
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
    return (
      (getValue.value('openWB/bat/config/configured', undefined) as boolean) ||
      false
    );
  });

  /**
   * Get the battery ids
   * @returns number[]
   */
  const batteryIds = computed(() => {
    return getObjectIds.value('bat').filter((id) => {
      return batteryAccessible.value(id);
    });
  });

  const batteryAccessible = computed(() => {
    return (batteryId: number) => {
      return batteryName.value(batteryId) !== undefined;
    };
  });

  /**
   * Get the total power of all batteries
   * @param returnType type of return value, 'textValue', 'absoluteTextValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns number | string | ValueObject | undefined
   */
  const batteryTotalPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const power =
        (getValue.value('openWB/bat/get/power', undefined, 0) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get the SoC, averaged over all batteries
   * @returns number
   */
  const batterySocTotal = computed(() => {
    return (getValue.value('openWB/bat/get/soc') as number) || 0;
  });

  /**
   * Get the battery daily imported energy total of all batteries
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject
   */
  const batteryDailyImportedTotal = computed(() => {
    return (returnType: string = 'textValue') => {
      const importedEnergy =
        (getValue.value('openWB/bat/get/daily_imported') as number) || 0;
      const valueObject = getValueObject.value(importedEnergy, 'Wh', '', true);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
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
      const exportedEnergy =
        (getValue.value('openWB/bat/get/daily_exported') as number) || 0;
      const valueObject = getValueObject.value(exportedEnergy, 'Wh', '', true);
      if (Object.hasOwn(valueObject, returnType)) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
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
        return (
          (getValue.value(
            'openWB/general/chargemode_config/pv_charging/bat_mode',
          ) as string) || undefined
        );
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
  const vehicleList = computed<Vehicle[]>(() => {
    const list = getWildcardValues.value('openWB/vehicle/+/name');
    const hideStandardFahrzeuge =
      themeConfiguration.value?.hide_standard_vehicle;
    // Filter out Standard-Fahrzeug if hideStandardFahrzeuge is true
    const filteredList = hideStandardFahrzeuge
      ? Object.fromEntries(
          Object.entries(list).filter(
            ([, name]) =>
              typeof name === 'string' && name !== 'Standard-Fahrzeug',
          ),
        )
      : list;
    // generate an array of objects, containing vehicle index and name
    return Object.keys(filteredList).map((key) => {
      const vehicleIndex = parseInt(key.split('/')[2]);
      return {
        id: vehicleIndex,
        name: filteredList[key],
      } as Vehicle;
    }).filter((vehicle) => vehicleInfo.value(vehicle.id) !== undefined);
  });

  /**
   * Get vehicle manufacturer and model info identified by the vehicle id
   * @param vehicleId vehicle id
   * @returns vehicleInfo
   */
  const vehicleInfo = computed(() => {
    return (vehicleId: number) => {
      return getValue.value(`openWB/vehicle/${vehicleId}/info`) as VehicleInfo;
    };
  });

  /**
   * Get vehicle SoC type identified by the vehicle id
   * @param vehicleId vehicle id
   * @returns string | null | undefined
   */
  const vehicleSocType = computed(() => {
    return (vehicleId: number) => {
      const socConfig = getValue.value(
        `openWB/vehicle/${vehicleId}/soc_module/config`,
      ) as { type: string } | null;
      return socConfig?.type;
    };
  });

  /**
   * Get vehicle SoC value identified by the vehicle id
   * @param vehicleId vehicle id
   * @returns number | null
   */
  const vehicleSocValue = computed(() => {
    return (vehicleId: number) => {
      return getValue.value(`openWB/vehicle/${vehicleId}/get/soc`) as
        | number
        | undefined;
    };
  });

  /**
   * Get or set the manual SoC by vehicle id
   * @param vehicleId vehicle id
   * @param chargePointId charge point id, only necessary for updating the charge point connected vehicle soc value
   * @returns number | undefined
   */
  const vehicleSocManualValue = (
    vehicleId: number | undefined,
    chargePointId?: number,
  ) => {
    return computed({
      get() {
        const topic = `openWB/vehicle/${vehicleId}/soc_module/calculated_soc_state`;
        const socState = getValue.value(topic) as
          | CalculatedSocState
          | undefined;
        return socState?.manual_soc ?? socState?.soc_start ?? 0;
      },
      set(newValue: number) {
        doPublish(
          `openWB/set/vehicle/${vehicleId}/soc_module/calculated_soc_state/manual_soc`,
          newValue,
        ).then((success) => {
          // Also update the charge point connected vehicle soc to prevent long delay in display update
          if (success && chargePointId !== undefined) {
            const cpTopic = `openWB/chargepoint/${chargePointId}/get/connected_vehicle/soc`;
            const cpSoc = getValue.value(cpTopic) as { soc?: number };
            if (cpSoc && cpSoc.soc !== undefined) {
              updateTopic(cpTopic, newValue, 'soc', false);
            }
          }
        });
      },
    });
  };

  /**
   * trigger a force SOC update for the vehicle by vehicle id
   * @param vehicleId vehicle id
   * @returns void
   */
  const vehicleForceSocUpdate = (vehicleId: number) => {
    if (vehicleId !== undefined) {
      const topic = `openWB/vehicle/${vehicleId}/get/force_soc_update`;
      sendTopicToBroker(topic, 1);
    }
  };

  /**
   * Get vehicle state identified by the vehicle id
   * @param vehicleId vehicle id
   * @returns ChargePointInfo[]
   */
  const vehicleConnectionState = computed(() => {
    return (vehicleId: number) => {
      const connectedVehicles = getWildcardValues.value(
        'openWB/chargepoint/+/get/connected_vehicle/info',
        false,
        false,
      );
      // find the vehicle id in the connected vehicles
      const vehicleInfo = Object.entries(connectedVehicles)
        .filter(([, connectedVehicle]) => connectedVehicle.id === vehicleId)
        .map(([topic]) => {
          const chargePointId = parseInt(topic.split('/')[2]); // Extrahiere die Charge-Point-ID
          return {
            id: chargePointId,
            name: chargePointName.value(chargePointId),
            plugged: chargePointPlugState.value(chargePointId),
            charging: chargePointChargeState.value(chargePointId),
          };
        });
      return vehicleInfo;
    };
  });

  /**
   * Get scheduled charging plan/s data identified by the charge point id
   * @param chargePointId charge point id
   * @returns ScheduledChargingPlan[] | undefined
   */
  const vehicleScheduledChargingPlans = computed(() => {
    return (chargePointId: number) => {
      const plans = getValue.value(
        `openWB/chargepoint/${chargePointId}/set/charge_template`,
        'chargemode.scheduled_charging.plans',
      ) as ScheduledChargingPlan[] | undefined;
      return Array.isArray(plans) ? plans : [];
    };
  });

  function addScheduledChargingPlanForChargePoint(chargePointId: number) {
    const templateId =
      chargePointConnectedVehicleChargeTemplate(chargePointId).value?.id;
    if (templateId !== undefined) {
      sendSystemCommand('addChargeTemplateSchedulePlan', {
        template: templateId,
        chargepoint: chargePointId,
        changed_in_theme: true,
      });
    } else {
      console.warn('Kein Template für ChargePoint gefunden:', chargePointId);
    }
  }

  function removeScheduledChargingPlanForChargePoint(
    chargePointId: number,
    planId: number,
  ) {
    const templateId =
      chargePointConnectedVehicleChargeTemplate(chargePointId).value?.id;
    if (templateId !== undefined) {
      sendSystemCommand('removeChargeTemplateSchedulePlan', {
        template: templateId,
        plan: planId,
        chargepoint: chargePointId,
        changed_in_theme: true,
      });
    } else {
      console.warn('Kein Template für ChargePoint gefunden:', chargePointId);
    }
  }

  /**
   * Get time charging plan/s data identified by the charge point id
   * @param chargePointId charge point id
   * @returns TimeChargingPlan[]
   */
  const vehicleTimeChargingPlans = computed(() => {
    return (chargePointId: number) => {
      const plans = getValue.value(
        `openWB/chargepoint/${chargePointId}/set/charge_template`,
        'time_charging.plans',
      ) as TimeChargingPlan[] | undefined;
      return Array.isArray(plans) ? plans : [];
    };
  });

  /**
   * Get or set the active state of the scheduled charging plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns boolean | undefined
   */
  const vehicleScheduledChargingPlanActive = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.active;
      },
      set(newValue: boolean) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'active',
          newValue,
        );
      },
    });
  };

  /**
   * Helper function to update a subtopic of a scheduled charging plan
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @param propertyPath path to the property to update
   * @param newValue new value to set
   * @returns void
   */
  const updateScheduledChargingPlanSubtopic = <T>(
    chargePointId: number,
    planId: number,
    propertyPath: string,
    newValue: T,
  ): void => {
    const plans = vehicleScheduledChargingPlans.value(chargePointId);
    const planIndex = plans.findIndex((plan) => plan.id === planId);
    if (planIndex === -1) return;
    const objectPath = `chargemode.scheduled_charging.plans.${planIndex}.${propertyPath}`;
    updateTopic(
      `openWB/chargepoint/${chargePointId}/set/charge_template`,
      newValue,
      objectPath,
      true,
    );
  };

  /**
   * Get or set the active state {energy tariff} of the scheduled charging plan identified by the scheduled charge plan id
   * @param chargePointId charge point id
   * @param planId scheduled plan id
   * @returns boolean | undefined
   */
  const vehicleScheduledChargingPlanEtActive = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.et_active;
      },
      set(newValue: boolean) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'et_active',
          newValue,
        );
      },
    });
  };

  /**
   * Get the active plan for the current connected vehicle identified by the charge point id
   * @param chargePointId charge point id
   * @returns VehicleActivePlan | undefined
   */
  const vehicleActivePlan = (
    chargePointId: number,
  ): ComputedRef<VehicleActivePlan | undefined> => {
    return computed(() => {
      const planId =
        chargePointConnectedVehicleConfig(chargePointId).value?.current_plan;
      if (planId === undefined) {
        return;
      }
      return <VehicleActivePlan>{
        id: planId,
        type: chargePointConnectedVehicleConfig(chargePointId).value
          ?.time_charging_in_use
          ? 'timeCharging'
          : 'scheduledCharging',
        plan: chargePointConnectedVehicleConfig(chargePointId).value
          ?.time_charging_in_use
          ? vehicleTimeChargingPlans
              .value(chargePointId)
              .find((plan) => plan.id === planId)
          : vehicleScheduledChargingPlans
              .value(chargePointId)
              .find((plan) => plan.id === planId),
      };
    });
  };

  /**
   *
   * @param chargePointId charge point id
   * @returns
   */
  const vehicleChargeTarget = (
    chargePointId: number,
  ): ComputedRef<VehicleChargeTarget> => {
    return computed(() => {
      const activePlan = vehicleActivePlan(chargePointId).value;
      // Check if the active plan is undefined
      if (activePlan === undefined) {
        return {
          time: undefined,
          limit_mode: undefined,
          limit: undefined,
        };
      }
      // Check if the active plan is a scheduled charging plan
      if (activePlan.type === 'scheduledCharging') {
        const activeScheduledChargingPlan =
          activePlan.plan as ScheduledChargingPlan;
        return {
          time: activeScheduledChargingPlan?.time,
          limit_mode: activeScheduledChargingPlan?.limit.selected,
          limit:
            activeScheduledChargingPlan?.limit.selected == 'soc'
              ? activeScheduledChargingPlan.limit.soc_scheduled
              : activeScheduledChargingPlan?.limit.amount,
        };
      }
      // timeCharging
      const activeTimeChargingPlan = activePlan.plan as TimeChargingPlan;
      return {
        time: activeTimeChargingPlan?.time[1],
        limit_mode: activeTimeChargingPlan?.limit.selected,
        limit:
          activeTimeChargingPlan?.limit.selected == 'soc'
            ? activeTimeChargingPlan?.limit.soc
            : activeTimeChargingPlan?.limit.amount,
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.current;
      },
      set(newValue: number) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'current',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plane) => plane.id === planId);
        return plan?.limit.selected;
      },
      set(newValue: string) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.selected',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((p) => p.id === planId);
        const amount = plan?.limit.amount;
        if (amount === undefined) {
          return;
        }
        const valueObject = getValueObject.value(amount, 'Wh', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        const amountKiloWattHours = newValue * 1000;
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.amount',
          amountKiloWattHours,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.name;
      },
      set(newValue: string) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'name',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.time;
      },
      set(newValue: string) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'time',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.frequency.selected;
      },
      set(newValue: 'once' | 'daily' | 'weekly') {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.selected',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.frequency.once;
      },
      set(newValue: string) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.once',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.frequency.weekly;
      },
      set(newValue: boolean[]) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'frequency.weekly',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.limit.soc_limit;
      },
      set(newValue: number) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.soc_limit',
          newValue,
        );
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
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.limit.soc_scheduled;
      },
      set(newValue: number) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'limit.soc_scheduled',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle scheduled charging phases identified by the charge point id and plan id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanPhases = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.phases_to_use;
      },
      set(newValue: number) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'phases_to_use',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the charge point connected vehicle scheduled charging phases identified by the charge point id and plan id
   * @param chargePointId charge point id
   * @returns number | undefined
   */
  const vehicleScheduledChargingPlanPhasesPv = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.phases_to_use_pv;
      },
      set(newValue: number) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'phases_to_use_pv',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the bidirectional charging enabled state for a scheduled charging plan
   * @param chargePointId charge point id
   * @param planId scheduled charging plan id
   * @returns boolean | undefined
   */
  const vehicleScheduledChargingPlanBidiEnabled = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        return plan?.bidi_charging_enabled;
      },
      set(newValue: boolean) {
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'bidi_charging_enabled',
          newValue,
        );
      },
    });
  };

  /**
   * Get or set the bidirectional charging enabled state for a scheduled charging plan
   * @param chargePointId charge point id
   * @param planId scheduled charging plan id
   * @returns boolean | undefined
   */
  const vehicleScheduledChargingPlanBidiPower = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        const power = plan?.bidi_power;
        const valueObject = getValueObject.value(power, 'W', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        const watts = Math.round(newValue * 1000);
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'bidi_power',
          watts,
        );
      },
    });
  };

  /**
   * Get or set the DC charging power for a scheduled charging plan (plan.dc_current)
   * @param chargePointId charge point id
   * @param planId scheduled charging plan id
   * @returns number | undefined (in kW)
   */
  const vehicleScheduledChargingPlanDcPower = (
    chargePointId: number,
    planId: number,
  ) => {
    return computed({
      get() {
        const plans = vehicleScheduledChargingPlans.value(chargePointId);
        const plan = plans.find((plan) => plan.id === planId);
        const current = plan?.dc_current;
        const power = convertDcCurrentToPower(current);
        const valueObject = getValueObject.value(power, 'W', '', true);
        return valueObject.scaledValue;
      },
      set(newValue: number) {
        const current = convertPowerToDcCurrent(newValue);
        updateScheduledChargingPlanSubtopic(
          chargePointId,
          planId,
          'dc_current',
          current,
        );
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
   * Get all counter ids from component hierarchy
   * @returns number[]
   */
  const getAllCounterIds = computed(() => {
    const hierarchy = getValue.value('openWB/counter/get/hierarchy') as
      | Hierarchy[]
      | undefined;
    const getCounterIds = (
      nodes: Hierarchy[] | undefined,
      allCounters: number[] = [],
    ): number[] => {
      if (!nodes) return allCounters;
      nodes.forEach((node) => {
        if (node.type === 'counter') allCounters.push(node.id);
        allCounters = getCounterIds(node.children, allCounters);
      });
      return allCounters;
    };
    return getCounterIds(hierarchy);
  });

  /**
   * Get all secondary counter ids from all configured counters excluding the grid counter
   * @returns number[]
   */
  const getSecondaryCounterIds = computed(() => {
    const rootCounter = getGridId.value;
    return getAllCounterIds.value.filter((id) => id !== rootCounter);
  });

  /**
   * Get the power meter(counter) name identified by the Grid ID
   * @param counterId counter ID
   * @returns string
   */
  const getComponentName = computed(() => {
    return (componentId: number): string => {
      const configurations = getWildcardValues.value(
        `openWB/system/device/+/component/${componentId}/config`,
      ) as { [key: string]: CounterConfiguration };
      if (Object.keys(configurations).length === 0) {
        return `Zähler ${componentId}`;
      }
      return Object.values(configurations)[0].name;
    };
  });

  /**
   * Get counter power identified by root grid counter in component hierarchy or counterId
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @param counterId counter ID
   * @returns string | number | ValueObject | undefined
   */
  const getCounterPower = computed(() => {
    return (returnType: string = 'textValue', counterId?: number) => {
      const id = counterId ?? getGridId.value;
      if (id === undefined) {
        return '---';
      }
      const power =
        (getValue.value(
          `openWB/counter/${id}/get/power`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get daily counter energy imported identified by root grid counter in component hierarchy or counterId
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @param counterId counter ID
   * @returns string | number | ValueObject | undefined
   */
  const counterDailyImported = computed(() => {
    return (returnType: string = 'textValue', counterId?: number) => {
      const id = counterId ?? getGridId.value;
      if (id === undefined) {
        return '---';
      }
      const energy =
        (getValue.value(
          `openWB/counter/${id}/get/daily_imported`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  /**
   * Get daily counter energy exported identified by root grid counter in component hierarchy or counterId
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @param counterId counter ID
   * @returns string | number | ValueObject | undefined
   */
  const counterDailyExported = computed(() => {
    return (returnType: string = 'textValue', counterId?: number) => {
      const id = counterId ?? getGridId.value;
      if (id === undefined) {
        return '---';
      }
      const energy =
        (getValue.value(
          `openWB/counter/${id}/get/daily_exported`,
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
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
      const power =
        (getValue.value(
          'openWB/counter/set/home_consumption',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get daily home energy yield
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const homeDailyYield = computed(() => {
    return (returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          'openWB/counter/set/daily_yield_home_consumption',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
    };
  });

  ////////////////// PV data //////////////////////////

  /**
   * Get pv configured true or false
   * @returns boolean
   */
  const getPvConfigured = computed(() => {
    return (
      (getValue.value('openWB/pv/config/configured', undefined) as boolean) ||
      false
    );
  });

  /**
   * Get pv power
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const getPvPower = computed(() => {
    return (returnType: string = 'textValue') => {
      const power =
        (getValue.value('openWB/pv/get/power', undefined, 0) as number) || 0;
      const valueObject = getValueObject.value(power);
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, power);
    };
  });

  /**
   * Get pv daily exported energy
   * @param returnType type of return value, 'textValue', 'value', 'scaledValue', 'scaledUnit' or 'object'
   * @returns string | number | ValueObject | undefined
   */
  const pvDailyExported = computed(() => {
    return (returnType: string = 'textValue') => {
      const energy =
        (getValue.value(
          'openWB/pv/get/daily_exported',
          undefined,
          0,
        ) as number) || 0;
      const valueObject = getValueObject.value(energy, 'Wh');
      if (returnType in valueObject) {
        return valueObject[returnType as keyof ValueObject];
      }
      if (returnType == 'object') {
        return valueObject;
      }
      console.error('returnType not found!', returnType, energy);
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

  /* electricity tariff provider */
  const etProviderConfigured = computed(() => {
    return (
      (getValue.value(
        'openWB/optional/ep/configured',
        undefined,
        false,
      ) as boolean) || false
    );
  });

  const etPrices = computed(() => {
    return getValue.value('openWB/optional/ep/get/prices', undefined, {}) as {
      [key: string]: number;
    };
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
    // security settings
    userManagementActive,
    accessAllowed,
    settingsAccessible,
    statusAccessible,
    chargeLogAccessible,
    chartAccessible,
    // charge point data
    chargePointIds,
    chargePointAccessible,
    chargePointName,
    chargePointManualLock,
    chargePointPlugState,
    chargePointChargeState,
    chargePointSumPower,
    chargePointDailyImported,
    chargePointDailyExported,
    chargePointPower,
    chargePointEnergyCharged,
    chargePointEnergyChargedPlugged,
    chargePointPhaseNumber,
    chargePointChargingCurrent,
    chargePointStateMessage,
    chargePointFaultState,
    chargePointFaultMessage,
    chargePointChargeType,
    dcChargingEnabled,
    chargePointConnectedVehicleInfo,
    chargePointConnectedVehicleForceSocUpdate,
    chargePointConnectedVehicleChargeMode,
    chargePointConnectedVehicleInstantChargeCurrent,
    chargePointConnectedVehicleInstantDcChargePower,
    chargePointConnectedVehicleInstantChargePhases,
    chargePointConnectedVehicleInstantChargeLimit,
    chargePointConnectedVehicleInstantChargeLimitSoC,
    chargePointConnectedVehicleInstantChargeLimitEnergy,
    chargePointConnectedVehiclePvChargeMinCurrent,
    chargePointConnectedVehiclePvChargePhases,
    chargePointConnectedVehiclePvChargeLimit,
    chargePointConnectedVehiclePvChargeLimitSoC,
    chargePointConnectedVehiclePvChargeLimitEnergy,
    chargePointConnectedVehiclePvChargeMinSoc,
    chargePointConnectedVehiclePvChargeMinSocCurrent,
    chargePointConnectedVehiclePvDcChargePower,
    chargePointConnectedVehiclePvDcMinSocPower,
    chargePointConnectedVehiclePvChargePhasesMinSoc,
    chargePointConnectedVehiclePvChargeFeedInLimit,
    chargePointConnectedVehicleEcoChargeCurrent,
    chargePointConnectedVehicleEcoChargeDcPower,
    chargePointConnectedVehicleEcoChargePhases,
    chargePointConnectedVehicleEcoChargeLimit,
    chargePointConnectedVehicleEcoChargeLimitSoC,
    chargePointConnectedVehicleEcoChargeLimitEnergy,
    chargePointConnectedVehicleEcoChargeMaxPrice,
    chargePointConnectedVehiclePriority,
    chargePointConnectedVehicleTimeCharging,
    chargePointConnectedVehicleChargeTemplate,
    chargePointConnectedVehicleBidiEnabled,
    // vehicle data
    vehicleList,
    chargePointConnectedVehicleConfig,
    vehicleInfo,
    vehicleConnectionState,
    vehicleSocType,
    vehicleSocValue,
    vehicleSocManualValue,
    vehicleForceSocUpdate,
    chargePointConnectedVehicleSoc,
    vehicleActivePlan,
    vehicleChargeTarget,
    addScheduledChargingPlanForChargePoint,
    removeScheduledChargingPlanForChargePoint,
    vehicleScheduledChargingPlans,
    vehicleScheduledChargingPlanActive,
    vehicleScheduledChargingPlanEtActive,
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
    vehicleScheduledChargingPlanPhases,
    vehicleScheduledChargingPlanPhasesPv,
    vehicleScheduledChargingPlanBidiEnabled,
    vehicleScheduledChargingPlanBidiPower,
    vehicleScheduledChargingPlanDcPower,
    vehicleTimeChargingPlans,
    vehicleTimeChargingPlanName,
    addTimeChargingPlanForChargePoint,
    removeTimeChargingPlanForChargePoint,
    vehicleTimeChargingPlanActive,
    vehicleTimeChargingPlanStartTime,
    vehicleTimeChargingPlanEndTime,
    vehicleTimeChargingPlanCurrent,
    vehicleTimeChargingPlanLimitSelected,
    vehicleTimeChargingPlanSocLimit,
    vehicleTimeChargingPlanEnergyAmount,
    vehicleTimeChargingPlanFrequencySelected,
    vehicleTimeChargingPlanOnceDateStart,
    vehicleTimeChargingPlanOnceDateEnd,
    vehicleTimeChargingPlanPhases,
    vehicleTimeChargingPlanWeeklyDays,
    vehicleTimeChargingPlanDcPower,
    chargePointConnectedVehicleSocType,
    chargePointConnectedVehicleSocManual,
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
    getAllCounterIds,
    getSecondaryCounterIds,
    getComponentName,
    getCounterPower,
    counterDailyImported,
    counterDailyExported,
    // Home data
    getHomePower,
    homeDailyYield,
    // PV data
    getPvConfigured,
    getPvPower,
    pvDailyExported,
    // Chart data
    chartData,
    // electricity tariff provider
    etProviderConfigured,
    etPrices,
  };
});
