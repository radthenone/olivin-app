/**
 * Universal logger dla React Native/Expo - standalone version.
 * Obsługuje case conversion (camelCase ↔ snake_case).
 */

export type LogLevel = "debug" | "info" | "warn" | "error" | "success";

export interface LogData {
    [key: string]: any;
}

export interface ApiRequestData {
    headers?: Record<string, string>;
    params?: Record<string, any>;
    queryParams?: Record<string, any>;
    body?: any;
    contentType?: string;
}

export interface ApiResponseData {
    headers?: Record<string, string>;
    body?: any;
    status?: number;
    duration?: number;
}

export class PackLogger {
    private isDev: boolean;
    private appName: string;

    constructor(appName: string = "pack", isDev: boolean = true) {
        this.appName = appName;
        this.isDev = isDev;
    }

    /**
     * Formatuje timestamp
     */
    private getTime(): string {
        const now = new Date();
        const timeStr = now.toLocaleTimeString("pl-PL", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
        const ms = now.getMilliseconds().toString().padStart(3, "0");
        return `${timeStr}.${ms}`;
    }

    /**
     * Główna metoda logowania
     */
    private log(level: LogLevel, message: string, data?: LogData) {
        if (!this.isDev && level !== "error") return;

        const time = this.getTime();
        const color = {
            debug: "#6B7280",
            info: "#3B82F6",
            warn: "#F59E0B",
            error: "#EF4444",
            success: "#10B981",
        }[level];

        console.group(`%c[${time}] [${this.appName}] ${message}`, `color: ${color}; font-weight: bold;`);

        if (data && Object.keys(data).length > 0) {
            console.log("%cData:", "color: #9CA3AF; font-weight: bold;");
            Object.entries(data).forEach(([key, value]) => {
                if (typeof value === "object") {
                    console.log(`  ${key}:`, JSON.stringify(value, null, 2));
                } else {
                    console.log(`  ${key}:`, value);
                }
            });
        }

        console.groupEnd();
    }

    debug(message: string, data?: LogData) {
        this.log("debug", message, data);
    }

    info(message: string, data?: LogData) {
        this.log("info", message, data);
    }

    warn(message: string, data?: LogData) {
        this.log("warn", message, data);
    }

    error(message: string, data?: LogData) {
        this.log("error", message, data);
    }

    success(message: string, data?: LogData) {
        this.log("success", message, data);
    }

    /**
     * Maskuje wrażliwe dane
     */
    private maskSensitive(data: any): any {
        if (!data || typeof data !== "object") return data;

        const sensitive = ["password", "token", "secret", "apiKey", "cardNumber", "cvv"];
        const masked = Array.isArray(data) ? [...data] : { ...data };

        for (const key in masked) {
            if (sensitive.some((s) => key.toLowerCase().includes(s.toLowerCase()))) {
                masked[key] = "***";
            } else if (typeof masked[key] === "object") {
                masked[key] = this.maskSensitive(masked[key]);
            }
        }

        return masked;
    }

    /**
     * Loguje API request z pełnymi danymi developerskimi.
     * Dane są w camelCase (frontend standard).
     */
    apiRequest(method: string, url: string, data?: ApiRequestData) {
        const logData: LogData = {};

        if (data?.headers) {
            logData.headers = this.maskSensitive(data.headers);
        }
        if (data?.params) {
            logData.params = data.params;
        }
        if (data?.queryParams) {
            logData.queryParams = data.queryParams;
        }
        if (data?.body) {
            logData.body = this.maskSensitive(data.body);
        }
        if (data?.contentType) {
            logData.contentType = data.contentType;
        }

        this.log("info", `API Request: ${method} ${url}`, logData);
    }

    /**
     * Loguje API response z pełnymi danymi developerskimi.
     * Dane są w camelCase (frontend standard).
     */
    apiResponse(method: string, url: string, status: number, duration: number, data?: ApiResponseData) {
        const level = status >= 200 && status < 300 ? "success" : status >= 500 ? "error" : "warn";

        const logData: LogData = {
            status,
            duration: `${duration}ms`,
        };

        if (data?.headers) {
            logData.headers = data.headers;
        }
        if (data?.body) {
            // Body jest już w camelCase (dzięki backend camel-case renderer)
            const body =
                Array.isArray(data.body) && data.body.length > 10
                    ? {
                          itemsCount: data.body.length,
                          firstItems: data.body.slice(0, 3),
                          message: "[Truncated - too many items]",
                      }
                    : data.body;
            logData.body = body;
        }

        this.log(level, `API Response: ${method} ${url} [${status}] ${duration}ms`, logData);
    }

    /**
     * Loguje API error z pełnymi danymi.
     */
    apiError(method: string, url: string, error: any, duration?: number, data?: ApiResponseData) {
        const logData: LogData = {
            error: error.message || error,
            status: error.response?.status,
        };

        if (duration) {
            logData.duration = `${duration}ms`;
        }

        if (data?.headers) {
            logData.headers = data.headers;
        }

        if (error.response?.data) {
            logData.responseData = error.response.data;
        }

        this.log("error", `API Error: ${method} ${url}`, logData);
    }
}

/**
 * Tworzy instancję loggera
 */
export function createLogger(appName: string = "pack", isDev: boolean = true): PackLogger {
    return new PackLogger(appName, isDev);
}
