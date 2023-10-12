// this is our model. It contains all values required by the different parts of the front end
// it is constantly updated when new MQTT events come in

import { reactive } from 'vue'

export const topicForest: Node[] = reactive([])
export class Node {
	name: string
	children: Node[]
	count: number
	lastValue: string
	constructor(
		name: string,
		children: Node[],
		count: number,
		lastValue: string,
	) {
		this.name = name
		this.children = children
		this.count = count
		this.lastValue = lastValue
	}
	insert(topic: string[], message: string) {
		if (topic.length) {
			const subtopic = topic.splice(1)
			if (topic[0] == this.name) {
				if (subtopic.length) {
					// no leaf node
					let found = false
					this.children.forEach((child) => {
						if (child.name == subtopic[0]) {
							child.insert(subtopic, message)
							found = true
						}
					})
					if (!found) {
						const n = new Node(subtopic[0], [], 0, '')
						n.insert(subtopic, message)
						this.children.push(n)
					}
				} else {
					// this is a leaf
					this.count = this.count + 1
					this.lastValue = message
				}
			}
		}
	}
}
export function add(topic: string, message: string) {
	const elements = topic.split('/')
	if (elements.length) {
		let found = false
		topicForest.forEach((tree) => {
			if (tree.name == elements[0]) {
				tree.insert(elements, message)
				found = true
			}
		})
		if (!found) {
			const n = new Node(elements[0], [], 0, '')
			topicForest.push(n)
			n.insert(elements, message)
		}
	}
}
