<template>
  <WBWidget :variable-width="true"  >
    <template v-slot:title>
      Setup
    </template>
    <h3>to be done</h3>
    <div v-for="[key, value]  of system.components">
    <h3> {{ key }} </h3>
    <table class="table">
      <thead>
        <td>Modul</td><td>Beschreibung</td>
      </thead>
      <tbody>
      <tr v-for="item of value">
        <th>{{ item.name }} </th>
        <th>{{ item.text }}</th>
      </tr>
    </tbody>
    </table>
  </div>
  </WBWidget>

  </template>

<script setup lang="ts">
// import { computed, ref, watch, watchEffect } from 'vue'
import WBWidget from '@/components/shared/WBWidget.vue'
import { system } from './model'
</script>

<style scoped>
</style>
