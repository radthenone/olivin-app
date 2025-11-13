import { View, Text, StyleSheet } from "react-native";

export default function CategoriesScreen() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Categories</Text>
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
        fontSize: 24,
        fontWeight: "bold",
        color: "#000",
    },
});
