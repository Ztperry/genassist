import { apiRequest } from "@/config/api";
import {
  EmailAgentConfig,
  EmailAgentConfigResponse,
  EmailAgentConfigDetail,
  EmailAgentHistoryResponse,
  EmailAgentTriggerResponse,
} from "@/interfaces/email-agent.interface";

const BASE = "email-agent";

export const getEmailAgentConfigs = async (): Promise<
  EmailAgentConfigResponse[]
> => {
  try {
    const data = await apiRequest<EmailAgentConfigResponse[]>(
      "GET",
      `${BASE}/configs`
    );
    if (!data || !Array.isArray(data)) {
      return [];
    }
    return data;
  } catch (error) {
    throw error;
  }
};

export const getEmailAgentConfig = async (
  dsId: string
): Promise<EmailAgentConfigDetail | null> => {
  try {
    const data = await apiRequest<EmailAgentConfigDetail>(
      "GET",
      `${BASE}/${dsId}/config`
    );
    return data ?? null;
  } catch (error) {
    throw error;
  }
};

export const updateEmailAgentConfig = async (
  dsId: string,
  config: Partial<EmailAgentConfig>
): Promise<EmailAgentConfigDetail> => {
  try {
    const response = await apiRequest<EmailAgentConfigDetail>(
      "PUT",
      `${BASE}/${dsId}/config`,
      config as unknown as Record<string, unknown>
    );
    if (!response) throw new Error("Failed to update email agent config");
    return response;
  } catch (error) {
    throw error;
  }
};

export const triggerEmailAgent = async (
  dsId: string
): Promise<EmailAgentTriggerResponse> => {
  try {
    const response = await apiRequest<EmailAgentTriggerResponse>(
      "POST",
      `${BASE}/${dsId}/trigger`
    );
    if (!response) throw new Error("Failed to trigger email agent");
    return response;
  } catch (error) {
    throw error;
  }
};

export const getEmailAgentHistory = async (
  dsId: string
): Promise<EmailAgentHistoryResponse> => {
  try {
    const data = await apiRequest<EmailAgentHistoryResponse>(
      "GET",
      `${BASE}/${dsId}/history`
    );
    if (!data) {
      return { data_source_id: dsId, data_source_name: "", history: [], count: 0 };
    }
    return data;
  } catch (error) {
    throw error;
  }
};

export const deleteEmailAgentConfig = async (
  dsId: string
): Promise<void> => {
  try {
    await apiRequest("DELETE", `${BASE}/${dsId}/config`);
  } catch (error) {
    throw error;
  }
};
