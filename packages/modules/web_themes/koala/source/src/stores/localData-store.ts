import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useQuasar } from 'quasar';

export const useLocalDataStore = defineStore('localData', () => {
  const $q = useQuasar();

  //////////////    Legend Visibility     ///////////////////////

  const legendVisible = ref(!$q.platform.is.mobile);

  const toggleLegendVisibility = () => {
    legendVisible.value = !legendVisible.value;
  };

  //////////////    Legend Item Visibility     ///////////////////////

  const hiddenDatasets = ref<string[]>([]);

  // Function to add a dataset to hidden list
  const hideDataset = (datasetKey: string) => {
    if (!hiddenDatasets.value.includes(datasetKey)) {
      hiddenDatasets.value.push(datasetKey);
    }
  };

  const showDataset = (datasetKey: string) => {
    hiddenDatasets.value = hiddenDatasets.value.filter(
      (item) => item !== datasetKey,
    );
  };

  const toggleDataset = (datasetKey: string) => {
    if (hiddenDatasets.value.includes(datasetKey)) {
      showDataset(datasetKey);
    } else {
      hideDataset(datasetKey);
    }
  };

  const isDatasetHidden = (datasetKey: string): boolean => {
    return hiddenDatasets.value.includes(datasetKey);
  };

  return {
    hiddenDatasets,
    isDatasetHidden,
    toggleDataset,
    hideDataset,
    showDataset,
    legendVisible,
    toggleLegendVisibility,
  };
});
