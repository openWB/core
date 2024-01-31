<script>
export default {
  name: "ExtendedNumberInput",
  inheritAttrs: false,
  props: {
    modelValue: { type: Number },
    unit: { type: String },
    min: { type: Number, default: 0 },
    max: { type: Number, default: 100 },
    step: { type: Number, default: 1 },
    labels: { type: Array },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      minimum: this.labels ? 0 : this.min,
      maximum: this.labels ? this.labels.length - 1 : this.max,
      stepSize: this.labels ? 1 : this.step,
    };
  },
  computed: {
    label() {
      var currentLabel;
      if (this.labels && this.inputValue != undefined) {
        if (this.inputValue < this.labels.length) {
          currentLabel = this.labels[this.inputValue].label;
        } else {
          console.error("index out of bounds: " + this.inputValue);
        }
      } else {
        currentLabel = this.inputValue;
      }
      if (typeof currentLabel == "number") {
        currentLabel = currentLabel.toLocaleString(undefined, {
          minimumFractionDigits: this.precision,
          maximumFractionDigits: this.precision,
        });
      }
      return currentLabel;
    },
    precision() {
      if (!isFinite(this.stepSize)) return 0;
      var e = 1,
        p = 0;
      while (Math.round(this.stepSize * e) / e !== this.stepSize) {
        e *= 10;
        p++;
      }
      return p;
    },
    inputValue: {
      get() {
        if (this.labels) {
          var myValue = undefined;
          for (let index = 0; index < this.labels.length; index++) {
            if (this.labels[index].value == this.modelValue) {
              myValue = index;
              break;
            }
          }
          if (myValue === undefined && this.modelValue !== undefined) {
            console.warn(
              "inputValue: not found in values: ",
              this.modelValue,
              "using minimum as default: ",
              this.minimum,
            );
            return this.minimum;
          } else {
            return myValue;
          }
        }
        return this.modelValue;
      },
      set(newInputValue) {
        if (this.labels) {
          var myValue = this.labels[newInputValue].value;
          this.$emit("update:modelValue", myValue);
        } else {
          this.$emit("update:modelValue", newInputValue);
        }
      },
    },
  },
  methods: {
    increment() {
      var newInputValue = Math.min(
        this.inputValue + this.stepSize,
        this.maximum,
      );
      // rounding needed!
      this.inputValue =
        Math.round(newInputValue * Math.pow(10, this.precision)) /
        Math.pow(10, this.precision);
    },
    decrement() {
      var newInputValue = Math.max(
        this.inputValue - this.stepSize,
        this.minimum,
      );
      // rounding needed!
      this.inputValue =
        Math.round(newInputValue * Math.pow(10, this.precision)) /
        Math.pow(10, this.precision);
    },
  },
};
</script>

<template>
  <i-input plaintext class="_text-align:right" size="lg" v-model="label">
    <template #prepend>
      <i-button @click="decrement">-</i-button>
    </template>
    <template #suffix>{{ unit }}</template>
    <template #append>
      <i-button @click="increment">+</i-button>
    </template>
  </i-input>
</template>

<style scoped></style>
