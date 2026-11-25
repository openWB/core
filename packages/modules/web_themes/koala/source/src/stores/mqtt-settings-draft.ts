import { computed, reactive, watch } from 'vue';
import type { MqttSettingsTransport, MqttStore } from './mqtt-store';
import type {
  ChargeTemplateConfiguration,
  SystemCommandEvent,
  TopicList,
} from './mqtt-store-model';

const clone = <T>(value: T): T =>
  value === undefined ? value : JSON.parse(JSON.stringify(value));

function setPath(value: unknown, path: string, replacement: unknown): unknown {
  if (!path) return clone(replacement);
  const result = (clone(value) ?? {}) as Record<string, unknown>;
  const keys = path.split('.');
  let target = result;
  for (const key of keys.slice(0, -1)) {
    target[key] ??= {};
    target = target[key] as Record<string, unknown>;
  }
  target[keys.at(-1)!] = clone(replacement);
  return result;
}

const planKinds = {
  TimeCharging: { path: 'time_charging.plans', field: 'time_charging' },
  Schedule: {
    path: 'chargemode.scheduled_charging.plans',
    field: 'scheduled_charging',
  },
} as const;
type PlanKind = keyof typeof planKinds;

function getPlans(template: ChargeTemplateConfiguration, kind: PlanKind) {
  return kind === 'TimeCharging'
    ? template.time_charging.plans
    : template.chargemode.scheduled_charging.plans;
}

