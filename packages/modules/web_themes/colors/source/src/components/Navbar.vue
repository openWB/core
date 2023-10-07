<template>
	<!-- Fixed navbar -->
	<nav class="navbar navbar-expand-lg  px-3 mb-0">
		<a href="/" class="navbar-brand"><span>openWB</span></a>
		<button class="navbar-toggler togglebutton ps-5" type="button" data-bs-toggle="collapse" data-bs-target="#mainNavbar"
			aria-controls="mainNavbar" aria-expanded="false" aria-label="Toggle navigation">
			<span class="fa fa-ellipsis-vertical"></span>
		</button>
		<div class="collapse navbar-collapse justify-content-end" id="mainNavbar">
			<div class="nav navbar-nav">
				<a class="nav-link  " id="navStatus" href="../../settings/#/Status" target="_parent">Status</a>
				<div class="nav-item dropdown">

					<a class="nav-link" href="#" id="loggingDropdown" role="button" data-bs-toggle="dropdown"
						aria-expanded="false">Auswertungen <i class="fa-solid fa-caret-down"></i></a>
					<div class="dropdown-menu" aria-labelledby="loggingDropdown">
						<a href="../../settings/#/Logging/ChargeLog" class="dropdown-item" target="_parent">Ladeprotokoll</a>
						<a href="../../settings/#/Logging/Chart" class="dropdown-item" target="_parent">Diagramme</a>
					</div>
				</div>
				<div class="nav-item dropdown">
					<a class="nav-link" href="#" id="settingsDropdown" role="button" data-bs-toggle="dropdown"
						aria-expanded="false">Einstellungen <i class="fa-solid fa-caret-down"></i></a>
					<div class="dropdown-menu" aria-labelledby="settingsDropdown">
						<a class="nav-link" id="navSettings" href="../../settings/index.html" target="_parent">Wallbox</a>
						<a class="nav-link" data-bs-toggle="collapse" data-bs-target="#themesettings" aria-expanded="false"
							aria-controls="themeSettings">
							<span>Theme <span class="fa-solid fa-caret-down"></span></span>
						</a>
					</div>
				</div>
			</div>
		</div>
	</nav>
	<hr class="m-0 p-0 mb-2">
</template>

<script setup lang="ts">

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
	color: var(--color-fg)
}

.navbar-brand {
	font-weight: bold;
	color: var(--color-fg);
}

.nav-link {
	color: var(--color-fg);
	border-color: red;
	font-size: var(--font-normal);
}


.navbar-toggler {
	color: var(--color-fg);
	border-color: var(--color-bg)
}
</style>