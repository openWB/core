<template>
	<div :id="props.modalId" class="modal fade">
		<div class="modal-dialog modal-lg modal-fullscreen-sm-down">
			<div class="modal-content">
				<div class="modal-header">
					<h3 class="modal-title">
						<slot name="title" />
					</h3>
					<button
						type="button"
						class="btn-close buttonTextSize d-flex justify-content-center pt-3 pb-0"
						data-bs-dismiss="modal"
					>
						<i class="fa-solid fa-lg fa-circle-check m-0 p-0" />
					</button>
				</div>
				<div class="modal-body" style="background-color: var(--color-fg)">
					<slot />
				</div>
				<div class="modal-footer"></div>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
// import { Modal } from 'bootstrap'

const props = defineProps<{
	modalId: string
}>()
// state
//let mod: Modal

// lifecycle
onMounted(() => {
	/* let target = document.getElementById(props.modalId)
	if (target) {
		mod = new Modal(target, {})
	} */
})
</script>

<style scoped>
.modal-footer,
.modal-header,
.modal-body {
	background: var(--color-fg);
}
.modal-footer {
	text-align: right;
}
.modal-header .btn-close {
	color: var(--color-bg);
	background: var(--color-fg);
	border: 0px;
}
.modal-title {
	color: var(--color-bg);
}
.closebutton {
	background: var(--color-fg);
}

.modal.fade .modal-dialog {
	transition: transform 1s ease-out;
	transform: none;
	scale: 0.6;
}
.modal.show .modal-dialog {
	transition: transform 0.3s ease-in;
	transform: none;
	scale: 1;
}
.fa-circle-check {
	color: var(--color-bg);
}
</style>
