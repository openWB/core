<template>
	<svg
		class="spark-line"
		:viewBox="`0 0 ${width} ${height}`"
		width="100%"
		preserveAspectRatio="xMinYMin"
	>
		<rect
			v-for="bar in bars"
			:key="bar.x"
			:x="bar.x"
			:y="bar.y"
			:width="bar.width"
			:height="bar.height"
			:class="colorNegative && bar.negative ? 'negative' : ''"
		/>
		<path
			class="zero-line"
			:d="`M 0 ${zeroHeight} L ${width} ${zeroHeight}`"
		/>
	</svg>
</template>

<script>
export default {
	props: {
		data: {
			required: true,
			type: Array,
			default() {
				return [];
			},
		},
		width: { Number, default: 250 },
		height: { Number, default: 70 },
		gap: { Number, default: 2 },
		stroke: { Number, default: 3 },
		min: { Number, default: 0 },
		max: { Number, default: 1 },
		color: { String, default: "var(--color--primary)" },
		colorNegative: { String, default: undefined },
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
			return this.data.slice(-this.maxPoints);
		},
		zeroHeight() {
			return (
				this.height -
				((0 - this.lowestPoint) /
					(this.highestPoint - this.lowestPoint)) *
					this.height
			);
		},
		coordinates() {
			const coordinateArray = [];
			this.slicedData.forEach((item, n) => {
				const x = (n * this.width) / this.maxPoints;
				const y =
					this.height -
					((item - this.lowestPoint) /
						(this.highestPoint - this.lowestPoint)) *
						this.height;
				coordinateArray.push({ x, y });
			});
			return coordinateArray;
		},
		bars() {
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
		},
		fillEndPath() {
			return `V ${this.height} L 4 ${this.height} Z`;
		},
	},
};
</script>

<style scoped>
svg {
	transition: all 1s ease-in-out;
}

svg path.zero-line {
	stroke: v-bind(color);
}

svg rect {
	stroke: v-bind(color);
	fill: v-bind(color);
}

svg rect.negative {
	stroke: v-bind(colorNegative);
	fill: v-bind(colorNegative);
}
</style>
