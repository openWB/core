import { type RawComponent, type SystemComponent, system } from './model'

export function processSystemMessages(topic: string, message: string) {
  // console.log (`SYSTEM: (${topic}):${message}`)

  if (topic.match(/^openWB\/system\/configurable\//i,)) {
    processConfigurableMessages(topic, message)
  } /*else if ( topic.match(/^openWB\/LegacySmarthome\/Devices\//i,)) {
    processSmarthomeDeviceMessages(topic,message)
  } else {
    // console.warn('Ignored Smarthome status message: ' + topic)
  } */
}

function processConfigurableMessages(topic: string, message: string) {
  if (topic.match(/^openWB\/system\/configurable\/devices_components$/i,)) {
    storeComponents(JSON.parse(message))
  }
}
function storeComponents(complist: [RawComponent]) {
  for (const group of complist) {
    for (const item of group.component) {
      if (!(system.components.has(item.value))) {
        system.components.set(item.value, [])
      }
      system.components.get(item.value)!.push({name: group.value, text: item.text})
    }
  }
}

function getIndex(topic: string): number | undefined {
  let index = 0
  try {
    var matches = topic.match(/(?:\/)([0-9]+)(?=\/)/g)
    if (matches) {
      index = +matches[0].replace(/[^0-9]+/g, '')
      return index
    } else {
      return undefined
    }
  } catch (e) {
    console.warn('Parser error in getIndex for topic ' + topic)
  }
}
