<template>
  <div class="chartContainer">
    <ChartjsLine
      v-if="chartDataRead"
      ref="priceChart"
      :data="chartDataObject"
      :options="myChartOptions"
      class="chart"
      @click="chartClick"
    />
  </div>
</template>

<script setup>
import { ref, useTemplateRef, computed } from 'vue';
import { useMqttStore } from 'src/stores/mqtt-store';
import { useQuasar } from 'quasar';

import { Line as ChartjsLine } from 'vue-chartjs';
import 'chartjs-adapter-luxon';
import annotationPlugin from 'chartjs-plugin-annotation';
import {
  Chart,
  Legend,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Filler,
} from 'chart.js';
Chart.register(
  Legend,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Filler,
  annotationPlugin,
);

const props = defineProps({
  modelValue: {
    type: Number,
    required: false,
    default: undefined,
  },
});
const emit = defineEmits(['update:modelValue']);

const mqttStore = useMqttStore();
const $q = useQuasar();

const priceChart = useTemplateRef('priceChart');

const chartDatasets = ref({
  datasets: [
    {
      label: 'Stromtarif',
      unit: 'ct/kWh',
      type: 'line',
      stepped: true,
      borderColor: 'rgb(18, 111, 142)',
      backgroundColor: 'rgb(18, 111, 142)',
      fill: false,
      pointStyle: 'circle',
      pointRadius: 0,
      pointHoverRadius: 4,
      cubicInterpolationMode: 'monotone',
      hidden: false,
      borderWidth: 2,
      data: undefined,
      yAxisID: 'y',
      parsing: {
        xAxisKey: 'timestamp',
        yAxisKey: 'price',
      },
    },
  ],
});

const chartDataObject = computed(() => {
  let myData = [];
  const chartEntries = mqttStore.etPrices;
  if (Object.keys(chartEntries).length > 0) {
    // proper scaling:
    // timestamp: seconds -> milliseconds
    // price: €/Wh -> €/kWh
    for (const [key, value] of Object.entries(chartEntries)) {
      myData.push({
        timestamp: key * 1000,
        price: value * 100000,
      });
    }
    // repeat last dataset with 59min 59sec offset
    const lastData = myData.slice(-1)[0];
    myData.push({
      timestamp: lastData.timestamp + (60 * 60 - 1) * 1000,
      price: lastData.price,
    });
  }
  const dataObject = chartDatasets.value;
  dataObject.datasets[0].data = myData;
  return dataObject;
});

const chartDataRead = computed(() => {
  return Object.keys(chartDataObject.value.datasets[0].data).length > 0;
});

const priceAnnotations = computed(() => {
  const colorUnblocked = 'rgba(73, 238, 73, 0.2)'; // ToDo: use theme color
  const colorBlocked = 'rgba(255, 10, 13, 0.2)'; // ToDo: use theme color
  const myData = chartDataObject.value.datasets[0].data;
  class Annotation {
    type = 'box';
    drawTime = 'beforeDatasetsDraw';
    xMin = myData[0].timestamp;
    xMax = myData[0].timestamp;
    borderWidth = 2;
    cornerRadius = 0;
  }
  let annotations = [];
  if (props.modelValue !== undefined) {
    for (let i = 0; i < myData.length; i++) {
      if (myData[i].price <= props.modelValue) {
        let newAnnotation = new Annotation();
        newAnnotation.borderColor = colorUnblocked;
        newAnnotation.backgroundColor = colorUnblocked;
        newAnnotation.xMin = myData[i].timestamp; // set left edge of box
        while (i < myData.length && myData[i].price <= props.modelValue) {
          i++;
        }
        if (i == myData.length) {
          // correct index if out of bounds
          i--;
        }
        newAnnotation.xMax = myData[i].timestamp; // first index myData[i] > maxPrice is right edge of box
        annotations.push(newAnnotation); // add box to annotations
      }
    }
    for (let i = 0; i < myData.length; i++) {
      if (myData[i].price > props.modelValue) {
        let newAnnotation = new Annotation();
        newAnnotation.borderColor = colorBlocked;
        newAnnotation.backgroundColor = colorBlocked;
        newAnnotation.xMin = myData[i].timestamp; // set left edge of box
        while (i < myData.length && myData[i].price > props.modelValue) {
          i++;
        }
        if (i == myData.length) {
          // correct index if out of bounds
          i--;
        }
        newAnnotation.xMax = myData[i].timestamp; // first index myData[i] > maxPrice is right edge of box
        annotations.push(newAnnotation); // add box to annotations
      }
    }
  }
  return annotations;
});

const myChartOptions = computed(() => {
  return {
    plugins: {
      title: {
        display: false,
      },
      legend: {
        display: false,
      },
      annotation: {
        annotations: priceAnnotations.value,
      },
    },
    elements: {
      point: {
        radius: 2,
      },
    },
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'hour',
          text: 'Zeit',
          maxTicksLimit: 24,
        },
        display: true,
        title: {
          display: true,
          text: 'Uhrzeit',
          color: $q.dark.isActive ? 'rgb(255, 255, 255)' : 'rgb(0, 0, 0)',
        },
        ticks: {
          font: {
            size: 12,
          },
          color: $q.dark.isActive ? 'rgb(255, 255, 255)' : 'rgb(0, 0, 0)',
          // maxTicksLimit: 0,
        },
        grid: {
          color: $q.dark.isActive
            ? 'rgba(255, 255, 255, 0.1)'
            : 'rgba(0, 0, 0, 0.1)',
        },
      },
      y: {
        position: 'left',
        type: 'linear',
        display: 'auto',
        // suggestedMin: 0,
        // suggestedMax: 0,
        title: {
          font: {
            size: 12,
          },
          display: true,
          text: 'Preis [ct/kWh]',
          color: $q.dark.isActive ? 'rgb(255, 255, 255)' : 'rgb(0, 0, 0)',
        },
        grid: {
          color: $q.dark.isActive
            ? 'rgba(255, 255, 255, 0.1)'
            : 'rgba(0, 0, 0, 0.1)',
        },
        ticks: {
          font: {
            size: 12,
          },
          stepSize: 0.1,
          maxTicksLimit: 11,
          color: $q.dark.isActive ? 'rgb(255, 255, 255)' : 'rgb(0, 0, 0)',
        },
      },
    },
  };
});

function chartClick(event) {
  const points = priceChart.value.chart.getElementsAtEventForMode(
    event,
    'index',
    { intersect: false },
    true,
  );
  if (points.length > 0) {
    emit(
      'update:modelValue',
      Math.ceil(
        chartDataObject.value.datasets[0].data[points[0].index].price * 100,
      ) / 100,
    );
  }
}
</script>

<style scoped>
.chartContainer {
  width: 100%;
  min-height: 200px;
  height: min(50vh, 300px);
}
</style>
