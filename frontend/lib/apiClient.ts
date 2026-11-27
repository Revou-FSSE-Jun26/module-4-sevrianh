import { ApiError } from '@/lib/errors';

export interface RequestOptions {
  /** JWT, sent as a Bearer token unless `inviteToken` is set (Guest mode). */
  token?: string | null;
  /** Invite token (Guest mode, FE-30). */
  inviteToken?: string | null;
}

type Method = 'GET' | 'POST' | 'PATCH' | 'DELETE';

const INVITE_HEADER = 'X-Invite-Token';
const GUEST_READ_PATHS = [/^\/api\/boards\/[^/]+$/, /^\/api\/cards\/[^/]+\/comments$/];

function getBaseUrl(): string {
  const server = process.env.API_BASE_URL;
  const browser = process.env.NEXT_PUBLIC_API_BASE_URL;
  const base = typeof window === 'undefined' ? (server ?? browser) : (browser ?? server);
  return (base ?? '').replace(/\/+$/, '');
}

function isGuestReadRequest(method: Method, path: string): boolean {
  if (method !== 'GET') return false;
  const pathname = path.split('?')[0];
  return GUEST_READ_PATHS.some((pattern) => pattern.test(pathname));
}

function buildHeaders(method: Method, path: string, body: unknown, opts: RequestOptions) {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (opts.inviteToken) {
    if (isGuestReadRequest(method, path)) headers[INVITE_HEADER] = opts.inviteToken;
  } else if (opts.token) {
    headers.Authorization = `Bearer ${opts.token}`;
  }
  return headers;
}

async function readBody(res: Response): Promise<Record<string, unknown> | null> {
  try {
    const parsed: unknown = await res.json();
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

async function request<T>(
  method: Method,
  path: string,
  body?: unknown,
  opts: RequestOptions = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${getBaseUrl()}${path}`, {
      method,
      headers: buildHeaders(method, path, body, opts),
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    });
  } catch {
    throw new ApiError(0, 'Network error');
  }

  const payload = await readBody(res);
  if (!res.ok) {
    const message = typeof payload?.error === 'string' ? payload.error : 'Request failed';
    throw new ApiError(res.status, message);
  }
  return (payload?.data ?? null) as T;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) => request<T>('GET', path, undefined, opts),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>('POST', path, body ?? {}, opts),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>('PATCH', path, body ?? {}, opts),
  delete: <T>(path: string, opts?: RequestOptions) => request<T>('DELETE', path, undefined, opts),
};
