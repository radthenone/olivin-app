import React, { useEffect, useState } from "react";
import { View, Text, ScrollView, RefreshControl } from "react-native";
import { cn, ps } from "lib";
import { useTheme } from "../src/core/theme/theme";
import apiClient from "src/core/api/client";
import { log } from "@pack/logger";
import { ENDPOINTS } from "src/core/api/endpoints";
import { HealthStatus } from "src/core/api/api.types";

async function fetchHealth(): Promise<HealthStatus> {
  try {
    const response = await apiClient.get<HealthStatus>(ENDPOINTS.HEALTH);
    log.info("Health status fetched successfully", { data: response.data });
    return response.data;
  } catch (error: any) {
    const errorMessage =
      error.response?.data?.message ||
      error.message ||
      "Unable to fetch health status";

    log.error(errorMessage, { error });

    return {
      status: "error",
      services: { api: errorMessage },
    };
  }
}

export default function HealthScreen() {
  const theme = useTheme();
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    try {
      log.info("Fetching health status", { endpoint: ENDPOINTS.HEALTH });
      const response = await apiClient.get<HealthStatus>(ENDPOINTS.HEALTH);
      setHealthStatus(response.data);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.message ||
        error.message ||
        "Unable to fetch health status";

      setHealthStatus({
        status: "error",
        services: { api: errorMessage },
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  const getStatusColor = (status: string) => {
    if (status.includes("healthy")) return theme.colors.success;
    if (status.includes("unhealthy") || status.includes("error"))
      return theme.colors.error;
    return theme.colors.warning;
  };

  if (loading) {
    return (
      <View
        className={cn("flex-1", ps({ web: "p-5", native: "p-4" }))}
        style={{ backgroundColor: theme.colors.background }}
      >
        <Text
          className="text-base text-center mt-8"
          style={{ color: theme.colors.text }}
        >
          Loading health status...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      className={cn("flex-1", ps({ web: "p-5", native: "p-4" }))}
      style={{ backgroundColor: theme.colors.background }}
      contentContainerClassName="pb-8"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View
        className={cn(
          "mb-6 items-center",
          ps({
            web: "max-w-[800px] mx-auto px-5",
            native: "px-0",
          }),
        )}
      >
        <Text
          className={cn(
            "font-bold mb-4",
            ps({ web: "text-4xl", native: "text-3xl" }),
          )}
          style={{ color: theme.colors.text }}
        >
          Health Status
        </Text>

        <View
          className="px-4 py-2 rounded-full"
          style={{
            backgroundColor: getStatusColor(healthStatus?.status || "unknown"),
          }}
        >
          <Text className="text-white font-bold text-sm">
            {healthStatus?.status.toUpperCase() || "UNKNOWN"}
          </Text>
        </View>
      </View>

      {/* Services */}
      <View className={cn("w-full", ps({ web: "max-w-[800px] mx-auto" }))}>
        <Text
          className="text-xl font-semibold mb-4"
          style={{ color: theme.colors.text }}
        >
          Services
        </Text>

        {healthStatus?.services &&
          Object.entries(healthStatus.services).map(([service, status]) => (
            <View
              key={service}
              className={cn(
                ps({
                  web: "p-5 mb-4 rounded-xl",
                  native: "p-4 mb-3 rounded-lg",
                }),
              )}
              style={{ backgroundColor: theme.colors.card }}
            >
              <View className="flex-row justify-between items-center mb-2">
                <Text
                  className={cn(
                    "font-semibold",
                    ps({ web: "text-xl", native: "text-lg" }),
                  )}
                  style={{ color: theme.colors.text }}
                >
                  {service.charAt(0).toUpperCase() + service.slice(1)}
                </Text>

                <View
                  className="w-6 h-6 rounded-full items-center justify-center"
                  style={{ backgroundColor: getStatusColor(status) }}
                >
                  <Text className="text-white text-xs font-bold">
                    {status.includes("healthy") ? "✓" : "✗"}
                  </Text>
                </View>
              </View>

              <Text
                className="text-sm opacity-80"
                style={{ color: theme.colors.text }}
              >
                {status}
              </Text>
            </View>
          ))}
      </View>
    </ScrollView>
  );
}
