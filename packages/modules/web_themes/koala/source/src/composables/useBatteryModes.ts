export const useBatteryModes = () => {
  const batteryModes = [
    {
      value: 'ev_mode',
      label: 'Verbraucher',
      color: 'primary',
      icons: ['directions_car', 'power'],
      tooltip: 'Verbraucher',
    },
    {
      value: 'bat_mode',
      label: 'Speicher',
      color: 'primary',
      icons: ['battery_charging_full'],
      tooltip: 'Speicher',
    },
    {
      value: 'min_soc_bat_mode',
      label: 'Nach SoC des Speichers',
      color: 'primary',
      icons: ['battery_4_bar'],
      tooltip: 'Nach SoC des Speichers',
    },
  ];

  return {
    batteryModes,
  };
};
