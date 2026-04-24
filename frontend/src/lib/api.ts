import axios, { AxiosError } from "axios";
import { clearStoredToken, getStoredToken } from "@/lib/session";
import type {
  AgentExecution,
  AuthResponse,
  AuthUser,
  BrowserSession,
  Campaign,
  CampaignCreateInput,
  Company,
  CompanyCreateInput,
  PaginatedResponse,
  Prospect,
  ProspectCreateInput,
  Rule,
  RuleCreateInput,
  SearchResult,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005/api";

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string | Array<{ msg?: string }> }>) => {
    const status = error.response?.status;

    if (status === 401) {
      clearStoredToken();
    }

    const detail = error.response?.data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).filter(Boolean).join(", ")
      : detail || error.message || "Request failed";

    return Promise.reject(new ApiError(message, status));
  },
);

function toParams(params: Record<string, string | number | undefined>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== undefined && value !== ""));
}

const auth = {
  async signup(email: string, password: string) {
    const response = await client.post<AuthResponse>("/auth/signup", { email, password });
    return response.data;
  },
  async login(email: string, password: string) {
    const response = await client.post<AuthResponse>("/auth/login", { email, password });
    return response.data;
  },
  async me() {
    const response = await client.get<AuthUser>("/auth/me");
    return response.data;
  },
};

const prospects = {
  async list(params: { search?: string; page: number; per_page: number }) {
    const response = await client.get<PaginatedResponse<Prospect>>("/prospects", {
      params: toParams(params),
    });
    return response.data;
  },
  async create(input: ProspectCreateInput) {
    const response = await client.post<Prospect>("/prospects", {
      ...input,
      enrichment_status: "pending",
      enrichment_confidence: 0,
    });
    return response.data;
  },
  async remove(prospectId: number) {
    await client.delete(`/prospects/${prospectId}`);
  },
};

const companies = {
  async list(params: { search?: string; page: number; per_page: number }) {
    const response = await client.get<PaginatedResponse<Company>>("/companies", {
      params: toParams(params),
    });
    return response.data;
  },
  async create(input: CompanyCreateInput) {
    const response = await client.post<Company>("/companies", input);
    return response.data;
  },
  async toggleMonitoring(companyId: number) {
    await client.post(`/companies/${companyId}/monitor`);
  },
};

const campaigns = {
  async list(params: { page: number; per_page: number }) {
    const response = await client.get<PaginatedResponse<Campaign>>("/campaigns", { params });
    return response.data;
  },
  async create(input: CampaignCreateInput) {
    const response = await client.post<Campaign>("/campaigns", input);
    return response.data;
  },
  async remove(campaignId: number) {
    await client.delete(`/campaigns/${campaignId}`);
  },
};

const enrichment = {
  async executions(params: { page: number; per_page: number }) {
    const response = await client.get<PaginatedResponse<AgentExecution>>("/enrichment/executions", {
      params,
    });
    return response.data;
  },
  async trigger(prospectId: number) {
    await client.post("/enrichment/trigger", { prospect_id: prospectId });
  },
  async triggerSearch(prospectId: number, limit = 3) {
    const response = await client.post<{ execution_id: number; prospect_id: number; status: string; message: string }>(
      "/enrichment/search-trigger",
      { prospect_id: prospectId, limit },
    );
    return response.data;
  },
};

const search = {
  async createBrowserSession(input: { query?: string; company_id?: number; limit?: number; mode?: string }) {
    const response = await client.post<BrowserSession>("/search/browser/session", input);
    return response.data;
  },
  async getBrowserSession(sessionId: string) {
    const response = await client.get<BrowserSession>(`/search/browser/session/${sessionId}`);
    return response.data;
  },
  async acceptBrowserPage(sessionId: string, input: { url: string; title: string; snippet?: string; source?: string }) {
    const response = await client.post<SearchResult>(`/search/browser/session/${sessionId}/accept-page`, input);
    return response.data;
  },
};

const rules = {
  async list(params: { page: number; per_page: number }) {
    const response = await client.get<PaginatedResponse<Rule>>("/rules", { params });
    return response.data;
  },
  async create(input: RuleCreateInput) {
    const response = await client.post<Rule>("/rules", input);
    return response.data;
  },
  async remove(ruleId: number) {
    await client.delete(`/rules/${ruleId}`);
  },
};

export default {
  auth,
  prospects,
  companies,
  campaigns,
  enrichment,
  rules,
  search,
};
