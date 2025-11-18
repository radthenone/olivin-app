import { StyleSheet } from 'react-native';

/**
 * Style specyficzne dla platformy Web
 */
export const webStyles = StyleSheet.create({
  container: {
    maxWidth: 1200,
    marginHorizontal: 'auto',
    paddingHorizontal: 20,
  },
  card: {
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    borderRadius: 8,
    transition: 'all 0.2s ease',
  },
  button: {
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    userSelect: 'none',
  },
  input: {
    outlineWidth: 0,
    outlineStyle: 'none',
    outlineColor: 'transparent',
  },
  link: {
    cursor: 'pointer',
    textDecorationLine: 'underline',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: 16,
  },
});

/**
 * Funkcja pomocnicza do łączenia stylów web
 */
export const combineWebStyles = (...styles: any[]) => {
  return StyleSheet.flatten(styles);
};

