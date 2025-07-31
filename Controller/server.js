const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const path = require('path');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const fs = require('fs');

// Load users
const USERS_FILE = path.join(__dirname, 'users.json');
let USERS = JSON.parse(fs.readFileSync(USERS_FILE, 'utf8'));

function saveUsers() {
  fs.writeFileSync(USERS_FILE, JSON.stringify(USERS, null, 2), 'utf8');
}

function authAdmin(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) return res.status(401).json({ success: false, message: 'Missing token' });
  const token = authHeader.split(' ')[1];
  const payload = verifyToken(token);
  if (!payload || payload.user !== 'admin') {
    return res.status(403).json({ success: false, message: 'Admin only' });
  }
  req.authUser = payload.user;
  next();
}

const JWT_SECRET = process.env.JWT_SECRET || 'INSECURE_DEV_SECRET_CHANGE_ME';

function generateAccessToken(user) {
  return jwt.sign({ user }, JWT_SECRET, { expiresIn: '1h' });
}

function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    return null;
  }
}

const app = express();
const PORT = 3000;
const WS_PORT = 8080;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Redirect root to login page to avoid loading controller without auth
app.get('/', (req, res) => {
  res.redirect('/login.html');
});

// WebSocket server
const wss = new WebSocket.Server({ port: WS_PORT });

// Store connected clients
const clients = new Map();
const assignedPCs = new Set(); // Track which PC names are assigned
const statusListeners = new Set(); // Track connections that want status updates
const HEARTBEAT_INTERVAL = 10000; // 10 seconds

// New: room structure per user
const rooms = new Map(); // user -> {clients,map}

function getRoom(user) {
  if (!rooms.has(user)) {
    rooms.set(user, {
      clients: new Map(), // clientId -> clientData
      assignedPCs: new Set(),
      statusListeners: new Set(),
    });
  }
  return rooms.get(user);
}

