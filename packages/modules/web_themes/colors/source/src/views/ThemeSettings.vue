<template>
	<WbWidgetFlex :full-width="true">
		<template #title> Look & Feel </template>
		<template #buttons>
			<span
				type="button"
				class="float-end mt-0 ms-1"
				data-bs-toggle="collapse"
				data-bs-target="#themesettings"
			>
				<span>
					<i class="fa-solid fa-circle-check" />
				</span>
			</span>
		</template>
		<div class="subgrid m-0 p-0">
			<div class="topbanner grid-col-12">
				Eine Reihe von Einstellungen werden neu
				<em>in den openWB-Einstellungen "Allgemein"</em> <br />
				für alle Geräte einheitlich festgelegt.
			</div>
			<div class="settingscolumn">
				<ConfigItem
					:fullwidth="true"
					title="Buttonleiste für Ladepunkte"
					icon="fa-window-maximize"
					infotext="Informationen zu Ladepunkten über den Diagrammen anzeigen."
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.showButtonBar" />
					</template>
				</ConfigItem>
				<ConfigItem
					:fullwidth="true"
					title="Auswahleiste"
					icon="fa-filter"
					infotext="Hauptseite mit Reitern zur Schnellwahl von Widgets."
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.showQuickAccess" />
					</template>
				</ConfigItem>
				<ConfigItem
					v-if="globalConfig.showRelativeArcs"
					:fullwidth="true"
					title="Linker Graph: Bögen zurücksetzen"
					icon="fa-undo"
					infotext="Durch Click auf den Button wird die Maximallänge der Bögen auf den aktuellen Wert gesetzt."
				>
					<button
						v-if="globalConfig.showRelativeArcs"
						class="btn btn-secondary"
						@click="emit('reset-arcs')"
					>
						Reset
					</button>
				</ConfigItem>

				<ConfigItem
					:fullwidth="true"
					title="Kompakte Ladepunktliste"
					icon="fa-list"
					infotext="Zeige eine einzelne Ladepunktliste statt separater Element pro Ladepunkt."
				>
					<RadioInput2
						v-model="globalConfig.shortCpList"
						:options="shortListOptions"
					/>
				</ConfigItem>
			</div>
			<div class="settingscolumn">
				<ConfigItem
					:fullwidth="true"
					title="Breite Widgets"
					icon="fa-desktop"
					infotext="Widgets immer breit machen"
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.preferWideBoxes" />
					</template>
				</ConfigItem>
				<ConfigItem
					:fullwidth="true"
					title="Stufenlose Displaybreite"
					icon="fa-maximize"
					infotext="Die Breite des Displays wird immer voll ausgenutzt. Dies kann in einigen Fällen zu inkorrekter Darstellung führen."
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.fluidDisplay" />
					</template>
				</ConfigItem>
				<ConfigItem
					:fullwidth="true"
					title="Animationen"
					icon="fa-film"
					infotext="Animationen anzeigen"
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.showAnimations" />
					</template>
				</ConfigItem>
				<ConfigItem
					:fullwidth="true"
					title="Uhrzeit anzeigen"
					icon="fa-clock"
					infotext="Zeige die aktuelle Uhrzeit an. In der Menüleiste oder neben den Lade-Buttons."
				>
					<RadioInput2
						v-model="globalConfig.showClock"
						:options="clockModes"
					></RadioInput2>
				</ConfigItem>
			</div>
			<div class="settingscolumn">
				<ConfigItem
					:fullwidth="true"
					title="IFrame-Support für Einstellungen (Experimentell)"
					icon="fa-gear"
					infotext="Erlaubt das Lesen der Einstellungen, wenn das UI in andere Applikationen eingebettet ist (z.B. HomeAssistant). Erfordert eine mit SSL verschlüsselte Verbindung über HTTPS! Experimentelles Feature."
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.sslPrefs" />
					</template>
				</ConfigItem>
				<hr />
				<ConfigItem
					:fullwidth="true"
					title="Debug-Modus"
					icon="fa-bug-slash"
					infotext="Kontrollausgaben in der Console sowie Anzeige von Bildschirmbreite und MQ-Viewer"
				>
					<template #inline-item>
						<SwitchInput v-model="globalConfig.debug" />
					</template>
				</ConfigItem>
				<hr />
			</div>
			<div class="grid-col-12 mb-3 me-3">
				<button
					class="btn btn-sm btn-secondary float-end"
					data-bs-toggle="collapse"
					data-bs-target="#themesettings"
				>
					Schließen
				</button>
			</div>
		</div>
	</WbWidgetFlex>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput2 from '@/components/shared/RadioInput2.vue'

import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
const emit = defineEmits(['reset-arcs'])
const clockModes: [string, string][] = [
	['Aus', 'off'],
	['Menü', 'navbar'],
	['Buttonleiste', 'buttonbar'],
]
const shortListOptions: [string, string][] = [
	['Aus', 'no'],
	['"Alles"-Reiter', 'infoview'],
	['Immer', 'always'],
]
</script>
<style scoped>
.fa-circle-check {
	font-size: var(--font-large);
	background-color: var(--color-bg);
	color: var(--color-input);
}

.closebutton {
	justify-self: end;
}

.settingscolumn {
	padding: 20px;
}
.topbanner {
	font-size: var(--font-large);
	color: var(--color-charging);
	background-color: var(--color-bg);
	text-align: center;
	padding: 1em;
	border: 1px solid var(--color-charging);
	border-radius: 5px;
}
</style>
