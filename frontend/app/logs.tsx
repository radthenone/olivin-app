import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from "react-native";
import { useEffect, useState } from "react";
import { useTheme } from "../config/theme";
import { platformStyles, webOnly, nativeOnly } from "../styles";
import apiClient from "../api/client";
import { API_CONFIG } from "../config/api";

interface LogsResponse {
  logs: string[];
  total_lines: number;
  showing: number;
  error?: string;
  message?: string;
}

export default function LogsScreen() {
  const theme = useTheme();
  const [logsData, setLogsData] = useState<LogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      const response = await apiClient.get<LogsResponse>(
        API_CONFIG.ENDPOINTS.LOGS
      );
      setLogsData(response.data);
      setError(null);
    } catch (err: any) {
      console.error("Error fetching logs:", err);
      if (err.response?.status === 403) {
        setError("Logs are only available in development mode.");
      } else if (err.response?.status === 404) {
        setError("Log file not found.");
      } else {
        setError("Unable to fetch logs. Please try again later.");
      }
      setLogsData(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchLogs();
  };

  const getLogLevelColor = (log: string) => {
    if (log.includes("ERROR") || log.includes("CRITICAL")) {
      return "#FF3B30";
    }
    if (log.includes("WARNING") || log.includes("WARN")) {
      return "#FF9500";
    }
    if (log.includes("INFO")) {
      return "#007AFF";
    }
    if (log.includes("DEBUG")) {
      return "#34C759";
    }
    return undefined;
  };

  if (loading) {
    return (
      <View
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading logs...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <View
          style={[
            styles.errorCard,
            platformStyles.card,
            { backgroundColor: theme.colors.card },
          ]}
        >
          <Text style={[styles.errorTitle, { color: theme.colors.error }]}>
            Error
          </Text>
          <Text style={[styles.errorText, { color: theme.colors.text }]}>
            {error}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View
        style={[
          styles.header,
          webOnly({ maxWidth: 1200, marginHorizontal: "auto" }),
        ]}
      >
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Application Logs
        </Text>
        {logsData && (
          <View style={styles.infoContainer}>
            <Text style={[styles.infoText, { color: theme.colors.text }]}>
              Showing {logsData.showing} of {logsData.total_lines} lines
            </Text>
          </View>
        )}
      </View>

      <View
        style={[
          styles.logsContainer,
          platformStyles.card,
          { backgroundColor: theme.colors.card },
          webOnly({ maxWidth: 1200, marginHorizontal: "auto" }),
        ]}
      >
        {logsData?.logs && logsData.logs.length > 0 ? (
          logsData.logs.map((log, index) => {
            const logColor = getLogLevelColor(log);
            return (
              <View key={index} style={styles.logLine}>
                <Text
                  style={[
                    styles.logText,
                    { color: logColor || theme.colors.text },
                  ]}
                >
                  {log}
                </Text>
              </View>
            );
          })
        ) : (
          <Text style={[styles.noLogsText, { color: theme.colors.text }]}>
            No logs available
          </Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    ...webOnly({
      padding: 20,
    }),
    ...nativeOnly({
      padding: 16,
    }),
  },
  contentContainer: {
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
    ...webOnly({
      paddingHorizontal: 20,
    }),
    ...nativeOnly({
      paddingHorizontal: 0,
    }),
  },
  title: {
    ...webOnly({
      fontSize: 36,
    }),
    ...nativeOnly({
      fontSize: 28,
    }),
    fontWeight: "bold",
    marginBottom: 8,
  },
  infoContainer: {
    marginTop: 8,
  },
  infoText: {
    fontSize: 14,
    opacity: 0.7,
  },
  logsContainer: {
    ...webOnly({
      padding: 20,
      borderRadius: 12,
      maxHeight: "80%",
    }),
    ...nativeOnly({
      padding: 16,
      borderRadius: 8,
      maxHeight: "75%",
    }),
  },
  logLine: {
    marginBottom: 4,
    paddingVertical: 2,
  },
  logText: {
    ...webOnly({
      fontSize: 13,
    }),
    ...nativeOnly({
      fontSize: 11,
    }),
    fontFamily: "monospace",
  },
  noLogsText: {
    fontSize: 16,
    textAlign: "center",
    padding: 32,
    opacity: 0.6,
  },
  loadingText: {
    fontSize: 16,
    textAlign: "center",
    marginTop: 32,
  },
  errorCard: {
    ...webOnly({
      padding: 24,
      borderRadius: 12,
      margin: 20,
    }),
    ...nativeOnly({
      padding: 20,
      borderRadius: 8,
      margin: 16,
    }),
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 12,
  },
  errorText: {
    fontSize: 16,
    lineHeight: 24,
  },
});
