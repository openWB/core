<template>
  <div class="backup-cloud-sample">
    <openwb-base-heading>
      Einstellungen für Sample-Backup Cloud
    </openwb-base-heading>
  </div>
</template>

<script>
import BackupCloudConfigMixin from "../BackupCloudConfigMixin.vue";

export default {
  name: "BackupCloudSample",
  mixins: [BackupCloudConfigMixin],
  data() {
    return {};
  },
};
</script>
