export type ApiEnvelope<T> = {
  success?: boolean;
  message?: string;
  data?: T;
  error?: {
    code?: string;
    message?: string;
    detail?: unknown;
  };
};

export class ApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;

  constructor(message: string, status: number, code?: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

let globalErrorHandler: ((error: ApiError) => void) | null = null;

export function setGlobalApiErrorHandler(handler: ((error: ApiError) => void) | null) {
  globalErrorHandler = handler;
}

function isEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  return Boolean(value) && typeof value === "object" && ("success" in (value as Record<string, unknown>) || "error" in (value as Record<string, unknown>));
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  return text ? { message: text } : null;
}

function toApiError(response: Response, payload: unknown): ApiError {
  if (isEnvelope(payload)) {
    const message = payload.error?.message || payload.message || `Request failed: ${response.status}`;
    return new ApiError(message, response.status, payload.error?.code, payload.error?.detail);
  }
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const message = String(record.detail || record.message || `Request failed: ${response.status}`);
    return new ApiError(message, response.status);
  }
  return new ApiError(`Request failed: ${response.status}`, response.status);
}

export async function apiFetch<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (error: unknown) {
    const apiError = new ApiError(
      error instanceof Error ? error.message : "Network error",
      0,
      "network_error",
      error,
    );
    globalErrorHandler?.(apiError);
    throw apiError;
  }

  const payload = await parseResponseBody(response);
  if (!response.ok) {
    const apiError = toApiError(response, payload);
    globalErrorHandler?.(apiError);
    throw apiError;
  }

  if (isEnvelope(payload)) {
    if (payload.success === false) {
      const apiError = new ApiError(
        payload.error?.message || "Request failed",
        response.status,
        payload.error?.code,
        payload.error?.detail,
      );
      globalErrorHandler?.(apiError);
      throw apiError;
    }
    return (payload.data as T) ?? (payload as T);
  }

  return payload as T;
}
