// Token gate
const storedToken = localStorage.getItem('accessToken');
if (!storedToken) {
  window.location.href = 'login.html';
}

function getUserFromToken(token) {
  try {
    return JSON.parse(atob(token.split('.')[1])).user;
  } catch (e) { return null; }
}

const currentUser = getUserFromToken(storedToken);
if (!currentUser) {
  localStorage.removeItem('accessToken');
  window.location.href = 'login.html';
}

// State management
const state = {
  platform: 'Evolution',
  firstPC: 'PC1',
  amount: null,
  side: null,
  connectedPCs: {
    PC1: false,
    PC2: false,
  },
};

// DOM elements
const platformSwitch = document.getElementById('platform-switch');
const swapBtn = document.getElementById('swap-btn');
const chipContainer = document.getElementById('chip-container');
const chipConfigBtn = document.getElementById('chip-config-btn');
const chipModal = document.getElementById('chip-selector-modal');
const chipCheckboxContainer = document.getElementById(
  'chip-checkbox-container',
);
const chipSaveBtn = document.getElementById('chip-save-btn');
const chipCancelBtn = document.getElementById('chip-cancel-btn');
const chipSummary = document.getElementById('chip-summary');
const playerBtn = document.getElementById('player-btn');
const bankerBtn = document.getElementById('banker-btn');
const placeBetBtn = document.getElementById('place-bet');
const logContainer = document.getElementById('log-container');
const pc1Status = document.getElementById('pc1-status');
const pc2Status = document.getElementById('pc2-status');
const pc1Item = document.getElementById('pc1-item');
const pc2Item = document.getElementById('pc2-item');
const selectedAmountDisplay = document.getElementById('selected-amount');
const cancelAllBtn = document.getElementById('cancel-all');
const logoutBtn = document.getElementById('logout-btn');
const adminBtn = document.getElementById('admin-btn');

if (currentUser==='admin'){
  adminBtn.style.display='inline-block';
  adminBtn.addEventListener('click',()=>{
    window.location.href='admin.html';
  });
}

const placeBetPc1Btn = document.getElementById('place-bet-pc1');
const placeBetPc2Btn = document.getElementById('place-bet-pc2');
const betBtnRow = document.querySelector('.bet-btn-row');

// Configuration
// const WS_BASE = 'wss://quality-crappie-painfully.ngrok-free.app/ws/';
const WS_BASE = 'ws://localhost:8080';

// Initialize WebSocket connection for status updates
let statusWs = null;
let reconnectTimeout = null;

function connectStatusWebSocket() {
  statusWs = new WebSocket(WS_BASE);

  statusWs.onopen = () => {
    console.log('Socket open');
    addLog('Connected to controller server', 'success');
    // Clear any reconnect timeout
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    // Authenticate
    statusWs.send(JSON.stringify({ type: 'hello', token: storedToken }));

    // Register as a status listener
    statusWs.send(
      JSON.stringify({
        type: 'registerStatusListener',
        token: storedToken,
        user: currentUser,
      }),
    );
  };

  statusWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('onmessage', data);

    if (data.type === 'status') {
      updateConnectionStatus(data.connectedPCs);
    } else if (data.type === 'betError') {
      // Show alert for bet errors
      alert(`Bet Error from ${data.pc}: ${data.message}`);
      addLog(`Bet error from ${data.pc}: ${data.message}`, 'error');
    }
  };

  statusWs.onclose = () => {
    addLog('Disconnected from controller server', 'error');
    // Reset connection status
    updateConnectionStatus({ PC1: false, PC2: false });

    // Attempt to reconnect after 3 seconds
    reconnectTimeout = setTimeout(() => {
      addLog('Attempting to reconnect...', 'info');
      connectStatusWebSocket();
    }, 3000);
  };

  statusWs.onerror = (error) => {
    addLog('WebSocket error', 'error');
  };
}

