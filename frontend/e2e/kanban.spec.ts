import { expect, test } from '@playwright/test';
import { createUser, signInThroughUi } from './helpers/api';
import { columnByName } from './helpers/board';

test('kanban journey: a dragged card is still in Done after reload (TG-02)', async ({ page }) => {
  const user = await createUser();
  const boardName = `Board ${Date.now()}`;
  const cardTitle = `Card ${Date.now()}`;

  // 1. log in
  await signInThroughUi(page, user);
  await expect(page).toHaveURL(/\/$/);

  // 2. create a board
  await page.getByRole('button', { name: '+ New Board' }).click();
  await page.getByPlaceholder('e.g. Project Alpha').fill(boardName);
  await page.getByRole('button', { name: 'Create Board', exact: true }).click();
  const boardLink = page.getByRole('link', { name: `Open board ${boardName}` });
  await expect(boardLink).toBeVisible();
  await boardLink.click();
  await expect(page).toHaveURL(/\/boards\/[0-9a-f-]+/);

  // 3 and 4. add the columns "To Do" and "Done"
  for (const columnName of ['To Do', 'Done']) {
    await page.getByRole('button', { name: '+ Add Column' }).click();
    await page.getByPlaceholder('e.g. In Progress').fill(columnName);
    await page.getByRole('button', { name: 'Add Column', exact: true }).click();
    await expect(columnByName(page, columnName)).toBeVisible();
  }

  // 5. create a card in "To Do"
  const todo = columnByName(page, 'To Do');
  const done = columnByName(page, 'Done');
  await todo.getByRole('button', { name: '+ Add Card' }).click();
  await page.locator('#card-title').fill(cardTitle);
  await page.getByRole('button', { name: 'Add Card', exact: true }).click();
  await expect(todo.getByText(cardTitle)).toBeVisible();

  // 6. drag the card to "Done"
  const moved = page.waitForResponse(
    (response) =>
      response.url().includes('/position') &&
      response.request().method() === 'PATCH' &&
      response.ok(),
  );
  await todo.getByRole('button', { name: 'Drag to reorder' }).dragTo(done);
  await moved;
  await expect(done.getByText(cardTitle)).toBeVisible();

  // 7. reload
  await page.reload();

  // 8. the card is still in "Done" and no longer in "To Do"
  await expect(columnByName(page, 'Done').getByText(cardTitle)).toBeVisible();
  await expect(columnByName(page, 'To Do').getByText(cardTitle)).toHaveCount(0);
});
