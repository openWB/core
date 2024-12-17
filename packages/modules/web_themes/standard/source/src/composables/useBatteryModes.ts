export const useBatteryModes = () => {
  const batteryModes = [
    {
      value: 'ev_mode',
      label: 'Auto',
      color: 'primary',
      icon: 'directions_car',
      tooltip: 'Auto',
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
      label: 'SoC',
      color: 'primary',
      icon: 'battery_charging_full',
      tooltip: 'Minimum Speicher SoC',
    },
  ];

  return {
    batteryModes,
  };
};
