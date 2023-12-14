<script>
import NumberPad from "./NumberPad.vue";

export default {
  name: "CodeInputModal",
  props: {
    modelValue: { type: Boolean, required: true },
    backgroundColor: { type: String, default: "warning" },
    placeholderCharacter: {
      type: String,
      default: "*",
      validator(value) {
        return value.length == 1;
      },
    },
    inputVisible: { type: Boolean, default: false },
    minLength: { type: Number, default: 4 },
    maxLength: { type: Number, default: 4 },
  },
  data() {
    return {
      number: "",
      modalBackground: this.backgroundColor,
    };
  },
  components: {
    NumberPad,
  },
  emits: ["update:modelValue", "update:inputValue"],
  computed: {
    placeholder() {
      return this.placeholderCharacter.repeat(this.minLength);
    },
    enableSubmit() {
      return (
        this.number.length >= this.minLength &&
        this.number.length <= this.maxLength
      );
    },
  },
  watch: {
    modelValue(newValue, oldValue) {
      if (newValue === false && oldValue === true) {
        this.clear();
      }
    },
  },
  methods: {
    abort() {
      this.$emit("update:modelValue", false);
    },
    addDigit(digit) {
      if (this.number.length < this.maxLength) {
        this.number += digit;
      }
    },
    removeDigit() {
      this.number = this.number.slice(0, -1);
    },
    clear() {
      this.number = "";
    },
    submit() {
      this.$emit("update:inputValue", this.number);
    },
    success(color = "success") {
      this.modalBackground = color;
      setTimeout(() => {
        this.$emit("update:modelValue", false);
        this.modalBackground = this.backgroundColor;
      }, 500);
    },
    error(color = "danger") {
      this.modalBackground = color;
      setTimeout(() => {
        this.clear();
        this.modalBackground = this.backgroundColor;
      }, 2000);
    },
  },
};
</script>

<template>
  <Teleport to="body">
    <i-modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :color="modalBackground"
    >
      <template #header>
        <slot name="header"> **HEADER** </slot>
      </template>
      <i-container>
        <i-row center class="_padding-bottom:1">
          <i-column>
            <i-input
              v-model="number"
              :placeholder="placeholder"
              readonly
              size="lg"
              :type="inputVisible ? 'text' : 'password'"
              class="_text-align:center"
            />
          </i-column>
        </i-row>
        <NumberPad
          @key:digit="addDigit($event)"
          @key:clear="clear()"
          @key:delete="removeDigit($event)"
        />
      </i-container>
      <template #footer>
        <i-container>
          <i-row>
            <i-column>
              <i-button color="danger" @click="abort">
                <slot name="abort"> Zurück </slot>
              </i-button>
            </i-column>
            <i-column class="_text-align:right">
              <i-button v-if="enableSubmit" color="success" @click="submit">
                <slot name="submit"> OK </slot>
              </i-button>
            </i-column>
          </i-row>
        </i-container>
      </template>
    </i-modal>
  </Teleport>
</template>

<style scoped></style>
