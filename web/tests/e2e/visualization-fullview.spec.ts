import { expect, test } from '@playwright/test';

const streamEventBody = [
  'data: {"type":"token","content":"Here is a market snapshot with visualization."}',
  `data: ${JSON.stringify({
    type: 'done',
    properties: [],
    ui_actions: [
      {
        type: 'data_table',
        data: {
          title: 'Market Benchmark',
          subtitle: 'Deterministic test payload',
          columns: [
            { key: 'area', label: 'Area' },
            { key: 'avg_price', label: 'Avg Price/m²' },
          ],
          data: [
            { area: 'New Cairo', avg_price: '45,000 EGP' },
            { area: 'Sheikh Zayed', avg_price: '64,000 EGP' },
          ],
        },
      },
    ],
    suggestions: [],
    lead_score: 0,
    readiness_score: 0,
    detected_language: 'en',
    showing_strategy: 'NONE',
  })}`,
  '',
].join('\n\n');

test.describe('Visualization fullscreen (mobile)', () => {
  test('opens and closes full view from maximize button', async ({ page }) => {
    await page.route('**/api/chat/stream', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue();
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        headers: {
          'cache-control': 'no-cache',
        },
        body: streamEventBody,
      });
    });

    await page.goto('/chat');
    await page.waitForLoadState('domcontentloaded');

    const input = page.locator('textarea').first();
    await expect(input).toBeVisible();

    await input.fill('Show me a market benchmark');
    await page.getByRole('button', { name: /send message|إرسال الرسالة/i }).first().click();

    const maximizeButton = page.getByTestId('viz-maximize').first();
    await expect(maximizeButton).toBeVisible({ timeout: 15_000 });

    await maximizeButton.click();

    const fullscreenCloseButton = page.getByTestId('viz-fullscreen-close');
    await expect(fullscreenCloseButton).toBeVisible();
    await expect
      .poll(async () => page.evaluate(() => document.body.style.overflow))
      .toBe('hidden');

    await fullscreenCloseButton.click();

    await expect(fullscreenCloseButton).toHaveCount(0);
    await expect
      .poll(async () => page.evaluate(() => document.body.style.overflow))
      .not.toBe('hidden');
  });
});
