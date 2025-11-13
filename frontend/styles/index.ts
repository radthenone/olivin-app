// React Native automatycznie wybierze odpowiedni plik:
// - styles.web.ts dla web
// - styles.native.ts dla android/ios
import { webStyles, combineWebStyles } from './styles.web';
import { nativeStyles, combineNativeStyles } from './styles.native';

// Eksportujemy style dla aktualnej platformy
export const platformStyles = typeof window !== 'undefined' ? webStyles : nativeStyles;
export const combineStyles = typeof window !== 'undefined' ? combineWebStyles : combineNativeStyles;

// Re-eksportujemy dla łatwego dostępu
export { webStyles, nativeStyles };
export * from './platformStyles';

