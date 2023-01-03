<script>
export default {
	name: "DashBoardCard",
	props: {
		color: String,
	},
};
</script>

<template>
	<i-card :color="color">
		<template #header>
			<i-container>
				<i-row>
					<i-column>
						<slot name="headerLeft" />
					</i-column>
					<i-column
						v-if="$slots.headerRight"
						class="_text-align:right"
					>
						<slot name="headerRight" />
					</i-column>
				</i-row>
			</i-container>
		</template>
		<slot />
	</i-card>
</template>

<style lang="scss" scoped>
@import "@inkline/inkline/css/variables";
@import "@inkline/inkline/css/mixins";

@include i-column {
	padding-left: 0;
	padding-right: 0;
}
</style>
