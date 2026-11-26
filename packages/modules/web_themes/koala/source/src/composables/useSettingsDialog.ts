import {
  computed,
  onBeforeUnmount,
  provide,
  ref,
  watch,
  type WritableComputedRef,
} from 'vue';
import {
  createPinia,
  defineStore,
  disposePinia,
  getActivePinia,
  setActivePinia,
} from 'pinia';
import { useQuasar } from 'quasar';
import {
  mqttStoreSetup,
  settingsMqttStoreKey,
  useMqttStore,
  type MqttStore,
} from 'src/stores/mqtt-store';
import { createMqttSettingsDraft } from 'src/stores/mqtt-settings-draft';
import { useLocalDataStore } from 'src/stores/localData-store';

/** Shared dashboard edit session, including dismissal through Escape/backdrop. */
export function useSettingsDialog(
  isOpen: () => boolean,
  updateOpen: (value: boolean) => void,
  beforeApply?: () => void,
) {
  const source = useMqttStore();
  const localData = useLocalDataStore();
  const $q = useQuasar();
  const draft = createMqttSettingsDraft(source);
  const livePinia = getActivePinia();
  const draftPinia = createPinia();
  const draftStore = defineStore('mqtt', () => mqttStoreSetup(draft.transport))(
    draftPinia,
  );
  setActivePinia(livePinia);
  onBeforeUnmount(() => disposePinia(draftPinia));

  const dashboard = computed(() => localData.desktopOverview);
  const mqttStore = computed(() => (dashboard.value ? draftStore : source));
  provide(settingsMqttStoreKey, mqttStore);
  const saving = ref(false);
  const confirmClose = ref(false);
  const open = ref(isOpen());
  watch(isOpen, (value) => {
    if (value) draft.reset();
    if (!value) confirmClose.value = false;
    open.value = value;
  });
  const visible = computed({
    get: () => open.value,
    set: (value) => {
      if (!value && dashboard.value) {
        if (!saving.value) confirmClose.value = true;
        return;
      }
      open.value = value;
      updateOpen(value);
    },
  });

  // Keep writable store fields bound to the selected live/draft store.
  function field<T>(read: (store: MqttStore) => WritableComputedRef<T>) {
    return computed({
      get: () => read(mqttStore.value).value,
      set: (value: T) => {
        read(mqttStore.value).value = value;
      },
    });
  }

  function closeDialog() {
    confirmClose.value = false;
    open.value = false;
    updateOpen(false);
  }
  function discardChanges() {
    draft.reset();
    closeDialog();
  }
  async function applyChanges() {
    if (saving.value) return;
    saving.value = true;
    try {
      beforeApply?.();
      await draft.apply();
      closeDialog();
      $q.notify({ type: 'positive', message: 'Änderungen wurden übernommen.' });
    } catch (error) {
      $q.notify({
        type: 'negative',
        message:
          error instanceof Error
            ? error.message
            : 'Die Änderungen konnten nicht übernommen werden.',
      });
    } finally {
      saving.value = false;
    }
  }

  return {
    dashboard,
    mqttStore,
    field,
    visible,
    saving,
    confirmClose,
    discardChanges,
    applyChanges,
  };
}
