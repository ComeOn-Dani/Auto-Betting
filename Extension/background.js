// Background service worker for Bet Automation Extension

const WS_URL = 'wss://quality-crappie-painfully.ngrok-free.app/ws/';

let ws = null;
let reconnectInterval = null;
let pcName = null; // Will be assigned by server (PC1 or PC2)
let isConnected = false;
let isConnecting = false;
let watchdog = null;
let watchdogInterval = null;
let lastServerMsg = Date.now();
const WATCHDOG_INTERVAL = 15000; // 15 seconds

// Helper: broadcast a runtime message to all tabs (best-effort)
async function broadcastToAllTabs(msg) {
  try {
    const tabs = await chrome.tabs.query({});
    for (const tab of tabs) {
      if (tab.id != null) {
        chrome.tabs.sendMessage(tab.id, msg).catch(() => {});
      }
    }
  } catch (err) {
    console.error('broadcastToAllTabs error', err);
  }
}

// Update extension icon based on connection status
function updateIcon(connected) {
  const iconPath = connected
    ? 'icons/recording.png'
    : 'icons/not-recording.png';
  chrome.action.setIcon({ path: iconPath });
}

// Reload content scripts in all tabs
async function reloadContentScripts() {
  try {
    // Get all tabs
    const tabs = await chrome.tabs.query({});

    for (const tab of tabs) {
      // Skip chrome:// and other special URLs
      if (
        tab.url &&
        (tab.url.startsWith('http://') || tab.url.startsWith('https://'))
      ) {
        try {
          // Remove existing content script if any
          await chrome.scripting.executeScript({
            target: { tabId: tab.id, allFrames: true },
            func: () => {
              // Remove any existing indicators
              const existingIndicator = document.querySelector(
                '[data-bet-automation-indicator]',
              );
              if (existingIndicator) {
                existingIndicator.remove();
              }
            },
          });

          // Inject content script into all frames
          await chrome.scripting.executeScript({
            target: { tabId: tab.id, allFrames: true },
            files: ['content.js'],
          });

          console.log(`Reloaded content script in tab: ${tab.title}`);
        } catch (err) {
          console.log(
            `Failed to reload content script in tab ${tab.id}:`,
            err.message,
          );
        }
      }
    }
  } catch (error) {
    console.error('Error reloading content scripts:', error);
  }
}

// Disconnect from WebSocket
async function disconnect() {
  if (reconnectInterval) {
    clearInterval(reconnectInterval);
    reconnectInterval = null;
  }

  if (ws) {
    ws.close();
    ws = null;
  }

  isConnected = false;
  isConnecting = false;
  pcName = null;
  updateIcon(false);

  // Inform content scripts to deactivate
  await broadcastToAllTabs({ type: 'deactivateBetAutomation' });

  // Clear stored PC name
  chrome.storage.local.remove('pcName');
}

