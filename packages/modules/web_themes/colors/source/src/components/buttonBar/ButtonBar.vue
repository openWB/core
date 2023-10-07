/*
 * ButtonBar.vue
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// ButtonBar.vue // Display configuration buttons for all chargepoints
<template>
  <div class="row p-0 mt-0 mb-1 m-0">
    <div class="col p-0 m-0">
      <div class="container-fluid p-0 m-0">
        <div class="row p-0 m-0 d-flex justify-content-center">
          <BbChargeButton
            v-for="(cp, index) in chargePoints"
            :key="index"
            :chargepoint="cp"
            :chargePointCount="Object.values(chargePoints).length"
          ></BbChargeButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { chargePoints } from '../chargePointList/model'
import BbChargeButton from './BbChargeButton.vue'
</script>

<style></style>
