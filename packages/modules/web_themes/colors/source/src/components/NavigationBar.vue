<template>
	<!-- Fixed navbar -->
	<nav class="navbar navbar-expand-lg px-0 mb-0">
		<div :class="containerclass">
			<a href="/" class="navbar-brand"><span>openWB</span></a>
			<span
				v-if="globalConfig.showClock == 'navbar'"
				class="position-absolute-50 navbar-text ms-4 navbar-time"
				:style="{ color: 'var(--color-menu)' }"
				>{{ formatCurrentTime(currentTime) }}</span
			>
			<button
				class="navbar-toggler togglebutton ps-5"
				type="button"
				data-bs-toggle="collapse"
				data-bs-target="#mainNavbar"
				aria-controls="mainNavbar"
				aria-expanded="false"
				aria-label="Toggle navigation"
			>
				<span class="fa-solid fa-ellipsis-vertical" />
			</button>
			<div id="mainNavbar" class="collapse navbar-collapse justify-content-end">
				<div class="nav navbar-nav">
					<a id="navStatus" class="nav-link" href="../../settings/#/Status"
						>Status</a
					>
					<div class="nav-item dropdown">
						<a
							id="loggingDropdown"
							class="nav-link"
							href="#"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
							>Auswertungen <i class="fa-solid fa-caret-down" />
						</a>
						<div class="dropdown-menu" aria-labelledby="loggingDropdown">
							<a href="../../settings/#/Logging/ChargeLog" class="dropdown-item"
								>Ladeprotokoll</a
							>
							<a href="../../settings/#/Logging/Chart" class="dropdown-item"
								>Diagramme</a
							>
						</div>
					</div>
					<div class="nav-item dropdown">
						<a
							id="settingsDropdown"
							class="nav-link"
							href="#"
							role="button"
							data-bs-toggle="dropdown"
							aria-expanded="false"
							>Einstellungen <span class="fa-solid fa-caret-down" />
						</a>
						<div class="dropdown-menu" aria-labelledby="settingsDropdown">
							<a
								id="navSettings"
								class="nav-link"
								href="../../settings/index.html"
								>openWB</a
							>
							<a
								class="nav-link"
								data-bs-toggle="collapse"
								data-bs-target="#themesettings"
								aria-expanded="false"
								aria-controls="themeSettings"
							>
								<span
									>Look&amp;Feel<span class="fa-solid fa-caret-down" />
								</span>
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	</nav>
	<div :class="containerclass">
		<hr class="m-0 p-0 mb-2" />
	</div>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { formatCurrentTime } from '@/assets/js/helpers'
import { currentTime } from '@/assets/js/model'

let interval: ReturnType<typeof setInterval>

const containerclass = computed(() => {
	return globalConfig.fluidDisplay ? 'container-fluid' : 'container-lg'
})

onMounted(() => {
	interval = setInterval(() => {
		currentTime.value = new Date()
	}, 1000)
})
onBeforeUnmount(() => {
	clearInterval(interval)
})
</script>

<style scoped>
.navbar {
	background-color: var(--color-bg);
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.dropdown-menu {
	background-color: var(--color-bg);
	color: var(--color-fg);
}

.dropdown-item {
	background-color: var(--color-bg);
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.btn {
	font-size: var(--font-medium);
	background-color: var(--color-bg);
	color: var(--color-fg);
}

.navbar-brand {
	font-weight: bold;
	color: var(--color-fg);
	font-size: var(--font-normal);
}

.nav-link {
	color: var(--color-fg);
	border-color: red;
	font-size: var(--font-normal);
}

.navbar-toggler {
	color: var(--color-fg);
	border-color: var(--color-bg);
}

.navbar-time {
	font-weight: bold;
	color: var(--color-menu);
	font-size: var(--font-normal);
}
</style>