// Initialize WebSocket connection
function connectWebSocket() {
  if (isConnecting || isConnected) {
    return;
  }

  isConnecting = true;
  ws = new WebSocket(WS_URL);

  ws.onopen = async () => {
    console.log('Connected to controller server');
    clearInterval(reconnectInterval);
    reconnectInterval = null;
    isConnected = true;
    isConnecting = false;

    // Reload content scripts in all tabs
    await reloadContentScripts();

    // Tell content scripts to activate
    await broadcastToAllTabs({ type: 'activateBetAutomation' });

    // Request PC assignment from server
    ws.send(
      JSON.stringify({
        type: 'requestAssignment',
      }),
    );

    // Update icon to recording.png (connected)
    updateIcon(true);

    lastServerMsg = Date.now();
    startWatchdog();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received message:', data);

    // heartbeat
    if (data.type === 'ping') {
      lastServerMsg = Date.now();
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'pong' }));
      }
      return;
    }
    lastServerMsg = Date.now();

    if (data.type === 'assignment') {
      // Server assigned us a PC name (PC1 or PC2)
      pcName = data.pc;
      chrome.storage.local.set({ pcName: pcName });

      // Register with the assigned PC name
      ws.send(
        JSON.stringify({
          type: 'register',
          pc: pcName,
        }),
      );

      console.log(`This extension is assigned as: ${pcName}`);
    } else if (data.type === 'placeBet') {
      // Forward bet command to content script
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs
            .sendMessage(tabs[0].id, {
              type: 'placeBet',
              platform: data.platform,
              amount: data.amount,
              side: data.side,
            })
            .catch((err) => {
              console.error('Failed to send message to content script:', err);
              // Try to reinject content script and retry
              chrome.scripting
                .executeScript({
                  target: { tabId: tabs[0].id },
                  files: ['content.js'],
                })
                .then(() => {
                  // Retry sending the message after a short delay
                  setTimeout(() => {
                    chrome.tabs.sendMessage(tabs[0].id, {
                      type: 'placeBet',
                      platform: data.platform,
                      amount: data.amount,
                      side: data.side,
                    });
                  }, 100);
                });
            });
        }
      });
    } else if (data.type === 'cancelBet') {
      // Forward cancel command to content script
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, {
            type: 'cancelBet',
            platform: data.platform,
            amount: data.amount,
            side: data.side,
          });
        }
      });
    } else if (data.type === 'error') {
      // Handle error (e.g., both PC slots occupied)
      console.error('Server error:', data.message);
      alert(data.message);
      disconnect();
    }
  };

  ws.onclose = () => {
    console.log('Disconnected from controller server');
    const wasConnected = isConnected;
    isConnected = false;
    isConnecting = false;
    pcName = null;

    // Update icon to not-recording.png (disconnected)
    updateIcon(false);

    // Broadcast deactivation (fire-and-forget)
    broadcastToAllTabs({ type: 'deactivateBetAutomation' });

    // Clear stored PC name
    chrome.storage.local.remove('pcName');

    // Only attempt to reconnect if we were connected and didn't manually disconnect
    if (wasConnected && !reconnectInterval) {
      reconnectInterval = setInterval(() => {
        console.log('Connection lost, attempting to reconnect...');
        connectWebSocket();
      }, 3000);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    isConnecting = false;
  };
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'betSuccess') {
    // Forward success message to controller
    if (ws && ws.readyState === WebSocket.OPEN && pcName) {
      ws.send(
        JSON.stringify({
          type: 'betSuccess',
          pc: pcName,
          platform: request.platform,
          amount: request.amount,
          side: request.side,
        }),
      );
    }
  } else if (request.type === 'betError') {
    // Forward error message to controller
    if (ws && ws.readyState === WebSocket.OPEN && pcName) {
      ws.send(
        JSON.stringify({
          type: 'betError',
          pc: pcName,
          message: request.message,
          platform: request.platform,
          amount: request.amount,
          side: request.side,
        }),
      );
    }
  } else if (request.type === 'getConnectionStatus') {
    sendResponse({
      connected: isConnected,
      pcName: pcName,
    });
    return true; // Keep message channel open for async response
  }
});

// Handle extension icon click - toggle connection
chrome.action.onClicked.addListener(() => {
  if (isConnected) {
    // Disconnect when icon is clicked while connected
    console.log('Icon clicked - disconnecting from server...');
    disconnect();
  } else {
    // Connect when icon is clicked while disconnected
    console.log('Icon clicked - connecting to server...');
    connectWebSocket();
  }
});

// Initialize with not-recording.png icon
updateIcon(false);

function startWatchdog() {
  if (watchdogInterval) return;
  watchdogInterval = setInterval(() => {
    if (isConnected && Date.now() - lastServerMsg > WATCHDOG_INTERVAL) {
      console.warn('Watchdog: No ping from server, closing socket');
      if (ws) ws.close();
    }
  }, WATCHDOG_INTERVAL);
}

// Inject content script into any tab that finishes loading while connected
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (!isConnected) return;
  if (changeInfo.status === 'complete' && tab.url && (tab.url.startsWith('http://') || tab.url.startsWith('https://'))) {
    chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['content.js'] })
      .then(() => {
        chrome.tabs.sendMessage(tabId, { type: 'activateBetAutomation' }).catch(() => {});
      })
      .catch(() => {});
  }
});