// WebSocket connection handler
wss.on('connection', (ws, req) => {
  console.log('New WebSocket connection');

  // Generate unique client ID
  const clientId = Date.now().toString();

  let room = null;
  let clientUser = null;

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log('Received:', data);

      // Auth gate: expect first message type hello with token
      if (!clientUser) {
        if (data.type !== 'hello' || !data.token) {
          ws.close();
          return;
        }
        const payload = verifyToken(data.token);
        if (!payload) {
          ws.send(JSON.stringify({ type: 'error', message: 'Invalid token' }));
          ws.close();
          return;
        }
        clientUser = payload.user;
        room = getRoom(clientUser);
        // proceed; do not process further this initial hello
        return;
      }

      // Handle pong from client for heartbeat
      if (data.type === 'pong') {
        if (room && room.clients.has(clientId)) {
          room.clients.get(clientId).isAlive = true;
        }
        return; // no further processing
      }

      // Handle status listener registration
      if (data.type === 'registerStatusListener') {
        if (!room) return;
        room.statusListeners.add(ws);
        console.log('Registered status listener');
        // Send current status immediately
        sendStatusToClientRoom(ws, room);
      }

      // Handle PC assignment request
      if (data.type === 'requestAssignment') {
        let assignedPC = null;

        // Assign PC1 if available, otherwise PC2 within room
        if (!room.assignedPCs.has('PC1')) {
          assignedPC = 'PC1';
        } else if (!room.assignedPCs.has('PC2')) {
          assignedPC = 'PC2';
        } else {
          // Both PCs are taken
          ws.send(
            JSON.stringify({
              type: 'error',
              message: 'Both PC slots are occupied' + JSON.stringify(room),
            }),
          );
          ws.close();
          return;
        }

        // Mark PC as assigned; store on ws in case registration never arrives
        room.assignedPCs.add(assignedPC);
        ws.tempAssignedPC = assignedPC;

        // Send assignment to client
        ws.send(
          JSON.stringify({
            type: 'assignment',
            pc: assignedPC,
          }),
        );

        console.log(`Assigned ${assignedPC} to client ${clientId}`);
        broadcastStatus(room);
      }

      // Handle client registration
      if (data.type === 'register') {
        room.clients.set(clientId, {
          ws: ws,
          pc: data.pc,
          id: clientId,
          isAlive: true,
        });

        ws.send(
          JSON.stringify({
            type: 'registered',
            clientId: clientId,
            pc: data.pc,
          }),
        );

        console.log(`${data.pc} registered`);
        broadcastStatus(room);
        // registration complete; clear provisional flag
        delete ws.tempAssignedPC;
      }

      // Handle bet error
      if (data.type === 'betError') {
        console.log(`Bet error from ${data.pc}:`, data.message);

        // Broadcast error to all status listeners
        room.statusListeners.forEach((listener) => {
          if (listener.readyState === WebSocket.OPEN) {
            listener.send(
              JSON.stringify({
                type: 'betError',
                pc: data.pc,
                message: data.message,
                platform: data.platform,
                amount: data.amount,
                side: data.side,
              }),
            );
          }
        });

        // Cancel the opposite PC's bet if already sent
        const oppositePC = data.pc === 'PC1' ? 'PC2' : 'PC1';
        sendCancelBet(oppositePC, data.platform, data.amount, data.side, room);
      }

      // Handle bet success
      if (data.type === 'betSuccess') {
        console.log(`Bet success from ${data.pc}:`, data);
        // No further action required – bets are now sent simultaneously
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');

    // Remove from status listeners if present
    if (room) room.statusListeners.delete(ws);

    // Find and remove the client
    if (room) {
      for (const [id, client] of room.clients.entries()) {
        if (client.ws === ws) {
          // Free up the PC assignment
          if (client.pc) {
            room.assignedPCs.delete(client.pc);
            console.log(`Freed up ${client.pc}`);
          }
          room.clients.delete(id);
          break;
        }
      }
      // handle provisional assigned pc that never registered
      if (ws.tempAssignedPC) {
        room.assignedPCs.delete(ws.tempAssignedPC);
      }
    }
    broadcastStatus(room);
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Send status to a specific client
function sendStatusToClientRoom(ws, room) {
  if (!room) return;
  const status = {
    PC1: false,
    PC2: false,
  };

  room.clients.forEach((client) => {
    if (client.ws.readyState === WebSocket.OPEN) {
      status[client.pc] = true;
    }
  });

  if (ws.readyState === WebSocket.OPEN) {
    ws.send(
      JSON.stringify({
        type: 'status',
        connectedPCs: status,
      }),
    );
  }
}

// Broadcast connected PCs status to all listeners
function broadcastStatus(room) {
  if (!room) return;
  const status = {
    PC1: false,
    PC2: false,
  };

  room.clients.forEach((client) => {
    if (client.ws.readyState === WebSocket.OPEN) {
      status[client.pc] = true;
    }
  });

  console.log('Broadcasting status:', status);

  // Send status to all registered status listeners
  room.statusListeners.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({
          type: 'status',
          connectedPCs: status,
        }),
      );
    }
  });

  // Also send to all PC clients for backward compatibility
  room.clients.forEach((client) => {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(
        JSON.stringify({
          type: 'status',
          connectedPCs: status,
        }),
      );
    }
  });
}

// Ping loop to ensure connections are alive
setInterval(() => {
  rooms.forEach((room, user) => {
    room.clients.forEach((client, id) => {
      if (client.ws.readyState !== WebSocket.OPEN) return;

      if (client.isAlive === false) {
        console.log(`Heartbeat missed from ${client.pc}, terminating connection`);
        client.ws.terminate();
        room.clients.delete(id);
        room.assignedPCs.delete(client.pc);
        broadcastStatus(room);
        return;
      }

      client.isAlive = false; // will be set true on pong
      try {
        client.ws.send(JSON.stringify({ type: 'ping' }));
      } catch (err) {
        console.error('Failed to send ping', err);
      }
    });
  });
}, HEARTBEAT_INTERVAL);

