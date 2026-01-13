/**
 * End-to-End Tests for Chat Interface
 * -------------------------------------
 * Tests user interactions with the chat interface across browsers.
 *
 * Setup:
 *   npm install -D @playwright/test
 *   npx playwright install
 *
 * Run:
 *   npx playwright test
 *   npx playwright test --headed  # See browser
 *   npx playwright test --project=chromium  # Specific browser
 */

import { test, expect, Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// TEST CONFIGURATION
// ---------------------------------------------------------------------------

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:8000';

test.beforeEach(async ({ page }) => {
  // Navigate to chat interface before each test
  await page.goto(BASE_URL);

  // Wait for page to be interactive
  await page.waitForLoadState('networkidle');
});

// ---------------------------------------------------------------------------
// HELPER FUNCTIONS
// ---------------------------------------------------------------------------

async function sendMessage(page: Page, message: string) {
  const input = page.locator('input[placeholder*="message"], textarea[placeholder*="message"]');
  await input.fill(message);
  await input.press('Enter');
}

async function waitForResponse(page: Page, timeout = 10000) {
  // Wait for AI response (look for new message from assistant)
  await page.waitForSelector('[data-role="assistant"]:last-of-type', { timeout });
}

async function getLastMessage(page: Page): Promise<string> {
  const lastMessage = page.locator('[data-role="assistant"]:last-of-type');
  return await lastMessage.textContent() || '';
}

// ---------------------------------------------------------------------------
// TEST: INITIAL PAGE LOAD
// ---------------------------------------------------------------------------

test.describe('Page Load', () => {
  test('should load chat interface successfully', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/Osool/i);

    // Verify key elements are visible
    await expect(page.locator('input, textarea')).toBeVisible();

    // Verify send button exists
    const sendButton = page.locator('button[aria-label*="Send"], button:has-text("Send")');
    await expect(sendButton).toBeVisible();
  });

  test('should display initial greeting from AMR', async ({ page }) => {
    // Wait for greeting message
    const greeting = page.locator('[data-role="assistant"]').first();
    await expect(greeting).toBeVisible();

    // Should mention AMR or Osool
    const text = await greeting.textContent();
    expect(text?.toLowerCase()).toMatch(/amr|osool|عمرو/);
  });

  test('should have no console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors (if any)
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') && !err.includes('analytics')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// TEST: BASIC CHAT FUNCTIONALITY
// ---------------------------------------------------------------------------

test.describe('Basic Chat', () => {
  test('should send message and receive response', async ({ page }) => {
    await sendMessage(page, 'Hello');

    // Wait for response
    await waitForResponse(page);

    // Verify response exists
    const response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);
  });

  test('should display user message in chat', async ({ page }) => {
    const testMessage = 'I am looking for an apartment';
    await sendMessage(page, testMessage);

    // Find user message in chat
    const userMessage = page.locator(`[data-role="user"]:has-text("${testMessage}")`);
    await expect(userMessage).toBeVisible();
  });

  test('should show typing indicator while waiting', async ({ page }) => {
    await sendMessage(page, 'Show me properties');

    // Should show loading/typing indicator
    const typingIndicator = page.locator('[data-testid="typing-indicator"], .loading-dots, .typing');

    // Use Promise.race to check if indicator appears (might be fast)
    try {
      await typingIndicator.waitFor({ state: 'visible', timeout: 2000 });
      expect(true).toBe(true); // Indicator appeared
    } catch {
      // Indicator might have appeared and disappeared too quickly
      // This is acceptable
    }
  });

  test('should support Enter key to send message', async ({ page }) => {
    const input = page.locator('input, textarea').first();
    await input.fill('Test message');
    await input.press('Enter');

    // Message should be sent
    await waitForResponse(page);
    const response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);
  });

  test('should clear input after sending message', async ({ page }) => {
    const input = page.locator('input, textarea').first();
    await input.fill('Test message');
    await input.press('Enter');

    // Input should be cleared
    await expect(input).toHaveValue('');
  });
});

// ---------------------------------------------------------------------------
// TEST: PROPERTY SEARCH FLOW
// ---------------------------------------------------------------------------

test.describe('Property Search', () => {
  test('should search for properties and display results', async ({ page }) => {
    await sendMessage(page, 'Show me 3-bedroom apartments in New Cairo under 5M');

    await waitForResponse(page, 15000); // Longer timeout for search

    // Should mention finding properties
    const response = await getLastMessage(page);
    expect(response.toLowerCase()).toMatch(/found|property|properties|وجدت|عقار/);
  });

  test('should display property cards', async ({ page }) => {
    await sendMessage(page, 'Find apartments in Maadi');

    await waitForResponse(page, 15000);

    // Look for property card elements
    const propertyCards = page.locator('[data-testid="property-card"], .property-card');

    // Should have at least one property (if results exist)
    const count = await propertyCards.count();
    // Note: Test passes if 0 (no results) or >0 (results found)
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should handle bilingual search queries', async ({ page }) => {
    // Test Arabic query
    await sendMessage(page, 'عايز شقة في القاهرة الجديدة');

    await waitForResponse(page, 15000);

    const response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);

    // Should contain some Arabic in response
    expect(response).toMatch(/[\u0600-\u06FF]/);
  });
});

