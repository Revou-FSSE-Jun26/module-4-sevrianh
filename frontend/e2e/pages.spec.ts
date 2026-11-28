import { expect, test, type Page } from '@playwright/test';
import {
  createBoard,
  createCard,
  createColumn,
  createUser,
  signInWithCookie,
  type TestUser,
} from './helpers/api';
import { VIEWPORT_WIDTHS, assertNoHorizontalOverflow } from './helpers/viewport';

const PUBLIC_ROUTES = ['/register', '/login'];

async function checkAtEveryWidth(page: Page, check: () => Promise<void>): Promise<void> {
  for (const width of VIEWPORT_WIDTHS) {
    await page.setViewportSize({ width, height: 800 });
    await check();
    await assertNoHorizontalOverflow(page);
  }
}

test.describe('public pages', () => {
  for (const route of PUBLIC_ROUTES) {
    test(`${route} fits 375, 768 and 1280 px`, async ({ page }) => {
      await page.goto(route);
      await checkAtEveryWidth(page, async () => {
        await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      });
    });
  }
});

test.describe('authenticated pages', () => {
  let user: TestUser;
  let boardId: string;
  const cardTitle = 'Layout check card';

  test.beforeEach(async ({ context, baseURL }) => {
    user = await createUser();
    const board = await createBoard(user, 'Layout Board');
    boardId = board.id;
    const column = await createColumn(user, boardId, 'To Do');
    await createCard(user, column.id, cardTitle);
    await signInWithCookie(context, baseURL as string, user);
  });

  test('dashboard fits 375, 768 and 1280 px', async ({ page }) => {
    await page.goto('/');
    await checkAtEveryWidth(page, async () => {
      await expect(page.getByRole('link', { name: 'Open board Layout Board' })).toBeVisible();
    });
  });

  test('board detail fits and scrolls the board inside its own container', async ({ page }) => {
    await page.goto(`/boards/${boardId}`);
    await checkAtEveryWidth(page, async () => {
      await expect(page.getByText(cardTitle)).toBeVisible();
    });
  });

  test('card detail modal fits 375, 768 and 1280 px', async ({ page }) => {
    await page.goto(`/boards/${boardId}`);
    await page.getByText(cardTitle).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await checkAtEveryWidth(page, async () => {
      await expect(dialog).toBeVisible();
    });
  });

  test('my tasks fits 375, 768 and 1280 px', async ({ page }) => {
    await page.goto('/my-tasks');
    await checkAtEveryWidth(page, async () => {
      await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
    });
  });

  test('profile fits 375, 768 and 1280 px', async ({ page }) => {
    await page.goto('/profile');
    await checkAtEveryWidth(page, async () => {
      await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
    });
  });
});
