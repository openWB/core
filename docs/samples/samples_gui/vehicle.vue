<template>
	<div class="vehicle-soc-sample">
		<openwb-base-heading>
			Einstellungen für Sample SoC
			<span class="small">(Modul: {{ $options.name }})</span>
		</openwb-base-heading>
	</div>
</template>

<script>
export default {
	name: "VehicleSocSample",
	emits: ["update:configuration"],
	props: {
		configuration: { type: Object, required: true },
		vehicleId: { required: true },
	},
	data() {
		return {};
	},
	methods: {
		updateConfiguration(event, path = undefined) {
			this.$emit("update:configuration", { value: event, object: path });
		},
	},
};
</script>