// Update connection status
function updateConnectionStatus(connectedPCs) {
  state.connectedPCs = connectedPCs;

  // Update PC1 status
  if (connectedPCs.PC1) {
    pc1Status.textContent = 'Connected';
    pc1Status.classList.add('connected');
  } else {
    pc1Status.textContent = 'Disconnected';
    pc1Status.classList.remove('connected');
  }

  // Update PC2 status
  if (connectedPCs.PC2) {
    pc2Status.textContent = 'Connected';
    pc2Status.classList.add('connected');
  } else {
    pc2Status.textContent = 'Disconnected';
    pc2Status.classList.remove('connected');
  }

  // Update bet button state
  updateBetButton();
  updateCancelAllBtn();
}

// Platform switch handler
platformSwitch.addEventListener('change', (e) => {
  state.platform = e.target.checked ? 'Pragmatic' : 'Evolution';
  addLog(`Platform switched to ${state.platform}`, 'info');
});

// Swap button handler – toggles which PC is first in betting order
swapBtn.addEventListener('click', () => {
  state.firstPC = state.firstPC === 'PC1' ? 'PC2' : 'PC1';
  addLog(`Bet order swapped: ${state.firstPC} will bet first`, 'info');
  renderPcOrder();
});

function renderPcOrder() {
  const parent = swapBtn.parentNode;
  // Remove elements to reset order
  [pc1Item, pc2Item, swapBtn].forEach((el) => {
    if (el.parentNode === parent) parent.removeChild(el);
  });

  // helper to animate
  const animate = (el) => {
    el.classList.remove('swap-animate');
    // force reflow
    void el.offsetWidth;
    el.classList.add('swap-animate');
  };

  if (state.firstPC === 'PC1') {
    parent.appendChild(pc1Item);
    parent.appendChild(swapBtn);
    parent.appendChild(pc2Item);
    // reorder single PC bet buttons
    betBtnRow.appendChild(placeBetPc1Btn);
    betBtnRow.appendChild(placeBetPc2Btn);
  } else {
    parent.appendChild(pc2Item);
    parent.appendChild(swapBtn);
    parent.appendChild(pc1Item);
    // reorder buttons
    betBtnRow.appendChild(placeBetPc2Btn);
    betBtnRow.appendChild(placeBetPc1Btn);
  }

  // animate affected elements
  [pc1Item, pc2Item, placeBetPc1Btn, placeBetPc2Btn].forEach(animate);
}

// -------------------------------------------------------------
// Chip Config

const ALL_CHIPS = [
  10, 20, 100, 200, 1000, 2000, 3000, 5000, 10000, 20000, 25000, 50000, 125000,
  250000, 500000, 1000000, 1250000, 2500000, 5000000, 10000000, 50000000,
];

let selectedChips = [
  1000, 25000, 125000, 500000, 1250000, 2500000, 5000000, 50000000,
]; // defaults

const iconAvailable = new Set([
  10, 20, 100, 200, 1000, 2000, 3000, 5000, 10000, 20000, 25000, 50000, 125000,
  250000, 500000, 1000000, 1250000, 2500000, 5000000, 10000000, 50000000,
]);

const CHIP_FILL = '#FFA41B';

