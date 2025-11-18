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
import { log } from "@pack/logger";

interface HealthStatus {
  status: string;
  services: {
    [key: string]: string;
  };
}

export default function HealthScreen() {
  const theme = useTheme();
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    try {
      log.info("Fetching health status", {
        endpoint: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`,
      });

      const response = await apiClient.get<HealthStatus>(
        API_CONFIG.ENDPOINTS.HEALTH
      );

      setHealthStatus(response.data);

      log.success("Health status fetched successfully", {
        status: response.data.status,
        services: Object.keys(response.data.services),
      });
    } catch (error: any) {
      log.error("Failed to fetch health status", {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      });

      // Pokaż bardziej szczegółowy błąd
      const errorMessage =
        error.response?.data?.message ||
        error.message ||
        "Unable to fetch health status";

      setHealthStatus({
        status: "error",
        services: {
          api: errorMessage,
        },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    log.debug("Health screen mounted");
    fetchHealth();
  }, []);

  const onRefresh = () => {
    log.debug("Refreshing health status");
    setRefreshing(true);
    fetchHealth();
  };

  const getStatusColor = (status: string) => {
    if (status.includes("healthy")) {
      return theme.colors.success;
    }
    if (status.includes("unhealthy") || status.includes("error")) {
      return theme.colors.error;
    }
    return theme.colors.warning;
  };

  if (loading) {
    return (
      <View
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <Text style={[styles.loadingText, { color: theme.colors.text }]}>
          Loading health status...
        </Text>
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
          webOnly({ maxWidth: 800, marginHorizontal: "auto" }),
        ]}
      >
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Health Status
        </Text>
        <View
          style={[
            styles.statusBadge,
            {
              backgroundColor: getStatusColor(
                healthStatus?.status || "unknown"
              ),
            },
          ]}
        >
          <Text style={styles.statusText}>
            {healthStatus?.status.toUpperCase() || "UNKNOWN"}
          </Text>
        </View>
      </View>

      <View
        style={[
          styles.servicesContainer,
          webOnly({ maxWidth: 800, marginHorizontal: "auto" }),
        ]}
      >
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Services
        </Text>
        {healthStatus?.services &&
          Object.entries(healthStatus.services).map(([service, status]) => {
            log.info("Service status", { service: service, status: status });
            return (
              <View
                key={service}
                style={[
                  styles.serviceCard,
                  platformStyles.card,
                  { backgroundColor: theme.colors.card },
                ]}
              >
                <View style={styles.serviceHeader}>
                  <Text
                    style={[styles.serviceName, { color: theme.colors.text }]}
                  >
                    {service.charAt(0).toUpperCase() + service.slice(1)}
                  </Text>
                  <View
                    style={[
                      styles.serviceStatusBadge,
                      {
                        backgroundColor: getStatusColor(status),
                      },
                    ]}
                  >
                    <Text style={styles.serviceStatusText}>
                      {status.includes("healthy") ? "✓" : "✗"}
                    </Text>
                  </View>
                </View>
                <Text
                  style={[styles.serviceStatus, { color: theme.colors.text }]}
                >
                  {status}
                </Text>
              </View>
            );
          })}
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
    alignItems: "center",
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
    marginBottom: 16,
  },
  statusBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  statusText: {
    color: "#FFFFFF",
    fontWeight: "bold",
    fontSize: 14,
  },
  servicesContainer: {
    width: "100%",
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "600",
    marginBottom: 16,
  },
  serviceCard: {
    ...webOnly({
      padding: 20,
      marginBottom: 16,
      borderRadius: 12,
    }),
    ...nativeOnly({
      padding: 16,
      marginBottom: 12,
      borderRadius: 8,
    }),
  },
  serviceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  serviceName: {
    ...webOnly({
      fontSize: 20,
    }),
    ...nativeOnly({
      fontSize: 18,
    }),
    fontWeight: "600",
  },
  serviceStatusBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  serviceStatusText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "bold",
  },
  serviceStatus: {
    fontSize: 14,
    opacity: 0.8,
  },
  loadingText: {
    fontSize: 16,
    textAlign: "center",
    marginTop: 32,
  },
});
