// Content script for Bet Automation Extension

(function () {

  // Prevent duplicate evaluation
  if (window.__BET_AUTOMATION_LOADED__) {
    console.log('Bet Automation script already loaded in this frame');
    return;
  }
  window.__BET_AUTOMATION_LOADED__ = true;

  // Activation state toggled by background script
  let isActive = false;

  // Helper – check if this frame actually contains the betting UI
  function isBettingFrame() {
    return (
      document.querySelector('#leftBetTextRoot, #rightBetTextRoot') &&
      document.querySelector('button[data-testid^="chip-stack-value-"]')
    );
  }

  // Visual indicator helpers
  function hideIndicator() {
    const el = document.querySelector('[data-bet-automation-indicator]');
    if (el) el.remove();
  }

  function showIndicator() {
    hideIndicator();
    const indicator = document.createElement('div');
    indicator.setAttribute('data-bet-automation-indicator', 'true');
    indicator.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        z-index: 9999;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    indicator.textContent = 'Bet Automation Active';
    document.body.appendChild(indicator);
  }

  // Listen for bet commands from background script
  chrome.runtime.onMessage.addListener((request) => {
    switch (request.type) {
      case 'activateBetAutomation':
        isActive = true;
        if (isBettingFrame()) showIndicator();
        break;
      case 'deactivateBetAutomation':
        isActive = false;
        hideIndicator();
        break;
      case 'placeBet':
        if (isActive && isBettingFrame()) {
          placeBet(request.platform, request.amount, request.side);
        }
        break;
      case 'cancelBet':
        if (isActive && isBettingFrame()) {
          cancelBet();
        }
        break;
      default:
        break;
    }
  });

  // Function to simulate a more realistic click
  function simulateClick(element) {
    // Method 1: Try regular click first
    try {
      element.click();
    } catch (e) {}

    // Method 2: Dispatch mouse events
    try {
      const rect = element.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      // Create and dispatch mousedown event
      const mousedownEvent = new MouseEvent('mousedown', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY,
      });
      element.dispatchEvent(mousedownEvent);

      // Create and dispatch mouseup event
      const mouseupEvent = new MouseEvent('mouseup', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY,
      });
      element.dispatchEvent(mouseupEvent);

      // Create and dispatch click event
      const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY,
      });
      element.dispatchEvent(clickEvent);
    } catch (e) {}

    // Method 3: Try pointer events
    try {
      const rect = element.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const pointerdownEvent = new PointerEvent('pointerdown', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY,
        pointerId: 1,
        pointerType: 'mouse',
      });
      element.dispatchEvent(pointerdownEvent);

      const pointerupEvent = new PointerEvent('pointerup', {
        view: window,
        bubbles: true,
        cancelable: true,
        clientX: centerX,
        clientY: centerY,
        pointerId: 1,
        pointerType: 'mouse',
      });
      element.dispatchEvent(pointerupEvent);
    } catch (e) {}
  }

  // Function to find clickable element within betting area
  function findClickableElement(rootElement, side) {
    // Try different selectors based on the HTML structure
    const selectors = [
      '#leftBetText', // The text div inside
      '.so_sy', // The content wrapper
      '.so_sw', // Inner wrapper
      'svg', // The SVG element
      '.so_sr', // The SVG container
    ];

    // If it's the root element itself
    if (rootElement) {
      // Check if any child element is more suitable for clicking
      for (const selector of selectors) {
        const child = rootElement.querySelector(selector);
        if (child) {
          return child;
        }
      }
      // Return the root element if no better option found
      return rootElement;
    }
    return null;
  }

  // Function to place a bet
  async function placeBet(platform, amount, side) {
    try {
      // Ensure script active and correct frame
      if (!isActive || !isBettingFrame()) {
        return;
      }

      // Short initial wait to ensure page is ready
      await sleep(150);

      // Step 1: Try to select the chip with the exact amount
      const chipSelector = `button[data-testid="chip-stack-value-${amount}"]`;
      let chipButton = document.querySelector(chipSelector);

      // Helper to get all available chips (enabled only)
      function getAvailableChips() {
        const chipButtons = Array.from(
          document.querySelectorAll('button[data-testid^="chip-stack-value-"]'),
        ).filter((btn) => !btn.disabled && !btn.hasAttribute('disabled'));

        // Deduplicate by chip value – keep the first encountered button for each value
        const uniqueByValue = new Map();
        for (const btn of chipButtons) {
          const match = btn
            .getAttribute('data-testid')
            .match(/chip-stack-value-(\d+)/);
          if (match) {
            const value = parseInt(match[1], 10);
            if (!uniqueByValue.has(value)) {
              uniqueByValue.set(value, { value, btn });
            }
          }
        }

        return Array.from(uniqueByValue.values()).sort((a, b) => b.value - a.value); // Descending
      }

      // Helper to compose amount using available chips (dynamic programming)
      function composeChips(target, chips) {
        // dp[i] will store the combination to reach amount i, or null if not possible
        const dp = Array(target + 1).fill(null);
        dp[0] = [];
        for (let i = 1; i <= target; i++) {
          for (const chip of chips) {
            if (i - chip.value >= 0 && dp[i - chip.value] !== null) {
              dp[i] = dp[i - chip.value].concat([chip.value]);
              break; // Stop at first found (any valid solution)
            }
          }
        }
        if (!dp[target]) return null;
        // Count occurrences of each chip value
        const counts = {};
        for (const v of dp[target]) counts[v] = (counts[v] || 0) + 1;
        // Map back to chip objects and counts
        return chips
          .map(chip => counts[chip.value] ? { chip, count: counts[chip.value] } : null)
          .filter(Boolean);
      }

      let chipPlan = null;
      if (!chipButton) {
        // Try to compose the amount using available chips
        const availableChips = getAvailableChips();
        chipPlan = composeChips(amount, availableChips);
        if (!chipPlan) {
          console.error(`Cannot compose amount ${amount} with available chips.`);
          chrome.runtime.sendMessage({
            type: 'betError',
            message: `Cannot compose amount ${formatAmount(amount)} with available chips`,
            platform,
            amount,
            side,
          });
          return;
        }
        // Log the chip composition plan
        console.log(
          `[BetAutomation] Chip plan for ${amount}:`,
          chipPlan.map(({ chip, count }) => ({ value: chip.value, count })),
        );
      }

      // Step 2: Find the bet area
      let betArea;
      if (side === 'Player') {
        betArea = document.getElementById('leftBetTextRoot');
      } else if (side === 'Banker') {
        betArea = document.getElementById('rightBetTextRoot');
      }
      if (!betArea) {
        console.error(`Bet area not found for side: ${side}`);
        chrome.runtime.sendMessage({
          type: 'betError',
          message: `Bet area not found for ${side}`,
          platform,
          amount,
          side,
        });
        return;
      }

      // Step 3: Place the bet(s)
      if (chipButton) {
        // Exact chip exists, use original logic
        console.log(`[BetAutomation] About to click chip: ${amount}`);
        chipButton.click();
        await sleep(300);
        const clickTarget = findClickableElement(betArea, side);
        if (clickTarget) {
          simulateClick(clickTarget);
        } else {
          simulateClick(betArea);
        }
      } else if (chipPlan) {
        // Compose using multiple chips
        for (const { chip, count } of chipPlan) {
          // Select chip once
          console.log(`[BetAutomation] Selecting chip: ${chip.value}`);
          chip.btn.click();
          await sleep(300); // Allow UI to register selected chip

          const clickTarget = findClickableElement(betArea, side);
          for (let i = 0; i < count; i++) {
            console.log(
              `[BetAutomation] Placing chip ${chip.value} - click ${i + 1}/${count}`,
            );
            if (clickTarget) {
              simulateClick(clickTarget);
            } else {
              simulateClick(betArea);
            }
            await sleep(150); // Wait for bet to register
          }
        }
      }

      // Wait for bet to be placed
      await sleep(300);

      // Send success message back to background script
      chrome.runtime.sendMessage({
        type: 'betSuccess',
        platform: platform,
        amount: amount,
        side: side,
      });

      console.log('Bet placed successfully');
    } catch (error) {
      console.error('Error placing bet:', error);
      // Send error back to background script
      chrome.runtime.sendMessage({
        type: 'betError',
        message: `Error placing bet: ${error.message}`,
        platform: platform,
        amount: amount,
        side: side,
      });
    }
  }

  // Helper function to format amount for display
  function formatAmount(amount) {
    if (amount >= 1000000) {
      const millions = amount / 1000000;
      if (millions === Math.floor(millions)) {
        return `${millions}M`;
      }
      return `${millions.toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `${amount / 1000}K`;
    }
    return amount.toString();
  }

  // Helper function to sleep
  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // Wait for element helper
  async function waitForElement(selector, timeout = 2000, interval = 100) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const el = document.querySelector(selector);
      if (el) return el;
      await sleep(interval);
    }
    return null;
  }

  // Wait until a button becomes enabled (not disabled attribute)
  async function waitUntilEnabled(element, timeout = 2000, interval = 50) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (!element.disabled && !element.hasAttribute('disabled')) {
        return true;
      }
      await sleep(interval);
    }
    return false;
  }

  // Monitor for betting results (this would need to be customized based on the actual casino site)
  function monitorBettingResults() {
    // This is a placeholder - you would need to implement actual result detection
    // based on the specific casino platform's UI

    const observer = new MutationObserver((mutations) => {
      // Look for result notifications, win/lose indicators, etc.
      // This would be highly specific to the casino platform
    });

    // Start observing the document for changes
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
    });
  }

  // Initialize monitoring when the page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', monitorBettingResults);
  } else {
    monitorBettingResults();
  }

  // indicator-handling moved to showIndicator / hideIndicator and only when active

  // Function to cancel the last bet (best effort - selectors may need adjustment)
  async function cancelBet() {
    try {
      const selector = 'button[data-testid="undo-button"]';
      const btn = await waitForElement(selector, 2000);

      if (!btn) {
        console.warn('Undo button not found');
        return;
      }

      // Wait until button becomes enabled
      const enabled = await waitUntilEnabled(btn, 2000);
      if (!enabled) {
        console.warn('Undo button remained disabled, cannot click');
        return;
      }

      simulateClick(btn);
      console.log('Clicked undo button to cancel bet');
    } catch (err) {
      console.error('Error attempting to cancel bet:', err);
    }
  }

})();
