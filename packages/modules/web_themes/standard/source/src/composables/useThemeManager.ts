import { ref, onMounted } from 'vue';
import { useQuasar } from 'quasar';

export function useThemeManager() {
  const $q = useQuasar();
  const currentTheme = ref('custom'); // Default theme

  const setTheme = (theme: string) => {
    currentTheme.value = theme;
    localStorage.setItem('selectedTheme', theme);
    document.body.classList.remove(
      'q-theme--light',
      'q-theme--dark',
      'q-theme--custom',
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
