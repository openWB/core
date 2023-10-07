import { reactive } from 'vue'
export class System {
	components  = new Map<string, SystemComponent[]> 
}

export const system: System = reactive(new System())

export type RawComponent = {
value: string,
text: string,
component: [{value: string, text: string}]
}
export type SystemComponent = {
	name: string,
	text: string
}
