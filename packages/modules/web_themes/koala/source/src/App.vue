<template>
  <IconSprite />
  <router-view />
</template>

<script setup lang="ts">
import IconSprite from 'src/components/svgIcons/IconSprite.vue';

defineOptions({
  name: 'OpenwbKoalaWebTheme',
});
</script>
