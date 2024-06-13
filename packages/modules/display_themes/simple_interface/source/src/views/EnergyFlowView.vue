<script>
import FlowCard from "@/components/DashBoard/FlowCard.vue";

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
  <FlowCard />
</template>

<style scoped></style>