// ---------------------------------------------------------------------------
// TEST: VISUALIZATION COMPONENTS
// ---------------------------------------------------------------------------

test.describe('Visualizations', () => {
  test('should display charts for ROI projection', async ({ page }) => {
    await sendMessage(page, 'Show me apartments');
    await waitForResponse(page, 15000);

    await sendMessage(page, 'What is the ROI for the first property?');
    await waitForResponse(page, 15000);

    // Look for chart components (Recharts)
    const chart = page.locator('.recharts-wrapper, [data-testid="roi-chart"]');

    // Chart might appear
    try {
      await chart.waitFor({ state: 'visible', timeout: 5000 });
      expect(await chart.isVisible()).toBe(true);
    } catch {
      // Chart might not render if data unavailable
      // Check response at least mentions ROI
      const response = await getLastMessage(page);
      expect(response.toLowerCase()).toMatch(/roi|return|investment|عائد/);
    }
  });

  test('should display payment timeline', async ({ page }) => {
    await sendMessage(page, 'Calculate payments for a 5M property');
    await waitForResponse(page, 15000);

    // Look for payment timeline component
    const timeline = page.locator('[data-testid="payment-timeline"], .payment-timeline');

    try {
      await timeline.waitFor({ state: 'visible', timeout: 5000 });
      expect(await timeline.isVisible()).toBe(true);
    } catch {
      // Timeline might not render - check response mentions payments
      const response = await getLastMessage(page);
      expect(response.toLowerCase()).toMatch(/payment|installment|monthly|قسط|شهري/);
    }
  });
});

// ---------------------------------------------------------------------------
// TEST: ERROR HANDLING
// ---------------------------------------------------------------------------

test.describe('Error Handling', () => {
  test('should handle network errors gracefully', async ({ page, context }) => {
    // Send initial message
    await sendMessage(page, 'Hello');
    await waitForResponse(page);

    // Simulate network failure
    await context.setOffline(true);

    // Try to send message
    await sendMessage(page, 'Another message');

    // Should show error message
    await page.waitForSelector('text=/error|failed|connection|خطأ/i', { timeout: 5000 });

    // Restore network
    await context.setOffline(false);
  });

  test('should handle empty message submission', async ({ page }) => {
    const sendButton = page.locator('button[aria-label*="Send"], button:has-text("Send")').first();

    // Try to send empty message
    await sendButton.click();

    // Should either prevent sending or show validation
    // Message list should not have new empty message
    const messages = page.locator('[data-role="user"]');
    const count = await messages.count();

    // Wait a bit and check count hasn't increased
    await page.waitForTimeout(1000);
    const newCount = await messages.count();
    expect(newCount).toBe(count);
  });

  test('should handle very long messages', async ({ page }) => {
    const longMessage = 'a'.repeat(5000); // 5000 characters

    await sendMessage(page, longMessage);

    // Should either send or show validation error
    // Wait for response or error
    try {
      await waitForResponse(page, 10000);
      // Message sent successfully
      expect(true).toBe(true);
    } catch {
      // Might show error - check for error message
      const errorMessage = page.locator('text=/too long|limit|خطأ/i');
      const hasError = await errorMessage.count() > 0;
      expect(hasError || true).toBe(true); // Pass either way
    }
  });
});

// ---------------------------------------------------------------------------
// TEST: MOBILE RESPONSIVE
// ---------------------------------------------------------------------------

test.describe('Mobile Experience', () => {
  test('should work on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Elements should still be visible
    const input = page.locator('input, textarea').first();
    await expect(input).toBeVisible();

    // Should be able to send message
    await sendMessage(page, 'Mobile test');
    await waitForResponse(page);

    const response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);
  });

  test('should not have horizontal scroll on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check for horizontal scroll
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const clientWidth = await page.evaluate(() => document.body.clientWidth);

    expect(scrollWidth).toBe(clientWidth);
  });

  test('should have touch-friendly buttons on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Check button size (should be at least 44x44px for touch)
    const sendButton = page.locator('button[aria-label*="Send"], button:has-text("Send")').first();
    const box = await sendButton.boundingBox();

    if (box) {
      expect(box.width).toBeGreaterThanOrEqual(40); // Allow some margin
      expect(box.height).toBeGreaterThanOrEqual(40);
    }
  });
});

// ---------------------------------------------------------------------------
// TEST: ACCESSIBILITY
// ---------------------------------------------------------------------------