// All edits, including nested plan dialogs, stay in this private overlay. Values
// outside edited paths continue to follow MQTT while the dialog is open.
export function createMqttSettingsDraft(source: MqttStore) {
  const edits = reactive(new Map<string, Map<string, unknown>>());
  const pending = reactive(new Map<string, unknown>());
  let nextPlanId = -1;

  const topics = computed<TopicList>(() => {
    const result = { ...source.topics };
    for (const [topic, id] of pending) {
      const point = topic.match(
        /^openWB\/chargepoint\/(\d+)\/config\/ev$/,
      )?.[1];
      if (!point) continue;
      const info = source.topics[
        `openWB/chargepoint/${point}/get/connected_vehicle/info`
      ] as { id: number } | undefined;
      if (info?.id === id) continue;
      const templateId = source.getValue(
        `openWB/vehicle/${id}/charge_template`,
      );
      result[`openWB/chargepoint/${point}/set/charge_template`] =
        templateId === undefined
          ? undefined
          : source.getValue(
              `openWB/vehicle/template/charge_template/${templateId}`,
            );
      result[`openWB/chargepoint/${point}/get/connected_vehicle/config`] = {
        ...(source.topics[
          `openWB/chargepoint/${point}/get/connected_vehicle/config`
        ] as object),
        charge_template: templateId,
        ev_template: source.getValue(`openWB/vehicle/${id}/ev_template`),
      };
    }
    for (const [topic, paths] of edits) {
      let value = result[topic];
      for (const [path, replacement] of paths)
        value = setPath(value, path, replacement);
      result[topic] = value;
    }
    return result;
  });

  function edit(topic: string, payload: unknown, path = '', publish = false) {
    if (!(topic in topics.value)) return;
    const paths = edits.get(topic) ?? new Map<string, unknown>();
    // Editing a whole object supersedes earlier edits to its children.
    for (const key of paths.keys()) {
      if (!path || key === path || key.startsWith(`${path}.`))
        paths.delete(key);
    }
    paths.set(path, clone(payload));
    edits.set(topic, paths);
    if (publish) pending.set(topic, undefined);
  }

  function selectVehicle(topic: string) {
    const point = topic.match(/^openWB\/chargepoint\/(\d+)\/config\/ev$/)?.[1];
    if (!point) return;
    const templateTopic = `openWB/chargepoint/${point}/set/charge_template`;
    edits.delete(templateTopic);
    pending.delete(templateTopic);
  }

  function command(event: SystemCommandEvent) {
    const match = event.command.match(
      /^(add|remove)ChargeTemplate(TimeCharging|Schedule)Plan$/,
    );
    if (!match)
      throw new Error(
        'Dieser Befehl kann nicht als Entwurf bearbeitet werden.',
      );
    const kind = match[2] as PlanKind;
    const data = event.data as { chargepoint: number; plan?: number };
    const topic = `openWB/chargepoint/${data.chargepoint}/set/charge_template`;
    const template = topics.value[topic] as ChargeTemplateConfiguration;
    if (!template) return;
    const plans = clone(getPlans(template, kind));
    if (match[1] === 'remove') {
      edit(
        topic,
        plans.filter((plan) => plan.id !== data.plan),
        planKinds[kind].path,
        true,
      );
      return;
    }
    const date = new Date().toLocaleDateString('sv-SE');
    const common = {
      id: nextPlanId--,
      active: true,
      dc_current: 145,
      frequency: {
        selected: 'daily',
        once: kind === 'TimeCharging' ? [date, date] : date,
        weekly: Array(7).fill(false),
      },
    };
    const plan =
      kind === 'TimeCharging'
        ? {
            ...common,
            name: 'neuer Zeitladen-Plan',
            current: 16,
            time: ['06:00', '07:00'],
            limit: { selected: 'none', amount: 50000, soc: 50 },
            min_bat_soc: null,
            phases_to_use: 1,
          }
        : {
            ...common,
            name: 'neuer Zielladen-Plan',
            current: 14,
            time: '07:00',
            limit: {
              selected: 'amount',
              amount: 1000,
              soc_limit: 90,
              soc_scheduled: 80,
            },
            bidi_charging_enabled: false,
            bidi_power: 10000,
            et_active: false,
            phases_to_use: 0,
            phases_to_use_pv: 0,
          };
    edit(topic, [...plans, plan], planKinds[kind].path, true);
  }

  const transport: MqttSettingsTransport = {
    topics,
    subscribe(topic, defaultValue) {
      if (!source.subscriptions[topic]) source.subscribe(topic, defaultValue);
    },
    updateTopic(topic, payload, path, publish) {
      edit(topic, payload, path, publish);
    },
    async publish(topic, payload) {
      pending.set(topic, clone(payload));
      if (topic.endsWith('/config/ev')) selectVehicle(topic);
      return true;
    },
    command,
  };

  function reset() {
    pending.clear();
    edits.clear();
    nextPlanId = -1;
  }

  function waitFor<T>(
    read: () => T,
    accept: (value: T) => boolean,
  ): Promise<T> {
    if (accept(read())) return Promise.resolve(read());
    return new Promise((resolve, reject) => {
      const stop = watch(
        read,
        (value) => {
          if (accept(value)) {
            clearTimeout(timer);
            stop();
            resolve(value);
          }
        },
        { deep: true },
      );
      const timer = setTimeout(() => {
        stop();
        reject(
          new Error(
            'Die Rückmeldung der openWB ist ausgeblieben. Bitte erneut versuchen.',
          ),
        );
      }, 10000);
    });
  }

  async function publish(topic: string, value: unknown) {
    const original = clone(source.topics[topic]);
    if (!(await source.sendTopicToBroker(topic, value, original)))
      throw new Error(
        'Die Änderungen konnten nicht vollständig übernommen werden.',
      );
    source.updateTopic(topic, clone(value), undefined, false);
  }

  async function apply() {
    // A vehicle assignment must reach the backend before applying its settings.
    for (const [topic, value] of pending) {
      const point = topic.match(
        /^openWB\/chargepoint\/(\d+)\/config\/ev$/,
      )?.[1];
      if (!point) continue;
      const infoTopic = `openWB/chargepoint/${point}/get/connected_vehicle/info`;
      const templateTopic = `openWB/chargepoint/${point}/set/charge_template`;
      source.getValue(infoTopic);
      source.getValue(templateTopic);
      const selectedTemplate = await waitFor(
        () =>
          topics.value[templateTopic] as
            ChargeTemplateConfiguration | undefined,
        (template) => template !== undefined,
      );
      await publish(topic, value);
      await waitFor(
        () => source.topics[infoTopic] as { id: number } | undefined,
        (info) => info?.id === value,
      );
      await waitFor(
        () =>
          source.topics[templateTopic] as
            ChargeTemplateConfiguration | undefined,
        (template) => template?.id === selectedTemplate!.id,
      );
      pending.delete(topic);
    }
    for (const [topic, payload] of pending) {
      let value = clone(payload === undefined ? topics.value[topic] : payload);
      if (topic.endsWith('/set/charge_template')) {
        const template = value as ChargeTemplateConfiguration;
        // Let the existing backend commands allocate globally unique plan IDs.
        // No command is sent when the user discards the draft.
        for (const kind of Object.keys(planKinds) as PlanKind[]) {
          for (const plan of getPlans(template, kind)) {
            if (plan.id >= 0) continue;
            const previous = new Set(
              getPlans(
                source.topics[topic] as ChargeTemplateConfiguration,
                kind,
              ).map((p) => p.id),
            );
            source.sendSystemCommand(`addChargeTemplate${kind}Plan`, {
              template: template.id,
              chargepoint: Number(topic.split('/')[2]),
              changed_in_theme: true,
            });
            const updated = await waitFor(
              () => source.topics[topic] as ChargeTemplateConfiguration,
              (current) =>
                getPlans(current, kind).some((p) => !previous.has(p.id)),
            );
            plan.id = getPlans(updated, kind).find(
              (p) => !previous.has(p.id),
            )!.id;
            // Preserve the allocated ID if a later publish fails and is retried.
            edit(
              topic,
              clone(getPlans(template, kind)),
              planKinds[kind].path,
              true,
            );
          }
        }
        value = template;
      }
      await publish(topic, value);
      pending.delete(topic);
      edits.delete(topic);
    }
    reset();
  }

  return { transport, reset, apply };
}
