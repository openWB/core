import { computed } from 'vue';
import { Screen, useQuasar } from 'quasar';

export const useTable = () => {
  const $q = useQuasar();

  const tooltipsEnabled = !$q.platform.is.mobile;

  const compactTable = computed(() => Screen.lt.md);

  // the browser tooltip is only set if the text is really cut off by the
  // ellipsis, otherwise it would pop up next to the fault message tooltip
  // without adding any information
  const titleIfTruncated = (event: MouseEvent) => {
    const element = event.currentTarget as HTMLElement;
    const text = element.textContent?.trim() ?? '';
    // one pixel tolerance, scrollWidth and clientWidth are rounded values
    if (text && element.scrollWidth - element.clientWidth > 1) {
      element.title = text;
    } else {
      element.removeAttribute('title');
    }
  };

  return {
    tooltipsEnabled,
    compactTable,
    titleIfTruncated,
  };
};
