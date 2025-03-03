export const useBatteryModes = () => {
  const batteryModes = [
    {
      value: 'ev_mode',
      label: 'Fahrzeuge',
      color: 'primary',
      icon: 'directions_car',
      tooltip: 'Fahrzeuge',
    },
    {
      value: 'bat_mode',
      label: 'Speicher',
      color: 'primary',
      icon: 'battery_charging_full',
      tooltip: 'Speicher',
    },
    {
      value: 'min_soc_bat_mode',
      label: 'Mindest-SoC',
      color: 'primary',
      icon: 'battery_4_bar',
      tooltip: 'Mindest-SoC des Speichers',
    },
  ];

  return {
    batteryModes,
  };
};
