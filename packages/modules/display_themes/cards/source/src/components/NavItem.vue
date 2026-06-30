<script>
export default {
  name: "NavItem",
  props: {
    to: {
      type: Object,
      required: true,
    },
  },
};
</script>

<template>
  <i-nav-item
    :to="to"
    active-class="-active"
    class="_border _text-align:center"
  >
    <slot />
  </i-nav-item>
</template>

<style scoped>
.nav-item {
  margin-bottom: var(--spacing) !important;
  border-radius: var(--border-radius);
  border-color: var(--color--light);
}

.nav-item.-active {
  background-color: var(--color--dark-40);
  color: var(--color--light);
}
</style>
