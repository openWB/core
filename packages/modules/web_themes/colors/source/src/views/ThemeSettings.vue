<template>
	<div class="container-fluid p-0 m-0">
		<div class="row p-0 m-0">
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
				<div class="row m-0 p-0">
					<div class="col-lg-4">
						<ConfigItem
							:fullwidth="true"
							title="Farbschema"
							icon="fa-adjust"
							infotext="Hintergrundfarbe"
						>
							<RadioInput
								v-model="globalConfig.displayMode"
								:options="colorschemes"
							/>
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Farbschema Smart-Home-Geräte"
							icon="fa-palette"
							infotext="Für die Smart-Home-Geräte stehen mehrere Schemata zur Verfügung."
						>
							<RadioInput
								v-model="globalConfig.smartHomeColors"
								:options="shSchemes"
							/>
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Grafik: Raster"
							icon="fa-th"
							infotext="Verwende ein Hintergrundraster in den Grafiken"
						>
							<SwitchInput v-model="globalConfig.showGrid" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Variable Bogenlänge"
							icon="fa-chart-area"
							infotext="Im Graph 'Aktuelle Leistung' können die Bögen immer die volle Länge haben, oder entsprechend des aktuellen Gesamtleistung verkürzt dargestellt werden."
						>
							<SwitchInput v-model="globalConfig.showRelativeArcs" />
						</ConfigItem>
						<ConfigItem
							v-if="globalConfig.showRelativeArcs"
							:fullwidth="true"
							title="Bögen zurücksetzen"
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
							title="Anzahl Dezimalstellen"
							icon="fa-sliders-h"
							infotext="Alle kW- und kWh-Werte werden mit der gewählten Anzahl an Stellen angezeigt."
						>
							<SelectInput
								v-model="globalConfig.decimalPlaces"
								:options="decimalDisplay"
							/>
						</ConfigItem>
					</div>
					<div class="col-lg-4">
						<!-- <ConfigItem :fullwidth="true" title="Kompakte Ladepunktliste" icon="fa-list"
							infotext="Zeige eine einzelne Ladepunktliste statt separater Element pro Ladepunkt.">
							<SwitchInput v-model="globalConfig.simpleCpList" />
						</ConfigItem>
						 -->
						<ConfigItem
							:fullwidth="true"
							title="Uhrzeit anzeigen"
							icon="fa-clock"
							infotext="Zeige die aktuelle Uhrzeit an. In der Menüleiste oder neben den Lade-Buttons."
						>
							<!-- <SwitchInput v-model="globalConfig.showClock" /> -->
							<RadioInput
								v-model="globalConfig.showClock"
								:options="clockModes"
							></RadioInput>
						</ConfigItem>

						<ConfigItem
							:fullwidth="true"
							title="Kompakte Ladepunktliste"
							icon="fa-list"
							infotext="Zeige eine einzelne Ladepunktliste statt separater Element pro Ladepunkt."
						>
							<RadioInput
								v-model="globalConfig.shortCpList"
								:options="shortListOptions"
							/>
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Buttonleiste für Ladepunkte"
							icon="fa-window-maximize"
							infotext="Informationen zu Ladepunkten über den Diagrammen anzeigen."
						>
							<SwitchInput v-model="globalConfig.showButtonBar" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Filter-Buttons"
							icon="fa-filter"
							infotext="Hauptseite mit Buttons zur Auswahl der Kategorie."
						>
							<SwitchInput v-model="globalConfig.showQuickAccess" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Breite Widgets"
							icon="fa-desktop"
							infotext="Widgets immer breit machen"
						>
							<SwitchInput v-model="globalConfig.preferWideBoxes" />
						</ConfigItem>
					</div>
					<div class="col-lg-4">
						<ConfigItem
							:fullwidth="true"
							title="Stufenlose Displaybreite"
							icon="fa-maximize"
							infotext="Die Breite des Displays wird immer voll ausgenutzt. Dies kann in einigen Fällen zu inkorrekter Darstellung führen."
						>
							<SwitchInput v-model="globalConfig.fluidDisplay" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Animationen"
							icon="fa-film"
							infotext="Animationen anzeigen"
						>
							<SwitchInput v-model="globalConfig.showAnimations" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Zähler anzeigen (beta)"
							icon="fa-chart-bar"
							infotext="Zeige die Werte zusätzlich angelegter Zähler (beta)"
						>
							<SwitchInput v-model="globalConfig.showCounters" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Fahrzeuge anzeigen (beta)"
							icon="fa-car"
							infotext="Zeige die Werte zusätzlich angelegter Zähler (beta)"
						>
							<SwitchInput v-model="globalConfig.showVehicles" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Preistabelle anzeigen (beta)"
							icon="fa-car"
							infotext="Zeige die Strompreistabelle in einer separaten Box an (beta)"
						>
							<SwitchInput v-model="globalConfig.showPrices" />
						</ConfigItem>
						<ConfigItem
							:fullwidth="true"
							title="Debug-Modus"
							icon="fa-bug-slash"
							infotext="Kontrollausgaben in der Console sowie Anzeige von Bildschirmbreite und MQ-Viewer"
						>
							<SwitchInput v-model="globalConfig.debug" />
						</ConfigItem>
					</div>
				</div>
				<div class="row p-0 m-0">
					<div class="col-12 mb-3 pe-3 mt-0">
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
		</div>
	</div>
</template>

<script setup lang="ts">
import { globalConfig } from '@/assets/js/themeConfig'
import SelectInput from '@/components/shared/SelectInput.vue'
import ConfigItem from '@/components/shared/ConfigItem.vue'
import SwitchInput from '@/components/shared/SwitchInput.vue'
import RadioInput from '@/components/shared/RadioInput.vue'
import WbWidgetFlex from '@/components/shared/WbWidgetFlex.vue'
const emit = defineEmits(['reset-arcs'])
const colorschemes: [string, string][] = [
	['Dunkel', 'dark'],
	['Hell', 'light'],
	['Blau', 'blue'],
]
const decimalDisplay: [string, string][] = [
	['3 kW', '0'],
	['3,1 kW', '1'],
	['3,14 kW', '2'],
	['3,141 kW', '3'],
	['3141 W', '4'],
]
const shSchemes: [string, string][] = [
	['Orange', 'normal'],
	['Grün/Violett', 'standard'],
	['Bunt', 'advanced'],
]
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
	font-size: var(--font-extralarge);
	background-color: var(--color-bg);
	color: var(--color-menu);
}
</style>
