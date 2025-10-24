import { API_CONFIG } from "@/config/api";
import axios from "axios";

const apiClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: 10000,
});

export default apiClient;
