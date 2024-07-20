<script>
export default {
  name: "DashBoardCard",
  props: {
    color: { type: String, required: true },
  },
};
</script>

<template>
  <i-card :color="color">
    <template #header>
      <i-container>
        <i-row>
          <i-column>
            <slot name="headerLeft" />
          </i-column>
          <i-column
            v-if="$slots.headerRight"
            class="_flex-grow:0 _text-align:right _white-space:nowrap"
          >
            <slot name="headerRight" />
          </i-column>
        </i-row>
      </i-container>
    </template>
    <slot />
  </i-card>
</template>

<style lang="scss" scoped>
@import "@inkline/inkline/css/variables";
@import "@inkline/inkline/css/mixins";

@include i-column {
  padding-left: 0;
  padding-right: 0;
}

.card {
  ----background: inherit !important;
  ----body--color: var(--contrast-color-for-dark-background) !important;
}
</style>
