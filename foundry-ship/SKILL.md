---
name: foundry-ship
description: >
  Create and populate a Ship actor in Foundry VTT (Pirates of Drinax campaign,
  MGT2 system) via the JavaScript console. Trigger when the user asks to create
  a ship in Foundry, "add [Ship Name] to Foundry", "set up a ship actor",
  "create a [class] ship", "populate the ship stats for [Name]", or any request
  to build or configure a starship sheet in Foundry VTT. Also trigger when the
  user wants to add components, crew positions, cargo, or finance data to an
  existing ship actor. For crew members (Traveller NPCs) use the foundry-npc
  skill; this skill handles the ship itself.
---

# Foundry Ship — Ship Actor Creation

Creates and populates a Ship actor in Foundry VTT using the JavaScript console API. All operations are client-side — co no server access needed.

**Foundry URL.** `https://ragnaverso.duckdns.org:7443/game`
**System:** MGT2 (Mongoose Traveller 2nd Edition)

---

## Critical rules

- **Never use `await` at the top level** in the Foundry console — it throws SyntaxError. Wrap all async code in `(async () => { ... })()`.
- **Never use drag-and-drop** for adding items — use the JS API only.

---

## Step 1 — Create the ship actor

```javascript
Actor.create({name: "Ship Name", type: "ship"}).then(a => console.log("Created:", a.id));
```

---

## Step 2 — Set ship header stats

```javascript
(async () => {
  const ship = game.actors.find(a => a.name === "Ship Name");
  await ship.update({
    "system.techLevel": 12,
    "system.shipStats.mass.value": 100,
    "system.shipStats.mass.max": 100,
    "system.shipStats.hull.value": 20,
    "system.shipStats.hull.max": 20,
    "system.shipStats.fuel.value": 20,
    "system.shipStats.fuel.max": 20,
    "system.shipStats.fuel.isRefined": true,
    "system.shipStats.armor.value": 2,
    "system.shipStats.armor.max": 2,
    "system.shipStats.power.max": 30,
    "system.shipStats.drives.jDrive.rating": 2,
    "system.shipStats.drives.mDrive.rating": 2,
    "system.shipValue": 28.629,
    "system.maintenanceCost": 2385,
    "system.isMassProduced": true,
    "system.notes": "Ship description here"
  });
  console.log("Ship stats set");
})();
```

---

## Step 3 — Add ship components

Always use the `MGT2 Ship Components` compendium (34 items total).

```javascript
const pack = game.packs.find(p => p.metadata.label === "MGT2 Ship Components");
const ship = game.actors.find(a => a.name === "Ship Name");
const toAdd = ["Hull", "M-Drive", "J-Drive", "Power Plant", "Bridge", "Staterooms", "Sensors", "Fuel Tanks"];

pack.getIndex().then(index => {
  const entries = Array.from(index.values()).filter(i => toAdd.includes(i.name));
  Promise.all(entries.map(e => pack.getDocument(e._id))).then(docs => {
    ship.createEmbeddedDocuments("Item", docs.map(d => d.toObject()));
  });
});
```

**Set component quantity:**
```javascript
const comp = ship.items.find(i => i.name === "Staterooms");
comp.update({"system.quantity": 4});
```

---

## Audit Trail
- [2026-06-16] Created from CLAUDE.md Foundry VTT Ship Actor section
