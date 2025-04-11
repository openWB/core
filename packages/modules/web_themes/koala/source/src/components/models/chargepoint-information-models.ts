import { BaseRow } from './base-table-models';

export interface ChargePointRow extends BaseRow {
  id: number;
  name: string | undefined;
  vehicle: string;
  plugged: string;
  mode: string | undefined;
  soc: string;
  power: string | number | object | undefined;
  charged: string | number | object | undefined;
}
