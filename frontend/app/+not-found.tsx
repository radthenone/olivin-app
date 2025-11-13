import { View, Text, StyleSheet } from "react-native";
import { Link } from "expo-router";

export default function NotFoundScreen() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>404</Text>
            <Text style={styles.subtitle}>Page not found</Text>
            <Link href="/" style={styles.link}>
                <Text style={styles.linkText}>Go to Home</Text>
            </Link>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
    },
    title: {
        fontSize: 48,
        fontWeight: "bold",
        marginBottom: 10,
        color: "#000",
    },
    subtitle: {
        fontSize: 18,
        marginBottom: 20,
        color: "#666",
    },
    link: {
        padding: 10,
    },
    linkText: {
        fontSize: 16,
        color: "#007AFF",
        textDecorationLine: "underline",
    },
});
