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
  components: {
    FontAwesomeIcon,
  },
  emits: ["key:digit", "key:clear", "key:delete"],
  data() {
    return {
      buttonRows: [
        [
          {value: 1, label: "1"},
          {value: 2, label: "2"},
          {value: 3, label: "3"},
        ],
        [
          {value: 4, label: "4"},
          {value: 5, label: "5"},
          {value: 6, label: "6"},
        ],
        [
          {value: 7, label: "7"},
          {value: 8, label: "8"},
          {value: 9, label: "9"},
        ],
      ],
    };
  },
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
    <i-row
      v-for="buttonRow in buttonRows"
      :key="buttonRow"
      center
      class="_padding-bottom:1"
    >
      <i-column
        v-for="button in buttonRow"
        :key="button.value"
        class="pin-button-column"
      >
        <i-button
          size="lg"
          class="pin-button"
          @click="emitDigit(button.value)"
        >
          {{ button.label }}
        </i-button>
      </i-column>
    </i-row>
    <i-row center>
      <i-column class="pin-button-column">
        <i-button
          size="lg"
          class="pin-button"
          @click="emitClear()"
        >
          <FontAwesomeIcon
            fixed-width
            :icon="['fas', 'fa-eraser']"
          />
        </i-button>
      </i-column>
      <i-column class="pin-button-column">
        <i-button
          size="lg"
          class="pin-button"
          @click="emitDigit('0')"
        >
          0
        </i-button>
      </i-column>
      <i-column class="pin-button-column">
        <i-button
          size="lg"
          class="pin-button"
          @click="emitDelete()"
        >
          <FontAwesomeIcon
            fixed-width
            :icon="['fas', 'fa-delete-left']"
          />
        </i-button>
      </i-column>
    </i-row>
  </i-container>
</template>

<style scoped>
.pin-button-column {
  display: flex;
  flex-grow: 1;
}

.pin-button {
  min-height: 2em;
  flex-grow: 1;
  font-size: 200%;
  font-weight: bold;
}
</style>
