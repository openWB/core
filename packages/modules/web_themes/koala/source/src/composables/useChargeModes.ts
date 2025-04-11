export const useChargeModes = () => {
  const chargeModes = [
    { value: 'instant_charging', label: 'Sofort', color: 'negative' },
    { value: 'pv_charging', label: 'PV', color: 'positive' },
    { value: 'scheduled_charging', label: 'Ziel', color: 'primary' },
    { value: 'eco_charging', label: 'Eco', color: 'secondary' },
    { value: 'stop', label: 'Stop', color: 'light' },
  ];
  return {
    chargeModes,
  };
};
