<template>
  <LineGroup
    v-for="cat in categoryDefs"
    :key="cat.key"
    :label="cat.label"
    :color="getCssColor(cat.colorVar)"
    :mode="categoryMode[cat.key]"
    :items="categories[cat.key].individual"
    :is-visible="(id) => isInstanceVisible(cat.key, id)"
    :set-visible="(id, visible) => setInstanceVisible(cat.key, id, visible)"
    @update:mode="categoryMode[cat.key] = $event"
  />
</template>

<script setup lang="ts">
import { useChartSettings, type CategoryDef } from '@/composables/useChartSettings'
import { getCssColor } from '@/utils/color'
import LineGroup from './LineGroup.vue'

defineProps<{ categoryDefs: CategoryDef[] }>()

const { categoryMode, categories, isInstanceVisible, setInstanceVisible } = useChartSettings()
</script>
