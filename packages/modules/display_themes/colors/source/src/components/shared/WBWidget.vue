<template>
	<div class="p-2 m-0 cont">
		<div class="wb-widget m-0 pb-2 shadow">
			<div class="header mt-4 mx-2">
				<div class="titles">
					<div class="title">
						<slot name="title">
							<div class="p-0">(title goes here)</div>
						</slot>
					</div>
					<div class="subtitle">
						<slot name="subtitle" />
					</div>
				</div>
				<div class="buttons">
					<slot name="buttons" />
				</div>
			</div>
			<div class="wb-subwidget mx-2">
				<slot />
			</div>
			<div v-if="$slots.footer != undefined">
				<hr class="grid-col-12" />
				<div class="wb-subwidget mx-2">
					<slot name="footer" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts"></script>

<style scoped>
.wb-widget {
	background-color: var(--color-bg);
	border: 0.1px solid var(--color-frame);
	height: 100%;
	align-self: stretch;
	width: 100%;
	border-radius: 30px;
	/* display: grid;
	grid-template-columns: repeat(12, auto);
	gap: 0.2em; */
}

.wb-subwidget {
	border: 0px solid var(--color-subframe);
	padding: var(--padding-widget);
	/*grid-column: span 12;*/
}

.header {
	grid-column: span 12;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.titles {
	display: flex;
	flex-direction: column;
}

.title {
	font-size: var(--font-extralarge);
	color: var(--color-title);
	font-weight: bold;
	transform: scaleX(0.9294);
}

.cont {
	align-self: stretch;
	height: 100%;
}
.subtitle {
	font-size: var(--font-medium);
}

.buttons {
	grid-column: span 6;
}
</style>
