<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faLock as fasLock,
  faLockOpen as fasLockOpen,
  faDeleteLeft as fasDeleteLeft,
  faEraser as fasEraser,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasLock, fasLockOpen, fasDeleteLeft, fasEraser);

import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "LockNavItem",
  props: {},
  data() {
    return {
      mqttStore: useMqttStore(),
      modalPinEntryVisible: false,
      code: "",
    };
  },
  components: {
    FontAwesomeIcon,
  },
  computed: {
    changesLocked: {
      get() {
        return this.mqttStore.settings.changesLocked;
      },
      set(value) {
        this.mqttStore.settings.changesLocked = value;
      },
    },
    modalPinEntryColor() {
      return "warning";
    },
  },
  methods: {
    toggleChangesLock() {
      console.log("toggleChangesLock");
      if (this.changesLocked) {
        this.unlockChanges();
      } else {
        this.changesLocked = true;
      }
    },
    unlockChanges() {
      this.clearCode();
      this.modalPinEntryVisible = true;
    },
    abortUnlockChanges() {
      this.modalPinEntryVisible = false;
    },
    checkUnlockCode() {
      if (this.mqttStore.checkChangesLockCode(this.code)) {
        this.changesLocked = false;
        this.modalPinEntryVisible = false;
      } else {
        console.log("check unlock code failed!");
      }
    },
    addCodeDigit(digit) {
      if (this.code.length < 8) {
        this.code += digit;
      }
    },
    removeCodeDigit() {
      this.code = this.code.slice(0, -1);
    },
    clearCode() {
      this.code = "";
    },
  },
  mounted() {
    // init in locked state
    this.changesLocked = true;
  },
};
</script>

<template>
  <i-button
    v-if="mqttStore.getLockChanges"
    @click="toggleChangesLock()"
    class="_padding-left:0 _padding-right:0 _margin-bottom:1"
    size="lg"
    block
    :color="this.changesLocked ? 'danger' : 'success'"
  >
    <FontAwesomeIcon
      fixed-width
      :icon="this.changesLocked ? ['fas', 'fa-lock'] : ['fas', 'fa-lock-open']"
      :class="this.changesLocked ? '_color:danger-80' : '_color:success-80'"
    />
  </i-button>
  <!-- modals -->
  <Teleport to="body">
    <i-modal v-model="modalPinEntryVisible" :color="modalPinEntryColor">
      <template #header>
        Bitte den PIN zu Freigabe von Änderungen eingeben.
      </template>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column>
            <i-input
              v-model="code"
              placeholder="****"
              readonly
              size="lg"
              type="password"
              class="_text-align:center"
            />
          </i-column>
        </i-row>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('1')"
              >1</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('2')"
              >2</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('3')"
              >3</i-button
            >
          </i-column>
        </i-row>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('4')"
              >4</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('5')"
              >5</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('6')"
              >6</i-button
            >
          </i-column>
        </i-row>
        <i-row center class="_padding-bottom:1">
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('7')"
              >7</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('8')"
              >8</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('9')"
              >9</i-button
            >
          </i-column>
        </i-row>
        <i-row center>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="clearCode">
              <FontAwesomeIcon fixed-width :icon="['fas', 'fa-eraser']" />
            </i-button>
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="addCodeDigit('0')"
              >0</i-button
            >
          </i-column>
          <i-column class="_flex-grow:0">
            <i-button size="lg" class="pinButton" @click="removeCodeDigit">
              <FontAwesomeIcon fixed-width :icon="['fas', 'fa-delete-left']" />
            </i-button>
          </i-column>
        </i-row>
      </i-container>
      <template #footer>
        <i-container>
          <i-row>
            <!-- charge point data on left side -->
            <i-column>
              <i-button color="danger" @click="abortUnlockChanges">
                Zurück
              </i-button>
            </i-column>
            <i-column class="_text-align:right">
              <i-button color="success" @click="checkUnlockCode"> OK </i-button>
            </i-column>
          </i-row>
        </i-container>
      </template>
    </i-modal>
  </Teleport>
</template>

<style scoped>
.pinButton {
  min-width: 3em;
  min-height: 3em;
}
</style>
