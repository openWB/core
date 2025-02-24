<script>
import FlowCard from "@/components/Dashboard/FlowCard.vue";

export default {
  name: "EnergyFlowView",
  components: {
    FlowCard,
  },
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
};
</script>

<template>
  <FlowCard :changes-locked="changesLocked" />
</template>

<style scoped></style>
