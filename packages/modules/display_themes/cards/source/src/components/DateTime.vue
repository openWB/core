<script>
export default {
  name: "DateTime",
  props: {
    separator: { type: String, default: "<br />" },
  },
  data() {
    return {
      dateTimeInterval: "",
      date: "",
      time: "",
    };
  },
  mounted() {
    this.update();
    this.dateTimeInterval = setInterval(this.update, 1000);
  },
  beforeUnmount() {
    clearInterval(this.dateTimeInterval);
  },
  methods: {
    update() {
      const now = new Date();
      const dateOptions = {
        weekday: "short",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      };
      const timeOptions = {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      };
      this.date = now.toLocaleDateString(undefined, dateOptions);
      this.time = now.toLocaleTimeString(undefined, timeOptions);
    },
  },
};
</script>

<template>{{ time }}<span v-html="separator" />{{ date }}</template>

<style scoped></style>
