import { randomUUID } from 'node:crypto';
import type { BrowserContext, Page } from '@playwright/test';

const API_BASE_URL =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:5000';

export const PASSWORD = 'Passw0rd!e2e';

export interface TestUser {
  id: string;
  name: string;
  username: string;
  email: string;
  password: string;
  token: string;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = (await response.json()) as { data?: T; error?: string };
  if (!response.ok || payload.data === undefined) {
    throw new Error(`${method} ${path} failed: ${response.status} ${payload.error ?? ''}`);
  }
  return payload.data;
}

/** Creates a user through the API with a unique email and username (TC-19). */
export async function createUser(): Promise<TestUser> {
  const suffix = randomUUID().replace(/-/g, '').slice(0, 20);
  const username = `e2e_${suffix}`;
  const email = `${username}@example.com`;
  const name = `E2E ${suffix.slice(0, 6)}`;
  await request('POST', '/api/auth/register', { name, username, email, password: PASSWORD });
  const login = await request<{ access_token: string; user: { id: string } }>(
    'POST',
    '/api/auth/login',
    { email, password: PASSWORD },
  );
  return {
    id: login.user.id,
    name,
    username,
    email,
    password: PASSWORD,
    token: login.access_token,
  };
}

export function createBoard(user: TestUser, name: string): Promise<{ id: string; name: string }> {
  return request('POST', '/api/boards', { name }, user.token);
}

export function createColumn(
  user: TestUser,
  boardId: string,
  name: string,
): Promise<{ id: string; name: string }> {
  return request('POST', `/api/boards/${boardId}/columns`, { name }, user.token);
}

export function createCard(
  user: TestUser,
  columnId: string,
  title: string,
): Promise<{ id: string; title: string }> {
  return request('POST', `/api/columns/${columnId}/cards`, { title }, user.token);
}

export async function createInviteToken(user: TestUser, boardId: string): Promise<string> {
  const link = await request<{ token: string }>(
    'POST',
    `/api/boards/${boardId}/invite-links`,
    {},
    user.token,
  );
  return link.token;
}

/** Signs in without the UI by setting the `sevy_token` cookie (FE-22). */
export async function signInWithCookie(
  context: BrowserContext,
  baseURL: string,
  user: TestUser,
): Promise<void> {
  await context.addCookies([{ name: 'sevy_token', value: user.token, url: baseURL }]);
}

export async function signInThroughUi(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  await page.locator('#email').fill(user.email);
  await page.locator('#password').fill(user.password);
  await page.getByRole('button', { name: 'Log in' }).click();
}
