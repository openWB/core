import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, defineStore, disposePinia } from 'pinia';
import { reactive } from 'vue';
import { createMqttSettingsDraft } from './mqtt-settings-draft';
import { mqttStoreSetup } from './mqtt-store';
import type { MqttStore } from './mqtt-store';
import type {
  ChargeTemplateConfiguration,
  TopicList,
} from './mqtt-store-model';

vi.mock('quasar', () => ({
  useQuasar: () => ({ cookies: { has: () => false } }),
}));

const topic = 'openWB/chargepoint/1/set/charge_template';
const lockTopic = 'openWB/chargepoint/1/set/manual_lock';
const infoTopic = 'openWB/chargepoint/1/get/connected_vehicle/info';

function fixture() {
  const topics = reactive<TopicList>({
    [topic]: {
      id: 0,
      name: 'Template',
      chargemode: {
        selected: 'instant_charging',
        instant_charging: { current: 16, phases_to_use: 3 },
        scheduled_charging: { plans: [] },
      },
      time_charging: { active: false, plans: [] },
    },
    [lockTopic]: false,
    [infoTopic]: { id: 0, name: 'Vehicle 0' },
  });
  const source = {
    topics,
    subscriptions: {},
    getValue: vi.fn((key: string) => topics[key]),
    subscribe: vi.fn(),
    sendTopicToBroker: vi.fn<
      (topic: string, payload: unknown, original?: unknown) => Promise<boolean>
    >(async () => true),
    sendSystemCommand: vi.fn(),
    updateTopic: vi.fn((key: string, value: unknown) => {
      topics[key] = value;
    }),
  };
  const draft = createMqttSettingsDraft(source as unknown as MqttStore);
  const pinia = createPinia();
  const store = defineStore('mqtt', () => mqttStoreSetup(draft.transport))(
    pinia,
  );
  return { source, draft, store, pinia };
}

