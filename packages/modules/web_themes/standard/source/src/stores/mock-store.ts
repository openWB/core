import { defineStore } from 'pinia';

export const useCounterStore = defineStore('power', {
  state: () => ({
    power: {
      ChargePoint: {
        NumberOfChargePoints: 2,
        Power: 11,
        Current: 16,
        Charged_kWh: 25.3,
        Kilometer_Current: 150,
        Kilometer_Target: 250,
        Mode: {
          immediate: true,
          PV_target_charging: false,
          standby: false,
          stop: false,
        },
        Message: 'No car plugged in',
        Vehicle: 'Tesla Model 3',
        Connected: false,
        Locked: true,
        Priority: 'High',
        Scheduled_Charging: '2024-09-30 23:00',
        CurrentSoC: 45,
        TargetSoC: 80,
        Immediate: {
          Current: 16,
          Limit: {
            Keine: false,
            'EV-SoC': true,
            Energy: false,
          },
          MaximumSoC: 80,
        },
        PV: {
          MinimumConstantCurrent: 8,
          MinimumSoC: 20,
          MinimumSoCCurrent: 12,
          SoCLimit: 90,
          FeedInLimit: 5,
        },
        TargetCharging: {
          Description: 'Scheduled charging for energy optimization',
          TimeActive: 4,
          TargetTime: '2024-09-30 06:00',
          ChargingCurrent: 10,
          Target: 80,
          TargetEnergy: 30,
          Repetitions: 1,
        },
      },
      EnergyFlowDiagram: {
        EVUPower: 3000,
        PVPower: 5000,
        HousePower: 3500,
        StoragePower: 2000,
        ChargingPoints: {
          LP1Power: 3500,
          LP2Power: 0,
          LP3Power: 0,
        },
      },
      GraphData: {
        EVU: 3000,
        HousePower: 3500,
        LPTotalPower: 3500,
        LP1Power: 3500,
        LP2Power: 0,
        LP3Power: 0,
        PVTotalPower: 5000,
        SpeicherTotalPower: 2000,
        SpeicherSoC: 60,
      },
      TextOverviewData: {
        EnergyProduction: {
          PVEnergyDayTotal: 25.5,
          SpeicherDayTotal: 10.3,
          SpeicherSoC: 60,
          EVUDayTotal: 5.0,
        },
        EnergyConsumption: {
          HouseDailyTotal: 12.8,
          SpeicherDailyTotal: 7.2,
          EVUDailyTotal: 5.0,
          ChargePointsDailyTotal: 20.3,
        },
      },
      HouseBatteryStorage: {
        SoC: 60,
        Charged_kWh: 10.3,
        Discharged_kWh: 7.2,
      },
      ExcessEnergy: {
        Car: 12.5,
        BatteryStorage: 5.0,
      },
    },
  }),
  getters: {
    //
  },
  actions: {
    //
  },
});