function generateChipDataURI(amount) {
  const label = formatAmount(amount);
  // Estimate font-size based on label length
  const len = label.length;
  const fontSize = len <= 2 ? 400 : len === 3 ? 350 : 300;

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 1000'>
<circle cx='500' cy='500' r='499' fill='${CHIP_FILL}' />
<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' style='fill:white;font-size:${fontSize}px;font-family:Arial,sans-serif;text-shadow:0 4px 0 rgba(0,0,0,.3);'>${label}</text>
</svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function renderChips() {
  chipContainer.innerHTML = '';
  selectedChips.forEach((amt) => {
    const btn = document.createElement('button');
    btn.className = 'chip';
    btn.dataset.amount = amt;

    if (iconAvailable.has(amt)) {
      const img = document.createElement('img');
      img.src = `assets/chips/${amt}.svg`;
      img.alt = formatAmount(amt);
      btn.appendChild(img);
    } else {
      const img = document.createElement('img');
      img.alt = formatAmount(amt);
      img.src = generateChipDataURI(amt);
      btn.appendChild(img);
    }

    // Click handler
    btn.addEventListener('click', () => {
      // Remove selected class from all chips
      Array.from(chipContainer.children).forEach((c) =>
        c.classList.remove('selected'),
      );
      btn.classList.add('selected');
      state.amount = amt;
      selectedAmountDisplay.textContent = formatAmount(state.amount);
      addLog(`Amount selected: ${formatAmount(state.amount)}`, 'info');
      updateBetButton();
    });

    chipContainer.appendChild(btn);
  });

  // Update summary list
  chipSummary.textContent = `Selected Chips: ${selectedChips
    .map((a) => formatAmount(a))
    .join(', ')}`;
}

function openChipModal() {
  // Populate checkboxes
  chipCheckboxContainer.innerHTML = '';
  ALL_CHIPS.forEach((amt) => {
    const label = document.createElement('label');
    label.className = 'chip-checkbox-label';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = amt;
    checkbox.checked = selectedChips.includes(amt);

    const span = document.createElement('span');
    span.textContent = formatAmount(amt);

    // Icon
    const icon = document.createElement('img');
    icon.className = 'chip-mini';
    if (iconAvailable.has(amt)) {
      icon.src = `assets/chips/${amt}.svg`;
    } else {
      icon.src = generateChipDataURI(amt);
    }

    label.appendChild(checkbox);
    label.appendChild(icon);
    label.appendChild(span);
    chipCheckboxContainer.appendChild(label);
  });

  chipModal.classList.add('show');
}

function closeChipModal() {
  chipModal.classList.remove('show');
}

chipConfigBtn.addEventListener('click', openChipModal);
chipCancelBtn.addEventListener('click', closeChipModal);

chipSaveBtn.addEventListener('click', () => {
  // Gather selected
  const newSelected = Array.from(
    chipCheckboxContainer.querySelectorAll('input[type="checkbox"]:checked'),
  ).map((cb) => parseInt(cb.value));

  if (newSelected.length === 0) {
    alert('Please select at least one chip');
    return;
  }

  selectedChips = newSelected;
  closeChipModal();
  renderChips();
  // Reset amount if current not in new list
  if (!selectedChips.includes(state.amount)) {
    state.amount = null;
    selectedAmountDisplay.textContent = '--';
    updateBetButton();
  }
});

// Initial render
renderChips();
// -------------------------------------------------------------

// Side selection
playerBtn.addEventListener('click', () => {
  playerBtn.classList.add('selected');
  bankerBtn.classList.remove('selected');
  state.side = 'Player';
  addLog('Side selected: Player', 'info');
  updateBetButton();
});

bankerBtn.addEventListener('click', () => {
  bankerBtn.classList.add('selected');
  playerBtn.classList.remove('selected');
  state.side = 'Banker';
  addLog('Side selected: Banker', 'info');
  updateBetButton();
});

// Place bet handler
placeBetBtn.addEventListener('click', async () => {
  if (!canPlaceBet()) {
    return;
  }

  const betData = {
    platform: state.platform,
    pc: state.firstPC,
    amount: state.amount,
    side: state.side,
    user: currentUser,
  };

  try {
    const response = await fetch('/api/bet', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(betData),
    });

    const result = await response.json();

    if (result.success) {
      addLog(
        `Bet placed: ${state.firstPC} - ${formatAmount(state.amount)} on ${
          state.side
        }`,
        'success',
      );
    } else {
      addLog(`Failed to place bet: ${result.message}`, 'error');
    }
  } catch (error) {
    addLog(`Error placing bet: ${error.message}`, 'error');
  }
});

// Place bet on PC1 only
placeBetPc1Btn.addEventListener('click', async () => {
  if (!canPlaceBetSingle('PC1')) return; // order does not affect single PC bets
  const betData = {
    platform: state.platform,
    pc: 'PC1',
    amount: state.amount,
    side: state.side,
    single: true,
    user: currentUser,
  };
  try {
    const response = await fetch('/api/bet', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(betData),
    });
    const result = await response.json();
    if (result.success) {
      addLog(
        `Bet placed: PC1 - ${formatAmount(state.amount)} on ${state.side}`,
        'success',
      );
    } else {
      addLog(`Failed to place bet (PC1): ${result.message}`, 'error');
    }
  } catch (error) {
    addLog(`Error placing bet (PC1): ${error.message}`, 'error');
  }
});

