<template>
	<div :id="props.modalId" class="modal fade">
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
					>
						<i class="fa-solid fa-lg fa-rectangle-xmark m-0 p-0" />
					</button>
				</div>
				<div class="modal-body" style="background-color: var(--color-bg)">
					<slot />
					<button
						class="btn btn-secondary float-end mt-3 ms-1"
						data-bs-dismiss="modal"
					>
						Schließen
					</button>
				</div>
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
	background: var(--color-bg);
}
.btn-close {
	color: var(--color-fg);
}
.modal-footer {
	text-align: right;
}
.modal-header .btn-close {
	color: var(--color-fg);
	background: var(--color-bg);
	border: 0px;
}

/*.modal.fade .modal-dialog {
    -webkit-transform: scale(0.1);
    -moz-transform: scale(0.1);
    -ms-transform: scale(0.1);
    transform: scale(0.1);
     top: 300px;
    opacity: 0;
    -webkit-transition: all 0.3s;
    -moz-transition: all 0.3s;
    transition: all 0.3s;
 }*/

/*.modal.fade.in .modal-dialog {
    -webkit-transform: scale(1);
    -moz-transform: scale(1);
    -ms-transform: scale(1);
    transform: scale(1);
     -webkit-transform: translate3d(0, -300px, 0);
    transform: translate3d(0, -300px, 0);
    opacity: 1;
 
 }*/

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
</style>
