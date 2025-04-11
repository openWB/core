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
  const hideDataset = (datasetName: string) => {
    if (!hiddenDatasets.value.includes(datasetName)) {
      hiddenDatasets.value.push(datasetName);
    }
  };

  const showDataset = (datasetName: string) => {
    hiddenDatasets.value = hiddenDatasets.value.filter(
      (item) => item !== datasetName,
    );
  };

  const toggleDataset = (datasetName: string) => {
    if (hiddenDatasets.value.includes(datasetName)) {
      showDataset(datasetName);
    } else {
      hideDataset(datasetName);
    }
  };

  const isDatasetHidden = (datasetName: string): boolean => {
    return hiddenDatasets.value.includes(datasetName);
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
