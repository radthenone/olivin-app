import { StyleSheet, Platform } from 'react-native';

/**
 * Style specyficzne dla platformy Native (Android/iOS)
 */
export const nativeStyles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  card: {
    ...Platform.select({
      android: {
        elevation: 2,
        borderRadius: 4,
        backgroundColor: '#FFFFFF',
      },
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        borderRadius: 8,
        backgroundColor: '#FFFFFF',
      },
    }),
  },
  button: {
    ...Platform.select({
      android: {
        elevation: 2,
        borderRadius: 4,
      },
      ios: {
        borderRadius: 8,
      },
    }),
  },
  input: {
    ...Platform.select({
      android: {
        borderBottomWidth: 1,
        borderBottomColor: '#E0E0E0',
      },
      ios: {
        borderWidth: 1,
        borderColor: '#C6C6C8',
        borderRadius: 8,
      },
    }),
  },
  ripple: {
    color: 'rgba(0, 0, 0, 0.1)',
  },
  listItem: {
    ...Platform.select({
      android: {
        paddingVertical: 12,
        paddingHorizontal: 16,
      },
      ios: {
        paddingVertical: 16,
        paddingHorizontal: 20,
      },
    }),
  },
});

/**
 * Funkcja pomocnicza do łączenia stylów native
 */
export const combineNativeStyles = (...styles: any[]) => {
  return StyleSheet.flatten(styles);
};

