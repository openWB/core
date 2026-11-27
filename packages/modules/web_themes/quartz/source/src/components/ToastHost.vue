<template>
  <div
    class="pointer-events-none fixed right-4 bottom-4 left-4 z-[90] flex flex-col items-end gap-2"
    aria-live="assertive"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="panel pointer-events-auto flex max-w-[420px] items-start gap-3 border-error px-4 py-3"
      role="alert"
    >
      <p class="m-0 text-[14px] text-text">
        {{ toast.message }}
      </p>
      <button
        type="button"
        class="border-0 bg-transparent p-0 text-[16px] leading-none text-muted"
        aria-label="Meldung schließen"
        @click="dismissToast(toast.id)"
      >
        &times;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToasts } from '@/composables/useToasts'

const { toasts, dismissToast } = useToasts()
</script>
