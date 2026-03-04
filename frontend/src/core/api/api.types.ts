export interface HealthStatus {
  status: string;
  services: {
    [key: string]: string;
  };
}
