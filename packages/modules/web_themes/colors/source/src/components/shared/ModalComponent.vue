<template>
	<Teleport to="body">
		<div :id="props.modalId" class="modal fade">
			<div class="modal-dialog modal-lg modal-fullscreen-lg-down shadow">
				<div class="modal-content">
					<div class="modal-header">
						<h3 class="modal-title">
							<slot name="title" />
						</h3>
						<button
							type="button"
							class="btn-close d-flex justify-content-center pt-3 pb-0"
							data-bs-dismiss="modal"
						>
							<span class="fa-solid fa-xl fa-circle-check" />
						</button>
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
	border-radius: 30px;
	border: 0px dotted var(--color-frame);
}
.modal-content {
	border-radius: 30px;
}
.modal-title {
	font-size: var(--font-large);
	color: var(--color-charging);
}
.modal-footer,
.modal-header,
.modal-body {
	background: var(--color-bg);
	color: var(--color-fg);
}
.modal-header {
	border: 0px;
}
.btn-close {
	color: var(--color-menu);
	font-size: var(--font-medium);
	background-size: 0px;
}
.modal-footer {
	text-align: right;
	border: 0px;
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
	font-size: var(--font-settings-button);
}
</style>
