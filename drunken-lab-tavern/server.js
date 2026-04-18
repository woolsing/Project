const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer);

app.use(express.static(path.join(__dirname, 'public')));

// ── Card Definitions ──────────────────────────────────────────────────────────
const CARD_DEFS = {
  cheap_beer:  { id: 'cheap_beer',  name: 'Cheap Beer',   type: 'attack',  intoxCost: 0,  intoxEffect: 10, targetMode: 'single', desc: 'Deal 10 intox to a player.' },
  shots:       { id: 'shots',       name: 'Shots!',       type: 'attack',  intoxCost: 10, intoxEffect: 25, targetMode: 'single', desc: 'Drink 10, deal 25 intox to a player.' },
  chug:        { id: 'chug',        name: 'Chug!',        type: 'attack',  intoxCost: 20, intoxEffect: 40, targetMode: 'single', desc: 'Drink 20, deal 40 intox (55 if you are above 60).' },
  water_break: { id: 'water_break', name: 'Water Break',  type: 'heal',    intoxCost: 0,  intoxEffect: -20, targetMode: 'self', desc: 'Reduce your own intox by 20.' },
  sabotage:    { id: 'sabotage',    name: 'Sabotage',     type: 'control', intoxCost: 15, intoxEffect: 0,  targetMode: 'single', desc: 'Drink 15, skip a player\'s next turn.' },
  buy_a_round: { id: 'buy_a_round', name: 'Buy a Round!', type: 'aoe',     intoxCost: 5,  intoxEffect: 12, targetMode: 'all',   desc: 'Drink 5, deal 12 intox to ALL other players.' },
};

