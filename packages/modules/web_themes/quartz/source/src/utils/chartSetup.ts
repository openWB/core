import { Chart, Tooltip, Legend, LineController, LineElement, PointElement, LinearScale, TimeScale, Filler } from 'chart.js'
import 'chartjs-adapter-luxon'

Chart.register(Tooltip, Legend, LineController, LineElement, PointElement, LinearScale, TimeScale, Filler)
