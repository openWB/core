<template>
	<div :id="props.modalId" class="modal fade">
		<div class="modal-dialog modal-lg modal-fullscreen-lg-down">
			<div class="modal-content">
				<div class="modal-header">
					<h3 class="modal-title scaled">
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
				<div class="modal-body">
					<slot />
				</div>
				<div class="modal-footer"></div>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
const props = defineProps<{
	modalId: string
}>()
</script>

<style scoped>
.modal-content {
	background-color: var(--color-bg);
	border-color: var(--color-menu);
	box-shadow: 3px 5px black;
}
.modal-footer,
.modal-header,
.modal-body {
	background-color: var(--color-bg);
	color: var(--color-fg);
}
.modal-body {
	border-color: var(--color-fg);
}
.modal-footer {
	text-align: right;
}
.modal-header .btn-close {
	color: var(--color-fg);
	background-color: var(--color-bg);
	border: 0px;
}
.modal-title {
	color: var(--color-fg);
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
	color: var(--color-fg);
}
</style>
