import { expect, test } from '@playwright/test';
import {
  createBoard,
  createInviteToken,
  createUser,
  signInThroughUi,
  signInWithCookie,
} from './helpers/api';

test.describe('authentication', () => {
  test('successful login redirects to the dashboard', async ({ page, context }) => {
    const user = await createUser();
    await signInThroughUi(page, user);

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
    await expect
      .poll(async () => (await context.cookies()).some((c) => c.name === 'sevy_token'))
      .toBe(true);
  });

  test('invalid credentials show an inline error and stay on /login', async ({ page }) => {
    const user = await createUser();
    await page.goto('/login');
    await page.locator('#email').fill(user.email);
    await page.locator('#password').fill('not-the-password');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page.getByText('Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('unauthenticated visit to a protected route redirects to /login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/profile');
    await expect(page).toHaveURL(/\/login/);
  });

  test('logout redirects to /login and clears the session cookie', async ({
    page,
    context,
    baseURL,
  }) => {
    const user = await createUser();
    await signInWithCookie(context, baseURL as string, user);
    await page.goto('/');
    await page.getByRole('button', { name: 'Log out' }).click();

    await expect(page).toHaveURL(/\/login/);
    await expect
      .poll(async () => (await context.cookies()).some((c) => c.name === 'sevy_token'))
      .toBe(false);
  });

  test('a valid invite link opens the board read-only without a login redirect', async ({
    page,
  }) => {
    const owner = await createUser();
    const board = await createBoard(owner, 'Guest Board');
    const token = await createInviteToken(owner, board.id);

    await page.goto(`/boards/${board.id}?invite=${token}`);

    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByText('Guest Board')).toBeVisible();
    await expect(page.getByRole('button', { name: '+ Add Column' })).toHaveCount(0);
  });
});
