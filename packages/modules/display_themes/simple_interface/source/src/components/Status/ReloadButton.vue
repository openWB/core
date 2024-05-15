<script>
/* fontawesome */
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faUndo as fasUndo } from "@fortawesome/free-solid-svg-icons";
/* add icons to the library */
library.add(fasUndo);

export default {
  name: "ReloadButton",
  props: {},
  data() {
    return {};
  },
  components: {
    FontAwesomeIcon,
  },
  methods: {
    /**
     * will trigger a reload of the current page
     */
    reloadDisplay() {
      location.reload();
    },
  },
};
</script>

<template>
  <i-button color="success" @click="reloadDisplay()">
    Display neu laden
    <FontAwesomeIcon fixed-width :icon="['fas', 'fa-undo']" />
  </i-button>
</template>

<style scoped></style>
