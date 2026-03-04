import { Text, View } from "react-native";
import { cn, ps } from "@lib";
import { Container } from "@ui";

export default function HomeScreen() {
  return (
    <>
      <View className={cn("flex-1", ps({ web: "p-2", native: "p-2" }))}>
        <Text>Home</Text>
        <Container
          direction="row"
          platform="web"
          gap={4}
          align="center"
          justify="between"
        >
          <Text>Web</Text>
        </Container>
        <Container
          direction="row"
          platform="native"
          gap={4}
          align="center"
          justify="center"
          className="p-4 bg-gray-200 rounded"
        >
          <Text>Native</Text>
        </Container>
      </View>
    </>
  );
}
