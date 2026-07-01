---
name: foundry-npc
description: >
  Create and populate a Traveller NPC actor in Foundry VTT (Pirates of Drinax
  campaign, MGT2 system) via the JavaScript console. Trigger when the user asks
  to create an NPC in Foundry, "add [Name] to Foundry", "set up a Foundry actor
  for [Name]", "populate [Name]'s stats in Foundry", "create a Traveller NPC",
  or any request to build, fill out, or configure a character sheet in Foundry
  VTT. Also trigger when the user wants to add skills, equipment, or
  characteristics to an existing Foundry actor. Use this for all humanoid NPCs
  (humans, Aslan, Vargr, etc.) — for ships use the foundry-ship skill instead.
---

# Foundry NPC — Traveller Actor Creation

Creates and populates a Traveller actor in Foundry VTT using the JavaScript console API. All operations are client-side — co no server access needed.

**Foundry URL.** `https://ragnaverso.duckdns.org:7443/game`
**System:** MGT2 (Mongoose Traveller 2nd Edition)

---

## Critical rules

- **Never use `await` at the top level** in the Foundry console — it throws SyntaxError. Wrap all async code in `(async () => { ... })()`.
- **Never use drag-and-drop** for adding items — it doesn't fire Foundry's DataTransfer events. Always use the JS API.
- **Always use exact item names** when searching compendiums. `includes()` can match unintended items. Use `i.name === exactName` or filter with an exact list.
- **Multiple items may share the same name** at different TLs (e.g., "Medikit" exists at TL8, TL10, TL12, TL14). Filter by `system.techLevel` when needed.
- **CSC item names** use the format `Name TlNN` (e.g., `"Vacc Suit Tl12"`, `"Cloth Tl10"`).

---

## Step 1 — Create the actor

```javascript
Actor.create({name: "NPC Name", type: "traveller"}).then(a => console.log("Created:", a.id));
```

Actor type is always `traveller` for both PCs and NPCs. The PC/NPC distinction is organizational only — NPCs go in the `NPCs` folder in the Actors panel.

---

## Step 2 — Set characteristics

All characteristic keys use full lowercase names:

```javascript
(async () => {
  const actor = game.actors.find(a => a.name === "NPC Name");
  await actor.update({
    "system.characteristics.strength.value": 9,
    "system.characteristics.dexterity.value": 8,
    "system.characteristics.endurance.value": 7,
    "system.characteristics.intelligence.value": 11,
    "system.characteristics.education.value": 9,
    "system.characteristics.socialStanding.value": 6  // capital S in Standing
  });
  console.log("Characteristics set");
})();
```

**All valid characteristic keys:** `strength`, `dexterity`, `endurance`, `intelligence`, `education`, `socialStanding`, `psionicStrength`, `stamina`, `lifeblood`, `alternative1`, `alternative2`, `alternative3`

---

## Step 3 — Set biography fields

```javascript
(async () => {
  const actor = game.actors.find(a => a.name === "NPC Name");
  await actor.update({
    "system.age": 34,
    "system.gender": "Hombre",       // or "Hembra"
    "system.species": "Humano",
    "system.homeWorld": "Torpol",
    "system.description": "Physical description and background here",
    "system.notes": "GM notes here"
  });
})();
```

---

## Step 4 — Add skills from MGT2 Skills compendium

Always add skills from the `MGT2 Skills` compendium, never create them manually.

```javascript
const pack = game.packs.find(p => p.metadata.label === "MGT2 Skills");
const actor = game.actors.find(a => a.name === "NPC Name");
const skillNames = ["Astrogation", "Deception", "Pilot: Spacecraft"];

pack.getIndex().then(index => {
  const entries = Array.from(index.values()).filter(i => skillNames.includes(i.name));
  Promise.all(entries.map(e => pack.getDocument(e._id))).then(docs => {
    actor.createEmbeddedDocuments("Item", docs.map(d => d.toObject()));
  });
});
```

**Setting skill levels after adding** (do NOT try to edit inline — single-clicking appends digits):
```javascript
const skill = actor.items.find(i => i.name === "Astrogation");
skill.update({"system.value": 2});
```

---

## Step 5 — Add equipment from CSC

Look up items in the `MGT2 Central Supply Catalog`. Set `equipped` on items that should appear in the sidebar stats.

```javascript
const csc = game.packs.find(p => p.metadata.label === "MGT2 Central Supply Catalog");
const actor = game.actors.find(a => a.name === "NPC Name");
const itemNames = ["Autopistol", "Cloth Tl10"];  // exact CSC names

csc.getIndex().then(index => {
  const entries = Array.from(index.values()).filter(i => itemNames.includes(i.name));
  Promise.all(entries.map(e => csc.getDocument(e._id))).then(docs => {
    const items = docs.map(d => {
      const obj = d.toObject();
      obj.system.equipped = "equipped";
      return obj;
    });
    actor.createEmbeddedDocuments("Item", items);
  });
});
```

Items auto-sort to the correct inventory section.

---

## Step 6 — Create custom items (when not in CSC)

Tag non-canonical items with `[claude]` prefix so they're identifiable.

**Custom armor:**
```javascript
const customArmor = {
  name: "[claude] Combat Vacc Suit +9",
  type: "armor",
  system: {
    armor: 9,
    equipped: "equipped",
    techLevel: 12,
    quantity: 1,
    weight: 0,
    price: 0,
    traits: [],
    description: "Description here",
    armorType: "nothing"
  }
};
const actor = game.actors.find(a => a.name === "NPC Name");
actor.createEmbeddedDocuments("Item", [customArmor]);
```

**Custom weapon:**
```javascript
const customWeapon = {
  name: "[claude] Reaver's Axe (4D)",
  type: "weapon",
  system: {
    damage: "4d6",
    associatedSkillName: "Melee: Blade",
    traits: [],
    armorPiercing: "0",
    equipped: "equipped",
    techLevel: 12,
    quantity: 1,
    weight: 0,
    price: 0,
    rateOfFire: "",
    magazineSize: 0,
    ammo: 0,
    magazineCost: 0,
    range: "melee",
    description: "Description here"
  }
};
actor.createEmbeddedDocuments("Item", [customWeapon]);
```

---

## Audit Trail
- [2026-06-16] Created from CLAUDE.md Foundry VTT Actor Manipulation Reference
