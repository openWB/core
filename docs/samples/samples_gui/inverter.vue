<template>
	<div class="device-sample-inverter">
		<openwb-base-heading>
			Einstellungen für Sample Wechselrichter
			<span class="small">(Modul: {{ $options.name }})</span>
		</openwb-base-heading>
	</div>
</template>

<script>
export default {
	name: "DeviceSampleInverter",
	emits: ["update:configuration"],
	props: {
		configuration: { type: Object, required: true },
		deviceId: { type: Number, default: undefined },
		componentId: { type: Number, required: true },
	},
	methods: {
		updateConfiguration(event, path = undefined) {
			this.$emit("update:configuration", { value: event, object: path });
		},
	},
};
</script>