// 19-card deck pool — each player gets their own shuffled copy
const DECK_POOL = [
  ...Array(5).fill('cheap_beer'),
  ...Array(4).fill('shots'),
  ...Array(3).fill('chug'),
  ...Array(3).fill('water_break'),
  ...Array(2).fill('sabotage'),
  ...Array(2).fill('buy_a_round'),
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function makeDeck() {
  return shuffle(DECK_POOL.map(defId => ({ instanceId: uuidv4(), ...CARD_DEFS[defId] })));
}

function addLog(room, msg) {
  room.log.unshift(msg);
  if (room.log.length > 30) room.log.pop();
}

// ── State Factories ───────────────────────────────────────────────────────────

function makeRoom(code) {
  return { code, phase: 'lobby', players: {}, turnOrder: [], activeIdx: 0, log: [], winnerId: null };
}

function makePlayer(id, name) {
  return { id, name, intox: 0, hand: [], deck: [], discard: [], ko: 0, status: 'active', skipNext: false, lastAttacker: null };
}

// ── Game Logic ────────────────────────────────────────────────────────────────

function getActive(room) {
  return room.players[room.turnOrder[room.activeIdx]];
}

function resolveCard(room, actorId, card, targetId) {
  const actor = room.players[actorId];

  // The intox cost is what you "drink" to play the card — added to actor
  if (card.intoxCost > 0) {
    actor.intox = Math.min(100, actor.intox + card.intoxCost);
  }

  // If drinking the cost collapsed the actor, the card effect doesn't resolve
  if (actor.intox >= 100) return;

  let effect = card.intoxEffect;
  if (card.id === 'chug' && actor.intox > 60) effect = 55;

  switch (card.targetMode) {
    case 'self': {
      actor.intox = Math.max(0, actor.intox + effect);
      addLog(room, `${actor.name} played ${card.name}.`);
      break;
    }
    case 'single': {
      const target = room.players[targetId];
      if (!target || target.status !== 'active') break;
      if (card.type === 'control') {
        target.skipNext = true;
        addLog(room, `⚠️  ${actor.name} sabotaged ${target.name}! Their next turn is skipped.`);
      } else {
        const prev = target.intox;
        target.intox = Math.min(100, target.intox + effect);
        target.lastAttacker = actorId;
        addLog(room, `${actor.name} → ${card.name} → ${target.name}  (${prev} → ${target.intox} intox)`);
      }
      break;
    }
    case 'all': {
      const others = room.turnOrder.filter(id => id !== actorId && room.players[id]?.status === 'active');
      for (const id of others) {
        const p = room.players[id];
        const prev = p.intox;
        p.intox = Math.min(100, Math.max(0, p.intox + effect));
        if (effect > 0) p.lastAttacker = actorId;
      }
      addLog(room, `${actor.name} played ${card.name}! All others: +${effect} intox`);
      break;
    }
  }
}

function checkCollapses(room) {
  for (const [id, p] of Object.entries(room.players)) {
    if (p.intox >= 100 && p.status === 'active') {
      p.status = 'collapsed';
      addLog(room, `💀 ${p.name} has collapsed!`);

      if (p.lastAttacker && room.players[p.lastAttacker]) {
        const attacker = room.players[p.lastAttacker];
        attacker.ko += 1;
        addLog(room, `🏆 ${attacker.name} earns a KO! (${attacker.ko}/3)`);
        if (attacker.ko >= 3) {
          room.phase = 'ended';
          room.winnerId = attacker.id;
          addLog(room, `🎉 ${attacker.name} wins the game with 3 KOs!`);
          return;
        }
      }

      // Recover after 4 seconds
      setTimeout(() => {
        const r = rooms[room.code];
        if (!r || !r.players[id] || r.phase === 'ended') return;
        r.players[id].status = 'active';
        r.players[id].intox = 20;
        r.players[id].lastAttacker = null;
        addLog(r, `🍺 ${r.players[id].name} recovered with 20 intox.`);
        broadcastState(r);
      }, 4000);
    }
  }
}

function advanceTurn(room) {
  if (room.phase !== 'playing') return;

  let tries = 0;
  do {
    room.activeIdx = (room.activeIdx + 1) % room.turnOrder.length;
    tries++;
    if (tries > room.turnOrder.length) return; // everyone collapsed simultaneously
  } while (room.players[room.turnOrder[room.activeIdx]]?.status !== 'active');

  const next = getActive(room);
  if (!next) return;

  if (next.skipNext) {
    next.skipNext = false;
    addLog(room, `⏭  ${next.name}'s turn is skipped!`);
    broadcastState(room);
    advanceTurn(room);
    return;
  }

  // Reshuffle discard into deck if empty
  if (next.deck.length === 0 && next.discard.length > 0) {
    next.deck = shuffle(next.discard);
    next.discard = [];
  }
  if (next.deck.length > 0) {
    next.hand.push(next.deck.shift());
  }

  addLog(room, `🎲 ${next.name}'s turn.`);
  broadcastState(room);
}

// ── Broadcast ─────────────────────────────────────────────────────────────────

function publicState(room, viewerId) {
  const players = {};
  for (const [id, p] of Object.entries(room.players)) {
    players[id] = {
      ...p,
      // Hide other players' card contents — only show count
      hand: id === viewerId ? p.hand : p.hand.map(() => null),
      handCount: p.hand.length,
    };
  }
  return {
    code: room.code,
    phase: room.phase,
    players,
    turnOrder: room.turnOrder,
    activeIdx: room.activeIdx,
    log: room.log,
    winnerId: room.winnerId,
  };
}

function broadcastState(room) {
  for (const id of room.turnOrder) {
    if (room.players[id]) {
      io.to(id).emit('state', publicState(room, id));
    }
  }
}

// ── Rooms Store ───────────────────────────────────────────────────────────────

const rooms = {};

// ── Socket Handlers ───────────────────────────────────────────────────────────

io.on('connection', socket => {
  console.log(`[+] ${socket.id} connected`);

  socket.on('join', ({ name, code }) => {
    const roomCode = (code || '').toUpperCase().trim() || uuidv4().slice(0, 4).toUpperCase();
    if (!rooms[roomCode]) rooms[roomCode] = makeRoom(roomCode);
    const room = rooms[roomCode];

    if (room.phase !== 'lobby') return socket.emit('err', 'Game already in progress.');
    if (Object.keys(room.players).length >= 6) return socket.emit('err', 'Room is full (max 6).');

    const player = makePlayer(socket.id, (name || '').slice(0, 20).trim() || 'Anon');
    room.players[socket.id] = player;
    room.turnOrder.push(socket.id);
    socket.join(roomCode);
    socket.data.room = roomCode;

    addLog(room, `${player.name} joined the tavern.`);
    broadcastState(room);
  });

  socket.on('start', () => {
    const room = rooms[socket.data.room];
    if (!room || room.phase !== 'lobby') return;
    if (room.turnOrder.length < 2) return socket.emit('err', 'Need at least 2 players to start.');

    room.phase = 'playing';
    room.turnOrder = shuffle(room.turnOrder);
    room.activeIdx = 0;

    for (const p of Object.values(room.players)) {
      p.deck = makeDeck();
      p.hand = p.deck.splice(0, 5);
    }

    addLog(room, `🎮 Game started with ${room.turnOrder.length} players!`);
    addLog(room, `🎲 ${getActive(room).name} goes first.`);
    broadcastState(room);
  });

  socket.on('play', ({ instanceId, targetId }) => {
    const room = rooms[socket.data.room];
    if (!room || room.phase !== 'playing') return;

    const active = getActive(room);
    if (!active || active.id !== socket.id) return socket.emit('err', 'Not your turn.');

    const cardIdx = active.hand.findIndex(c => c.instanceId === instanceId);
    if (cardIdx === -1) return socket.emit('err', 'Card not in hand.');

    const card = active.hand[cardIdx];

    if (card.targetMode === 'single' && !targetId) return socket.emit('err', 'Select a target first.');
    if (card.targetMode === 'single' && !room.players[targetId]) return socket.emit('err', 'Invalid target.');
    if (card.targetMode === 'single' && room.players[targetId]?.status !== 'active') return socket.emit('err', 'That player is not active.');
    if (card.targetMode === 'single' && targetId === socket.id) return socket.emit('err', 'Cannot target yourself.');

    // Remove from hand, add to discard before resolving
    active.hand.splice(cardIdx, 1);
    active.discard.push(card);

    resolveCard(room, socket.id, card, targetId);
    checkCollapses(room);

    if (room.phase === 'ended') { broadcastState(room); return; }

    advanceTurn(room);
  });

  socket.on('pass', () => {
    const room = rooms[socket.data.room];
    if (!room || room.phase !== 'playing') return;
    const active = getActive(room);
    if (!active || active.id !== socket.id) return;
    addLog(room, `${active.name} passed.`);
    advanceTurn(room);
  });

  socket.on('disconnect', () => {
    const code = socket.data.room;
    if (!code || !rooms[code]) return;
    const room = rooms[code];
    const p = room.players[socket.id];
    if (!p) return;

    addLog(room, `${p.name} left the tavern.`);
    delete room.players[socket.id];
    const idx = room.turnOrder.indexOf(socket.id);
    if (idx !== -1) room.turnOrder.splice(idx, 1);

    if (room.turnOrder.length === 0) { delete rooms[code]; return; }
    if (room.activeIdx >= room.turnOrder.length) room.activeIdx = 0;

    // Last player standing wins
    if (room.phase === 'playing' && room.turnOrder.length === 1) {
      room.phase = 'ended';
      room.winnerId = room.turnOrder[0];
      addLog(room, `🎉 ${room.players[room.turnOrder[0]].name} wins — last player standing!`);
    }

    broadcastState(room);
    console.log(`[-] ${socket.id} disconnected`);
  });
});

const PORT = process.env.PORT || 3000;
httpServer.listen(PORT, () => console.log(`🍺 Drunken Lab Tavern → http://localhost:${PORT}`));
