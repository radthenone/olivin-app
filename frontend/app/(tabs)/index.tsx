import { View, Text, StyleSheet, ScrollView } from "react-native";
import { Link } from "expo-router";

export default function TabsHomeScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Home</Text>
        <Link href={"/products" as any} style={styles.link}>
          <Text style={styles.linkText}>View Products</Text>
        </Link>
        <Link href="/health" style={styles.link}>
          <Text style={styles.linkText}>Health Status</Text>
        </Link>
        <Link href="/logs" style={styles.link}>
          <Text style={styles.linkText}>Application Logs</Text>
        </Link>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
    color: "#000",
  },
  link: {
    padding: 10,
    backgroundColor: "#007AFF",
    borderRadius: 8,
    marginTop: 10,
  },
  linkText: {
    color: "#fff",
    fontSize: 16,
    textAlign: "center",
  },
});
