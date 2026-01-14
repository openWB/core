<template>
	<Teleport to="body">
		<div :id="props.modalId" class="modal fade" data-bs-backdrop="static">
			<div class="modal-dialog modal-lg modal-fullscreen-lg-down">
				<div class="modal-content">
					<div class="modal-header">
						<h3 class="modal-title">
							<slot name="title" />
						</h3>
						<button
							type="button"
							class="btn-close buttonTextSize d-flex justify-content-center pt-3 pb-0"
							data-bs-dismiss="modal"
						></button>
					</div>
					<div class="modal-body">
						<slot />
					</div>
					<div class="modal-footer d-flex justify-content-center">
						<slot name="footer"></slot>
						<button
							class="close-button-bottom btn btn-secondary"
							data-bs-dismiss="modal"
						>
							Schließen
						</button>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

const props = defineProps<{
	modalId: string
}>()

onMounted(() => {
	/* let target = document.getElementById(props.modalId)
	if (target) {
		mod = new Modal(target, {})
	} */
})
</script>

<style scoped>
.modal {
	opacity: 1;
}
.modal-dialog {
	border-radius: 2px;
	box-shadow: 2px 2px 5px 3px darkslategray;
}

.modal-footer,
.modal-header,
.modal-body {
	background: var(--color-bg);
	color: var(--color-fg);
}
.btn-close {
	color: var(--color-input);
}
.modal-footer {
	text-align: right;
}
.modal-header .btn-close {
	color: var(--color-fg);
	border: 0px;
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

.close-button-bottom {
	font-size: var(--font-settings);
}
</style>