describe('isolated charge point settings', () => {
  let f: ReturnType<typeof fixture>;
  beforeEach(() => {
    vi.stubGlobal('location', {
      protocol: 'http:',
      hostname: 'localhost',
      port: '',
    });
    f = fixture();
  });
  afterEach(() => {
    disposePinia(f.pinia);
    vi.unstubAllGlobals();
  });

  it('keeps lock, mode and nested settings local and discards everything without publishing', () => {
    f.store.chargePointManualLock(1).value = true;
    f.store.chargePointConnectedVehicleChargeMode(1).value = 'pv_charging';
    f.store.chargePointConnectedVehicleInstantChargeCurrent(1).value = 20;
    expect(f.store.chargePointManualLock(1).value).toBe(true);
    expect(f.store.chargePointConnectedVehicleChargeMode(1).value).toBe(
      'pv_charging',
    );
    expect(f.source.topics[lockTopic]).toBe(false);
    expect(
      (f.source.topics[topic] as ChargeTemplateConfiguration).chargemode
        .selected,
    ).toBe('instant_charging');
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
    f.draft.reset();
    expect(f.store.chargePointManualLock(1).value).toBe(false);
    expect(
      f.store.chargePointConnectedVehicleInstantChargeCurrent(1).value,
    ).toBe(16);
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
  });

  it('applies edited paths once while preserving unrelated concurrent MQTT updates', async () => {
    f.store.chargePointConnectedVehicleInstantChargeCurrent(1).value = 20;
    f.store.chargePointConnectedVehicleInstantChargeCurrent(1).value = 24;
    (f.source.topics[topic] as ChargeTemplateConfiguration).name =
      'Updated remotely';
    (
      f.source.topics[topic] as ChargeTemplateConfiguration
    ).chargemode.instant_charging.phases_to_use = 1;
    await f.draft.apply();
    expect(f.source.sendTopicToBroker).toHaveBeenCalledTimes(1);
    const saved = f.source.sendTopicToBroker.mock.calls[0] as unknown as [
      string,
      ChargeTemplateConfiguration,
    ];
    expect(saved[0]).toBe(topic);
    expect(saved[1].name).toBe('Updated remotely');
    expect(saved[1].chargemode.instant_charging).toMatchObject({
      current: 24,
      phases_to_use: 1,
    });
  });

  it('leaves failed edits available for retry and does not report a successful apply', async () => {
    f.store.chargePointManualLock(1).value = true;
    f.source.sendTopicToBroker.mockResolvedValueOnce(false);
    await expect(f.draft.apply()).rejects.toThrow('nicht vollständig');
    expect(f.source.topics[lockTopic]).toBe(false);
    expect(f.store.chargePointManualLock(1).value).toBe(true);
    await f.draft.apply();
    expect(f.source.topics[lockTopic]).toBe(true);
  });

  it('previews plan creation, editing and deletion without sending commands', () => {
    f.store.addTimeChargingPlanForChargePoint(1);
    const plan = f.store.vehicleTimeChargingPlans(1)[0];
    expect(plan.id).toBeLessThan(0);
    f.store.vehicleTimeChargingPlanName(1, plan.id).value = 'Draft overnight';
    expect(f.store.vehicleTimeChargingPlans(1)[0].name).toBe('Draft overnight');
    f.store.removeTimeChargingPlanForChargePoint(1, plan.id);
    expect(f.store.vehicleTimeChargingPlans(1)).toEqual([]);
    f.draft.reset();
    expect(f.source.sendSystemCommand).not.toHaveBeenCalled();
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
  });

  it('allocates real plan IDs only when confirmed and retains edited plan values', async () => {
    f.store.addTimeChargingPlanForChargePoint(1);
    const plan = f.store.vehicleTimeChargingPlans(1)[0];
    f.store.vehicleTimeChargingPlanName(1, plan.id).value = 'Overnight';
    f.source.sendSystemCommand.mockImplementation(() => {
      (
        f.source.topics[topic] as ChargeTemplateConfiguration
      ).time_charging.plans.push({ ...plan, id: 42 });
    });
    await f.draft.apply();
    expect(f.source.sendSystemCommand).toHaveBeenCalledTimes(1);
    expect(
      (f.source.topics[topic] as ChargeTemplateConfiguration).time_charging
        .plans[0],
    ).toMatchObject({ id: 42, name: 'Overnight' });
  });

  it('keeps vehicle selection local, follows its asynchronously loaded template and discards it', () => {
    f.store.chargePointConnectedVehicleInfo(1).value = {
      id: 2,
      name: 'Vehicle 2',
    };
    expect(f.store.chargePointConnectedVehicleInfo(1).value?.id).toBe(2);
    f.source.topics['openWB/vehicle/2/charge_template'] = 7;
    f.source.topics['openWB/vehicle/template/charge_template/7'] = {
      ...(f.source.topics[topic] as object),
      id: 7,
      name: 'Vehicle 2 template',
    };
    expect(f.store.chargePointConnectedVehicleChargeTemplate(1).value?.id).toBe(
      7,
    );
    expect(f.source.topics[infoTopic]).toEqual({ id: 0, name: 'Vehicle 0' });
    f.draft.reset();
    expect(f.store.chargePointConnectedVehicleInfo(1).value?.id).toBe(0);
    expect(f.store.chargePointConnectedVehicleChargeTemplate(1).value?.id).toBe(
      0,
    );
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
  });

  it('applies a selected vehicle before its edited template', async () => {
    const vehicleTopic = 'openWB/chargepoint/1/config/ev';
    f.source.topics['openWB/vehicle/2/charge_template'] = 7;
    const template = JSON.parse(JSON.stringify(f.source.topics[topic]));
    template.id = 7;
    f.source.topics['openWB/vehicle/template/charge_template/7'] = template;
    f.store.chargePointConnectedVehicleInfo(1).value = {
      id: 2,
      name: 'Vehicle 2',
    };
    f.store.chargePointConnectedVehicleInstantChargeCurrent(1).value = 24;
    f.source.sendTopicToBroker.mockImplementation(async (key) => {
      if (key === vehicleTopic) {
        f.source.topics[infoTopic] = { id: 2, name: 'Vehicle 2' };
        f.source.topics[topic] = JSON.parse(JSON.stringify(template));
      }
      return true;
    });
    await f.draft.apply();
    expect(f.source.sendTopicToBroker.mock.calls.map(([key]) => key)).toEqual([
      vehicleTopic,
      topic,
    ]);
    expect((f.source.topics[topic] as ChargeTemplateConfiguration).id).toBe(7);
    expect(
      (f.source.topics[topic] as ChargeTemplateConfiguration).chargemode
        .instant_charging.current,
    ).toBe(24);
  });

  it('stages scheduled plans and allocates their IDs through the matching backend command', async () => {
    f.store.addScheduledChargingPlanForChargePoint(1);
    const plan = f.store.vehicleScheduledChargingPlans(1)[0];
    expect(plan.id).toBeLessThan(0);
    expect(f.source.sendSystemCommand).not.toHaveBeenCalled();
    f.source.sendSystemCommand.mockImplementation(() => {
      (
        f.source.topics[topic] as ChargeTemplateConfiguration
      ).chargemode.scheduled_charging.plans.push({ ...plan, id: 43 });
    });
    await f.draft.apply();
    expect(f.source.sendSystemCommand).toHaveBeenCalledWith(
      'addChargeTemplateSchedulePlan',
      { template: 0, chargepoint: 1, changed_in_theme: true },
    );
    expect(
      (f.source.topics[topic] as ChargeTemplateConfiguration).chargemode
        .scheduled_charging.plans[0].id,
    ).toBe(43);
  });

  it('discards consumer modes and schedules without changing the live consumer', () => {
    const key = 'openWB/consumer/5/usage';
    f.source.topics[key] = {
      type: 'continuous',
      chargemode: 'pv_charging',
      reset_chargemode: {
        active: false,
        frequency: { selected: 'daily', weekly: Array(7).fill(false) },
        time: '07:00',
      },
    };
    const original = JSON.stringify(f.source.topics[key]);
    f.store.consumerMode(5).value = 'stop';
    f.store.consumerResetEnabled(5).value = true;
    f.store.consumerResetTrigger(5).value = 'weekly';
    f.store.consumerResetWeeklyDays(5).value = [
      true,
      false,
      true,
      false,
      false,
      false,
      false,
    ];
    expect(f.store.consumerMode(5).value).toBe('stop');
    expect(JSON.stringify(f.source.topics[key])).toBe(original);
    f.draft.reset();
    expect(f.store.consumerMode(5).value).toBe('pv_charging');
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
  });

  it('applies a consumer schedule in one publication and preserves unrelated live updates', async () => {
    const key = 'openWB/consumer/5/usage';
    f.source.topics[key] = { type: 'continuous', chargemode: 'pv_charging' };
    f.store.consumerResetEnabled(5).value = true;
    f.store.consumerResetTime(5).value = '08:30';
    f.store.consumerResetTrigger(5).value = 'once';
    f.store.consumerResetOnceDate(5).value = '2026-12-01';
    f.store.consumerResetTargetMode(5).value = 'stop';
    (f.source.topics[key] as { chargemode: string }).chargemode =
      'instant_charging';
    await f.draft.apply();
    expect(f.source.sendTopicToBroker).toHaveBeenCalledTimes(1);
    expect(f.source.sendTopicToBroker).toHaveBeenCalledWith(
      key,
      {
        type: 'continuous',
        chargemode: 'instant_charging',
        reset_chargemode: {
          active: true,
          time: '08:30',
          frequency: { selected: 'once', once: '2026-12-01' },
          chargemode: 'stop',
        },
      },
      expect.anything(),
    );
  });

  it('keeps battery priority and SoC bounds local until confirmation', async () => {
    const base = 'openWB/general/chargemode_config/bat/';
    f.source.topics[base + 'mode'] = 'ev_mode';
    f.source.topics[base + 'min_soc'] = 20;
    f.source.topics[base + 'max_soc'] = 80;
    f.store.batteryMode().value = 'min_soc_bat_mode';
    f.store.batteryChargePriorityRange = { min: 30, max: 90 };
    expect(f.source.topics[base + 'min_soc']).toBe(20);
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
    f.draft.reset();
    expect(f.store.batteryChargePriorityRange).toEqual({ min: 20, max: 80 });
    f.store.batteryMode().value = 'min_soc_bat_mode';
    f.store.batteryChargePriorityRange = { min: 40, max: 95 };
    await f.draft.apply();
    expect(f.source.topics[base + 'min_soc']).toBe(40);
    expect(f.source.topics[base + 'max_soc']).toBe(95);
    expect(f.source.sendTopicToBroker).toHaveBeenCalledTimes(3);
  });

  it('queues a manual vehicle SoC only until apply and uses the existing command topic', async () => {
    const key = 'openWB/vehicle/1/soc_module/calculated_soc_state/manual_soc';
    f.store.vehicleSocManualValue(1).value = 61;
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
    f.draft.reset();
    await f.draft.apply();
    expect(f.source.sendTopicToBroker).not.toHaveBeenCalled();
    f.store.vehicleSocManualValue(1).value = 72;
    await f.draft.apply();
    expect(f.source.sendTopicToBroker).toHaveBeenCalledWith(key, 72, undefined);
  });
});
