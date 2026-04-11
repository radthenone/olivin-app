/**
 * /app/(app)/_layout.tsx
 * Layout dla zalogowanych użytkowników — Stack z headerem.
 */
import { Stack } from "expo-router";

export default function AppLayout() {
  return (
    <Stack>
      <Stack.Screen name="home" options={{ title: "Strona główna" }} />
    </Stack>
  );
}
