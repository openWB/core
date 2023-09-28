<template>
	<div class="backup-cloud-sample">
		<openwb-base-heading>
			Einstellungen für Sample-Backup Cloud
			<span class="small">(Modul: {{ $options.name }})</span>
		</openwb-base-heading>
	</div>
</template>

<script>
export default {
	name: "BackupCloudSample",
	emits: ["update:configuration"],
	props: {
		configuration: { type: Object, required: true },
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