// API endpoint to send bet command
app.post('/api/bet', (req, res) => {
  const { platform, pc, amount, side, single = false, user } = req.body;

  console.log('Bet request:', { platform, pc, amount, side });

  const selectedPC = pc;
  const oppositePC = pc === 'PC1' ? 'PC2' : 'PC1';
  const oppositeSide = side === 'Player' ? 'Banker' : 'Player';

  let sentCount = 0;

  // Helper to send bet to a specific PC
  const sendBetToPC = (targetPC, targetSide) => {
    const room = getRoom(user);
    room.clients.forEach((client) => {
      if (client.pc === targetPC && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(
          JSON.stringify({
            type: 'placeBet',
            platform,
            amount,
            side: targetSide,
          }),
        );
        sentCount += 1;
      }
    });
  };

  if (single) {
    // Bet only on the selected PC
    sendBetToPC(selectedPC, side);

    if (sentCount === 1) {
      res.json({ success: true, message: `Bet command sent to ${selectedPC}` });
    } else {
      res.status(404).json({ success: false, message: `${selectedPC} is not connected` });
    }
    return;
  }

  // Original behavior: send to both PCs
  sendBetToPC(selectedPC, side);
  sendBetToPC(oppositePC, oppositeSide);

  if (sentCount === 2) {
    res.json({ success: true, message: 'Bet commands sent to both PCs' });
  } else {
    res.status(404).json({ success: false, message: 'One or both PCs are not connected' });
  }
});

// Utility: cancel bet on a specific PC
function sendCancelBet(targetPC, platform = '', amount = null, side = '', room) {
  room.clients.forEach((client) => {
    if (client.pc === targetPC && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(
        JSON.stringify({
          type: 'cancelBet',
          platform,
          amount,
          side,
        }),
      );
    }
  });
}

// API endpoint to get connection status
app.get('/api/status', (req, res) => {
  const status = {
    PC1: false,
    PC2: false,
  };

  clients.forEach((client) => {
    if (client.ws.readyState === WebSocket.OPEN) {
      status[client.pc] = true;
    }
  });

  res.json(status);
});

// API endpoint to send cancel to both PCs
app.post('/api/cancelBetAll', (req, res) => {
  const { user } = req.body;
  if (user) {
    const room = getRoom(user);
    ['PC1', 'PC2'].forEach((pc) => sendCancelBet(pc, '', null, '', room));
  } else {
    // no user specified: broadcast to every room (admin scenario)
    rooms.forEach((room) => {
      ['PC1', 'PC2'].forEach((pc) => sendCancelBet(pc, '', null, '', room));
    });
  }
  res.json({ success: true });
});

// Login endpoint
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const userRecord = USERS[username];
  if (!userRecord) {
    return res.status(401).json({ success: false, message: 'Invalid credentials' });
  }
  if (!bcrypt.compareSync(password, userRecord.passwordHash)) {
    return res.status(401).json({ success: false, message: 'Invalid credentials' });
  }
  const token = generateAccessToken(username);
  return res.json({ success: true, token });
});

// ---------------- Admin APIs ----------------
// Get all users (admin only)
app.get('/api/users', authAdmin, (req, res) => {
  res.json(Object.keys(USERS));
});

// Add new user
app.post('/api/users', authAdmin, (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ success: false, message: 'Username and password required' });
  }
  if (USERS[username]) {
    return res.status(409).json({ success: false, message: 'User already exists' });
  }
  USERS[username] = { passwordHash: bcrypt.hashSync(password, 10) };
  saveUsers();
  return res.json({ success: true });
});

// Delete user (cannot delete admin)
app.delete('/api/users/:username', authAdmin, (req, res) => {
  const { username } = req.params;
  if (username === 'admin') return res.status(400).json({ success: false, message: 'Cannot delete admin user' });
  if (!USERS[username]) return res.status(404).json({ success: false, message: 'User not found' });
  delete USERS[username];
  saveUsers();
  return res.json({ success: true });
});

// Update admin password
app.put('/api/users/admin', authAdmin, (req, res) => {
  const { password } = req.body;
  if (!password) return res.status(400).json({ success: false, message: 'Password required' });
  USERS['admin'] = { passwordHash: bcrypt.hashSync(password, 10) };
  saveUsers();
  return res.json({ success: true });
});

// Start Express server
app.listen(PORT, () => {
  console.log(`Controller server running on http://localhost:${PORT}`);
  console.log(`WebSocket server running on ws://localhost:${WS_PORT}`);
});
