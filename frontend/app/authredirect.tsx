import { Redirect } from "expo-router";

export default function AuthRedirectRoute() {
  return <Redirect href="/login" />;
}
