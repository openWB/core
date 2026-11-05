/** The 5 chargemode options exposed in the UI (the Chargemode enum has 2 more - time_charging,
 *  bidi_charging - neither surfaced here, same choice koala's own useChargeModes makes). Shared
 *  between ChargePointCard.vue and ConsumerCard.vue/ConsumerSettings.vue. */
export const chargeModes = [
  { value: 'instant_charging', label: 'Sofort' },
  { value: 'pv_charging', label: 'PV' },
  { value: 'scheduled_charging', label: 'Ziel' },
  { value: 'eco_charging', label: 'Eco' },
  { value: 'stop', label: 'Stop' },
]
