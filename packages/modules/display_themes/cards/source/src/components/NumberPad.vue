<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faDeleteLeft as fasDeleteLeft,
  faEraser as fasEraser,
} from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasDeleteLeft, fasEraser);

export default {
  name: "NumberPad",
  data() {
    return {};
  },
  components: {
    FontAwesomeIcon,
  },
  emits: ["key:digit", "key:clear", "key:delete"],
  methods: {
    emitDigit(value) {
      this.$emit("key:digit", value);
    },
    emitClear() {
      this.$emit("key:clear");
    },
    emitDelete() {
      this.$emit("key:delete");
    },
  },
};
</script>

<template>
  <i-container>
    <i-row center class="_padding-bottom:1">
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('1')">
          1
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('2')">
          2
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('3')">
          3
        </i-button>
      </i-column>
    </i-row>
    <i-row center class="_padding-bottom:1">
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('4')">
          4
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('5')">
          5
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('6')">
          6
        </i-button>
      </i-column>
    </i-row>
    <i-row center class="_padding-bottom:1">
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('7')">
          7
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('8')">
          8
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('9')">
          9
        </i-button>
      </i-column>
    </i-row>
    <i-row center>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitClear()">
          <FontAwesomeIcon fixed-width :icon="['fas', 'fa-eraser']" />
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDigit('0')">
          0
        </i-button>
      </i-column>
      <i-column class="_flex-grow:0">
        <i-button size="lg" class="pinButton" @click="emitDelete()">
          <FontAwesomeIcon fixed-width :icon="['fas', 'fa-delete-left']" />
        </i-button>
      </i-column>
    </i-row>
  </i-container>
</template>

<style scoped>
.pinButton {
  min-width: 3em;
  min-height: 3em;
}
</style>
