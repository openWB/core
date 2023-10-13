<template>
  <div>
    <button class="btn btn-outline-secondary btn-sm" id="calendarButton" @click="$emit('toggleMonthlyView')">
      <span class="fa fa-calendar-alt px-0"></span>
    </button>
    <button
      class="btn btn-outline-secondary btn-sm"
      id="energyLeftButton"
      :class="{ disabled: !showLeftButton }"
      @click="$emit('shiftLeft')"
    >
      <span class="fa fa-chevron-circle-left px-0"></span>
    </button>
    <button
      class="btn btn-outline-secondary btn-sm"
      id="energyRightButton"
      :class="{ disabled: !showRightButton }"
      @click="$emit('shiftRight')"
    >
      <span class="fa fa-chevron-circle-right px-0"></span>
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  showLeftButton: boolean
  showRightButton: boolean
}>()
</script>

<style></style>
