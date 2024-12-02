import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';

export function useThemeManager() {
  const $q = useQuasar();
  const currentTheme = ref('custom1'); // Default theme

  const setTheme = (theme: string) => {
    currentTheme.value = theme;
    localStorage.setItem('selectedTheme', theme);
    document.body.classList.remove(
      'q-theme--light',
      'q-theme--dark',
      'q-theme--custom1',
      'q-theme--custom2',
      'q-theme--custom3',
      'q-theme--custom4',
      'q-theme--custom5',
    );
    document.body.classList.add(`q-theme--${theme}`);

    if (theme === 'dark') {
      $q.dark.set(true);
    } else {
      $q.dark.set(false);
    }
  };

  onMounted(() => {
    const savedTheme = localStorage.getItem('selectedTheme');
    setTheme(savedTheme || currentTheme.value);
  });

  return {
    currentTheme,
    setTheme,
  };
}
