import { test, expect } from '@playwright/test';

test.describe('Main Page Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the page with the correct heading', async ({ page }) => {
    const heading = page.locator('h1', { hasText: 'Tech Contributions Monitor' });
    await expect(heading).toBeVisible();
  });

  test('should not have "Invalid Date" month dividers', async ({ page }) => {
    const invalidDateText = page.getByText('Invalid Date');
    await expect(invalidDateText).not.toBeVisible();
    await page.getByRole('button', { name: '🏢 Corporate PACs' }).click();
    await expect(invalidDateText).not.toBeVisible();
  });

  test.describe('Corporate PACs Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('button', { name: '🏢 Corporate PACs' }).click();
    });

    test('should display valid, summarized contributions', async ({ page }) => {
      const firstSummary = page.locator('div', { hasText: /donated .* to/ }).first();
      await expect(firstSummary).toBeVisible();

      // Check for no "undefined"
      await expect(firstSummary.getByText('undefined donated')).not.toBeVisible();

      // Check for non-zero total
      const amountSpan = firstSummary.locator('span.font-bold').first();
      await expect(amountSpan).not.toHaveText('$0');
    });

    test('should apply correct party colors', async ({ page }) => {
      const recipientSpan = page.locator('span.font-semibold', { hasText: 'TROY CARTER FOR CONGRESS' }).first();
      await expect(recipientSpan).toBeVisible();
      await expect(recipientSpan).toHaveCSS('color', 'rgb(37, 99, 235)'); // blue-600
    });

    test('should expand and collapse details', async ({ page }) => {
      const detailsButton = page.getByRole('button', { name: 'Show Details' }).first();
      await expect(detailsButton).toBeVisible();

      const detailsList = page.locator('[data-testid="details-list"]').first();
      await expect(detailsList).not.toBeVisible();

      await detailsButton.click();
      await expect(detailsList).toBeVisible();
      expect(await detailsList.locator('li').count()).toBeGreaterThan(0);

      const summaryItem = page.locator('div', { hasText: /donated .* to/ }).first();
      await summaryItem.getByRole('button', { name: 'Hide Details' }).click();
      await expect(detailsList).not.toBeVisible();
    });
  });

  test.describe('Individual Contributions Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.waitForSelector('button:has-text("👥 Executive Clusters")');
      await page.getByRole('button', { name: '👥 Executive Clusters' }).click();
    });

    test('should display valid, summarized contributions', async ({ page }) => {
      const firstSummary = page.locator('div', { hasText: /donated .* to/ }).first();
      await expect(firstSummary).toBeVisible();

      // Check for no "undefined"
      await expect(firstSummary.getByText('undefined donated')).not.toBeVisible();

      // Check for non-zero total
      const amountSpan = firstSummary.locator('span.font-bold').first();
      await expect(amountSpan).not.toHaveText('$0');
    });

    test('should expand and collapse details', async ({ page }) => {
      const detailsButton = page.getByRole('button', { name: 'Show Details' }).first();
      await expect(detailsButton).toBeVisible();

      const detailsList = page.locator('ul[role="list"]').first();
      await expect(detailsList).not.toBeVisible();

      await detailsButton.click();
      await expect(detailsList).toBeVisible();
      expect(await detailsList.locator('li').count()).toBeGreaterThan(0);

      const summaryItem = page.locator('div', { hasText: /execs/ }).first();
      await summaryItem.getByRole('button', { name: 'Hide Details' }).click();
      await expect(detailsList).not.toBeVisible();
    });
  });
});
