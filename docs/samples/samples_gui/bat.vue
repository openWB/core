<template>
	<div class="device-sample-bat">
		<openwb-base-heading>
			Einstellungen für Sample Batteriespeicher
			<span class="small">(Modul: {{ $options.name }})</span>
		</openwb-base-heading>
	</div>
</template>

<script>
export default {
	name: "DeviceSampleBat",
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
