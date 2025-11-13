import { Platform, ViewStyle, TextStyle, ImageStyle } from 'react-native';

/**
 * Zwraca style tylko dla platformy Web
 */
export const webOnly = <T extends ViewStyle | TextStyle | ImageStyle>(
  styles: T
): Partial<T> => {
  return Platform.OS === 'web' ? styles : {};
};

/**
 * Zwraca style tylko dla platform Native (Android/iOS)
 */
export const nativeOnly = <T extends ViewStyle | TextStyle | ImageStyle>(
  styles: T
): Partial<T> => {
  return Platform.OS !== 'web' ? styles : {};
};

/**
 * Zwraca style tylko dla platformy Android
 */
export const androidOnly = <T extends ViewStyle | TextStyle | ImageStyle>(
  styles: T
): Partial<T> => {
  return Platform.OS === 'android' ? styles : {};
};

/**
 * Zwraca style tylko dla platformy iOS
 */
export const iosOnly = <T extends ViewStyle | TextStyle | ImageStyle>(
  styles: T
): Partial<T> => {
  return Platform.OS === 'ios' ? styles : {};
};

/**
 * Zwraca style na podstawie warunku platformy
 */
export const platformSelect = <T extends ViewStyle | TextStyle | ImageStyle>(options: {
  web?: T;
  android?: T;
  ios?: T;
  native?: T;
  default?: T;
}): Partial<T> => {
  if (Platform.OS === 'web' && options.web) {
    return options.web;
  }
  if (Platform.OS === 'android' && options.android) {
    return options.android;
  }
  if (Platform.OS === 'ios' && options.ios) {
    return options.ios;
  }
  if (Platform.OS !== 'web' && options.native) {
    return options.native;
  }
  return options.default || {};
};

/**
 * Zwraca wartość na podstawie platformy
 */
export const platformValue = <T>(options: {
  web?: T;
  android?: T;
  ios?: T;
  native?: T;
  default?: T;
}): T | undefined => {
  if (Platform.OS === 'web' && options.web !== undefined) {
    return options.web;
  }
  if (Platform.OS === 'android' && options.android !== undefined) {
    return options.android;
  }
  if (Platform.OS === 'ios' && options.ios !== undefined) {
    return options.ios;
  }
  if (Platform.OS !== 'web' && options.native !== undefined) {
    return options.native;
  }
  return options.default;
};

