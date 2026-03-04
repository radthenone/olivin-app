import { Text } from "react-native";
import { Link } from "expo-router";
import { Web, Native } from "@lib";

export default function NotFoundScreen() {
  return (
    <>
      <Web>
        <title>404</title>
        <h1>404 - Page Not Found</h1>
        <p>Sorry, the page you are looking for does not exist.</p>
      </Web>
      <Native>
        <Text>404</Text>
        <Text>Page not found</Text>
      </Native>
      <Link href="/">Go to Home</Link>
    </>
  );
}