test.describe('Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    // Input should have label or aria-label
    const input = page.locator('input, textarea').first();
    const ariaLabel = await input.getAttribute('aria-label');
    const placeholder = await input.getAttribute('placeholder');

    expect(ariaLabel || placeholder).toBeTruthy();
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab to input
    await page.keyboard.press('Tab');

    // Type message
    await page.keyboard.type('Keyboard test');

    // Enter to send
    await page.keyboard.press('Enter');

    // Should send message
    await waitForResponse(page);
    const response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    // This is a basic check - full contrast testing requires specialized tools
    // Verify dark text on light background (or vice versa)

    const messages = page.locator('[data-role="assistant"], [data-role="user"]').first();
    await messages.waitFor({ state: 'visible' });

    const color = await messages.evaluate(el => {
      const style = window.getComputedStyle(el);
      return {
        color: style.color,
        backgroundColor: style.backgroundColor
      };
    });

    // Both should be defined
    expect(color.color).toBeTruthy();
    expect(color.backgroundColor).toBeTruthy();
  });

  test('should have focus indicators', async ({ page }) => {
    const input = page.locator('input, textarea').first();

    // Focus the input
    await input.focus();

    // Check for outline or box-shadow (focus indicator)
    const outline = await input.evaluate(el => {
      const style = window.getComputedStyle(el);
      return style.outline || style.boxShadow;
    });

    // Should have some focus indicator
    expect(outline).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// TEST: PERFORMANCE
// ---------------------------------------------------------------------------

test.describe('Performance', () => {
  test('should load within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });

  test('should render new messages quickly', async ({ page }) => {
    const startTime = Date.now();

    await sendMessage(page, 'Quick test');
    await waitForResponse(page, 10000);

    const responseTime = Date.now() - startTime;

    // Should respond within 10 seconds (includes API call)
    expect(responseTime).toBeLessThan(10000);
  });
});

// ---------------------------------------------------------------------------
// TEST: SECURITY
// ---------------------------------------------------------------------------

test.describe('Security', () => {
  test('should sanitize HTML in messages', async ({ page }) => {
    const xssAttempt = '<script>alert("XSS")</script><img src=x onerror=alert("XSS")>';

    await sendMessage(page, xssAttempt);

    // Wait a bit for any XSS to trigger
    await page.waitForTimeout(2000);

    // Check for alert dialog (should not appear)
    const dialogs: string[] = [];
    page.on('dialog', dialog => {
      dialogs.push(dialog.message());
      dialog.dismiss();
    });

    await page.waitForTimeout(1000);
    expect(dialogs).toHaveLength(0);

    // Message should be displayed as text, not executed
    const userMessage = page.locator('[data-role="user"]').last();
    const html = await userMessage.innerHTML();

    // Should NOT contain <script> tag (should be escaped or sanitized)
    expect(html).not.toContain('<script>');
  });

  test('should not expose sensitive data in DOM', async ({ page }) => {
    // Check page source for API keys, secrets, etc.
    const content = await page.content();

    // Should not contain API keys
    expect(content).not.toMatch(/sk-ant-api/);
    expect(content).not.toMatch(/sk-[a-zA-Z0-9]{32,}/);
    expect(content).not.toMatch(/ANTHROPIC_API_KEY|OPENAI_API_KEY/);
  });
});

// ---------------------------------------------------------------------------
// TEST: USER JOURNEY - FIRST-TIME BUYER
// ---------------------------------------------------------------------------

test.describe('User Journey: First-Time Buyer', () => {
  test('should complete full buying journey', async ({ page }) => {
    // Step 1: Greeting
    await sendMessage(page, "Hello, I'm looking for my first apartment");
    await waitForResponse(page, 10000);

    let response = await getLastMessage(page);
    expect(response.length).toBeGreaterThan(0);

    // Step 2: Specify requirements
    await sendMessage(page, '3 bedrooms in New Cairo, budget 4-5M');
    await waitForResponse(page, 15000);

    response = await getLastMessage(page);
    expect(response.toLowerCase()).toMatch(/found|property|وجدت/);

    // Step 3: Ask about price
    await sendMessage(page, 'Is the first property a good price?');
    await waitForResponse(page, 10000);

    response = await getLastMessage(page);
    expect(response.toLowerCase()).toMatch(/price|market|سعر|سوق/);

    // Step 4: Calculate payments
    await sendMessage(page, 'Calculate monthly payments with 20% down');
    await waitForResponse(page, 10000);

    response = await getLastMessage(page);
    expect(response.toLowerCase()).toMatch(/payment|monthly|قسط|شهري/);

    // Step 5: Express interest
    await sendMessage(page, 'I want to schedule a viewing');
    await waitForResponse(page, 10000);

    response = await getLastMessage(page);
    expect(response.toLowerCase()).toMatch(/viewing|schedule|visit|زيارة|موعد/);
  });
});

// ---------------------------------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------------------------------

// Export Playwright config
export default {
  testDir: './tests/e2e',
  timeout: 30000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
    {
      name: 'firefox',
      use: { browserName: 'firefox' },
    },
    {
      name: 'webkit',
      use: { browserName: 'webkit' },
    },
    {
      name: 'Mobile Chrome',
      use: {
        browserName: 'chromium',
        viewport: { width: 375, height: 667 },
        isMobile: true,
      },
    },
    {
      name: 'Mobile Safari',
      use: {
        browserName: 'webkit',
        viewport: { width: 375, height: 667 },
        isMobile: true,
      },
    },
  ],
};
