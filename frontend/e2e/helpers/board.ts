import type { Locator, Page } from '@playwright/test';

/** The Kanban column whose `<h3>` heading reads `<name>(<card count>)`. */
export function columnByName(page: Page, name: string): Locator {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return page
    .getByRole('heading', { level: 3, name: new RegExp(`^${escaped}\\s*\\(\\d+\\)$`) })
    .locator("xpath=ancestor::div[contains(@class,'w-72')][1]");
}
