<script>
export default {
  props: {
    data: {
      required: false,
      type: Array,
      default: undefined,
    },
    socData: {
      required: false,
      type: Array,
      default: undefined,
    },
    width: { type: Number, default: 250 },
    height: { type: Number, default: 70 },
    gap: { type: Number, default: 3 },
    stroke: { type: Number, default: 3 },
    min: { type: Number, default: 0 },
    max: { type: Number, default: 1 },
    color: { type: String, default: "var(--color--primary)" },
    colorNegative: { type: String, default: undefined },
  },
  computed: {
    highestPoint() {
      return Math.max(1, this.max, ...this.slicedData);
    },
    lowestPoint() {
      return Math.min(0, this.min, ...this.slicedData);
    },
    maxPoints() {
      return Math.floor(this.width / (this.stroke + this.gap));
    },
    slicedData() {
      if (this.data) {
        return this.data.slice(-this.maxPoints);
      }
      return undefined;
    },
    slicedSocData() {
      if (this.socData) {
        return this.socData.slice(-this.maxPoints);
      }
      return undefined;
    },
    zeroHeight() {
      return (
        this.height -
        ((0 - this.lowestPoint) / (this.highestPoint - this.lowestPoint)) *
          this.height
      );
    },
    coordinates() {
      if (this.data) {
        return this.calculateCoordinates(
          this.slicedData,
          this.lowestPoint,
          this.highestPoint,
        );
      }
      return undefined;
    },
    socCoordinates() {
      if (this.socData) {
        return this.calculateCoordinates(this.slicedSocData, 0, 100);
      }
      return undefined;
    },
    bars() {
      if (this.coordinates) {
        const barCoordinates = [];
        this.coordinates.forEach((point) => {
          const left = point.x;
          const y = point.y;
          const width = this.stroke;
          const top = Math.min(y, this.zeroHeight);
          const height = Math.abs(y - this.zeroHeight);
          const isNegative = y > this.zeroHeight;
          barCoordinates.push({
            x: left,
            y: top,
            width: width,
            height: height,
            negative: isNegative,
          });
        });
        return barCoordinates;
      }
      return undefined;
    },
    socPath() {
      if (this.socCoordinates && this.socCoordinates.length > 0) {
        let firstPoint = this.socCoordinates.slice(0, 1)[0];
        let lastPoint = this.socCoordinates.slice(-1)[0];
        var path = `M 0,${this.height}`; // start in lower left corner
        path += ` L 0,${firstPoint.y}`; // go vertical to first value
        this.socCoordinates.forEach((point) => {
          path += ` L ${point.x + this.stroke / 2},${point.y}`; // x is centered on bars
        });
        path +=
          ` L ${lastPoint.x + this.stroke},${lastPoint.y}` + // extend last value to right end of last bar
          ` L ${lastPoint.x + this.stroke},${this.height}` + // go vertical to zero
          " Z"; // close path
        return path;
      }
      return undefined;
    },
  },
  methods: {
    calculateCoordinates(dataset, min, max) {
      const coordinateArray = [];
      dataset.forEach((item, n) => {
        const x = (n * this.width) / this.maxPoints + 1; // compensate stroke-width
        const y = this.height - ((item - min) / (max - min)) * this.height;
        coordinateArray.push({ x, y });
      });
      return coordinateArray;
    },
  },
};
</script>

<template>
  <svg
    class="spark-line"
    :viewBox="`0 0 ${width} ${height}`"
    width="100%"
    preserveAspectRatio="xMinYMin"
  >
    <path
      v-if="socData"
      class="soc-path"
      :d="socPath"
    />
    <rect
      v-for="bar in bars"
      :key="bar.x"
      :x="bar.x"
      :y="bar.y"
      :width="bar.width"
      :height="bar.height"
      :class="colorNegative && bar.negative ? 'negative' : ''"
    />
    <line
      class="zero-line"
      :x1="0"
      :y1="zeroHeight"
      :x2="width"
      :y2="zeroHeight"
    />
  </svg>
</template>

<style scoped>
svg {
  transition: all 1s ease-in-out;
}

svg line.zero-line {
  stroke: v-bind(color);
}

svg rect,
svg path {
  stroke: v-bind(color);
  fill: v-bind(color);
  fill-opacity: 0.5;
  stroke-width: 1px;
}

svg rect.negative {
  stroke: v-bind(colorNegative);
  fill: v-bind(colorNegative);
}

svg path.soc-path {
  fill-opacity: 0.4;
}
</style>
