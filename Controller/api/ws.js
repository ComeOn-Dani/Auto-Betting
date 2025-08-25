const WebSocket = require('ws');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const fs = require('fs');
const path = require('path');

// Load users
const USERS_FILE = path.join(__dirname, '../users.json');
let USERS = JSON.parse(fs.readFileSync(USERS_FILE, 'utf8'));

const JWT_SECRET = process.env.JWT_SECRET || 'INSECURE_DEV_SECRET_CHANGE_ME';

function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    return null;
  }
}

// Store connected clients (in memory - will reset on serverless cold starts)
const clients = new Map();
const assignedPCs = new Set();
const statusListeners = new Set();
const rooms = new Map();

function getRoom(user) {
  if (!rooms.has(user)) {
    rooms.set(user, {
      clients: new Map(),
      assignedPCs: new Set(),
      statusListeners: new Set(),
    });
  }
  return rooms.get(user);
}

module.exports = (req, res) => {
  // Handle WebSocket upgrade
  if (req.headers.upgrade && req.headers.upgrade.toLowerCase() === 'websocket') {
    const wss = new WebSocket.Server({ noServer: true });
    
    wss.on('connection', (ws) => {
      console.log('New WebSocket connection');
      
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
            
            // Store client info
            room.clients.set(clientId, {
              ws,
              user: clientUser,
              pcName: null,
              lastHeartbeat: Date.now()
            });

            ws.send(JSON.stringify({ type: 'hello', success: true }));
            return;
          }

          // Handle other message types
          if (data.type === 'register') {
            const pcName = data.pcName;
            if (room.assignedPCs.has(pcName)) {
              ws.send(JSON.stringify({ type: 'error', message: 'PC name already taken' }));
              return;
            }

            room.assignedPCs.add(pcName);
            room.clients.get(clientId).pcName = pcName;
            
            ws.send(JSON.stringify({ type: 'registered', pcName }));
            
            // Notify status listeners
            room.statusListeners.forEach(listener => {
              listener.ws.send(JSON.stringify({
                type: 'status',
                pcName,
                status: 'connected'
              }));
            });
          }
          else if (data.type === 'heartbeat') {
            room.clients.get(clientId).lastHeartbeat = Date.now();
            ws.send(JSON.stringify({ type: 'heartbeat' }));
          }
          else if (data.type === 'bet_result') {
            // Handle bet results
            console.log('Bet result:', data);
            
            // Notify status listeners
            room.statusListeners.forEach(listener => {
              listener.ws.send(JSON.stringify({
                type: 'bet_result',
                pcName: room.clients.get(clientId).pcName,
                success: data.success,
                message: data.message
              }));
            });
          }
        } catch (error) {
          console.error('Error processing message:', error);
          ws.send(JSON.stringify({ type: 'error', message: 'Invalid message format' }));
        }
      });

      ws.on('close', () => {
        if (room && room.clients.has(clientId)) {
          const clientData = room.clients.get(clientId);
          if (clientData.pcName) {
            room.assignedPCs.delete(clientData.pcName);
            
            // Notify status listeners
            room.statusListeners.forEach(listener => {
              listener.ws.send(JSON.stringify({
                type: 'status',
                pcName: clientData.pcName,
                status: 'disconnected'
              }));
            });
          }
          room.clients.delete(clientId);
        }
      });
    });

    // Handle the upgrade
    wss.handleUpgrade(req, req.socket, Buffer.alloc(0), (ws) => {
      wss.emit('connection', ws, req);
    });
  } else {
    res.status(400).json({ error: 'WebSocket upgrade required' });
  }
};