// Place bet on PC2 only
placeBetPc2Btn.addEventListener('click', async () => {
  if (!canPlaceBetSingle('PC2')) return;
  const betData = {
    platform: state.platform,
    pc: 'PC2',
    amount: state.amount,
    side: state.side,
    single: true,
    user: currentUser,
  };
  try {
    const response = await fetch('/api/bet', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(betData),
    });
    const result = await response.json();
    if (result.success) {
      addLog(
        `Bet placed: PC2 - ${formatAmount(state.amount)} on ${state.side}`,
        'success',
      );
    } else {
      addLog(`Failed to place bet (PC2): ${result.message}`, 'error');
    }
  } catch (error) {
    addLog(`Error placing bet (PC2): ${error.message}`, 'error');
  }
});

function canPlaceBet() {
  // Require both PCs to be connected
  return (
    state.amount &&
    state.side &&
    state.connectedPCs.PC1 &&
    state.connectedPCs.PC2
  );
}

function canPlaceBetSingle(pc) {
  return (
    state.amount &&
    state.side &&
    state.connectedPCs[pc]
  );
}

// Update bet button state
function updateBetButton() {
  if (canPlaceBet()) {
    placeBetBtn.disabled = false;
    placeBetBtn.textContent = 'Place Bet';
  } else {
    placeBetBtn.disabled = true;

    if (!state.amount) {
      placeBetBtn.textContent = 'Select Amount';
    } else if (!state.side) {
      placeBetBtn.textContent = 'Select Side';
    } else if (!state.connectedPCs.PC1 || !state.connectedPCs.PC2) {
      placeBetBtn.textContent = 'Both PCs Must Be Connected';
    }
  }
  // Update single PC bet buttons
  placeBetPc1Btn.disabled = !canPlaceBetSingle('PC1');
  placeBetPc2Btn.disabled = !canPlaceBetSingle('PC2');
}

// Format amount for display
function formatAmount(amount) {
  if (amount >= 1000000) {
    const millions = amount / 1000000;
    // If it's a whole number, don't show decimals
    if (millions === Math.floor(millions)) {
      return `${millions}M`;
    }
    // Otherwise show one decimal place
    return `${millions.toFixed(2).replace(/\.?0+$/, '')}M`;
  } else if (amount >= 1000) {
    return `${amount / 1000}K`;
  }
  return amount.toString();
}

// Add log entry
function addLog(message, type = 'info') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;

  const timestamp = new Date().toLocaleTimeString();
  entry.textContent = `[${timestamp}] ${message}`;

  logContainer.insertBefore(entry, logContainer.firstChild);

  // Keep only last 50 entries
  while (logContainer.children.length > 50) {
    logContainer.removeChild(logContainer.lastChild);
  }
}

// Initialize
connectStatusWebSocket();
updateBetButton();
updateCancelAllBtn();

// Render initial PC order
renderPcOrder();

// Initialize selected amount display
selectedAmountDisplay.textContent = '--';

// Initial log
addLog('Controller initialized', 'success');

// Cancel all bets handler
cancelAllBtn.addEventListener('click', async () => {
  try {
    const response = await fetch('/api/cancelBetAll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: currentUser }),
    });
    const result = await response.json();
    if (result.success) {
      addLog('Cancel bet command sent to both PCs', 'success');
    } else {
      addLog(`Failed to cancel bets: ${result.message}`, 'error');
    }
  } catch (err) {
    addLog(`Error sending cancel: ${err.message}`, 'error');
  }
});

function updateCancelAllBtn() {
  cancelAllBtn.disabled = !(state.connectedPCs.PC1 || state.connectedPCs.PC2);
}

logoutBtn.addEventListener('click', () => {
  localStorage.removeItem('accessToken');
  window.location.href = 'login.html';
});
