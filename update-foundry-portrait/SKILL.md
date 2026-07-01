---
name: update-foundry-portrait
description: >
  Update a Foundry VTT NPC actor's portrait and map token from the Obsidian vault. Use this
  skill whenever the user asks to update, refresh, fix, or set a character portrait or token
  in Foundry VTT — including when an image is wrong, outdated, a placeholder, or missing.
  Also trigger when the user mentions syncing NPC images between Obsidian/vault and Foundry,
  wants to tokenize a character, or says a specific actor "needs a portrait". Accepts one or
  more vault NPC names and handles the full pipeline: vault lookup → PNG upload → canvas
  composite → Actor path update.
---

# Update Foundry Portrait

Updates a Foundry VTT NPC actor's portrait (Avatar) and map token (Token webp) from the vault
source PNG, using the canonical wooden ring frame.

## Campaign paths

| What | Path |
|---|---|
| Vault root | `D:\Google Drive\Obsidian\Pirates of Drinax\` |
| PNG source folder | `D:\Google Drive\Obsidian\Pirates of Drinax\z_Assets\` |
| Foundry URL | `https://ragnaverso.duckdns.org:7443/game` |
| Portraits upload folder (in Foundry) | `worlds/pirates-of-drinax/images/portraits/` |
| Tokenizer output folder (in Foundry) | `tokenizer/npc-images/` |
| Ring frame (in Foundry) | `modules/vtta-tokenizer/img/default-frame-npc.png` |
| Canvas size | 400 × 400 px |

---

## Step 1 — Resolve vault image and Foundry actor name

For each character name provided:

1. Find the NPC markdown file in `Lore/Characters/NPCs/<Name>.md` (also check `Lore/Characters/NPCs/Fiambres/` for deceased NPCs).
2. Extract the image filename by grepping for the inline embed pattern: `!\[\[.*\.png`  
   e.g. `![[rachando.png|wm-sm]]` → `rachando.png`
3. Confirm the PNG exists at `z_Assets/<filename>.png`.
4. Determine the Foundry actor name using the table below, then fall back to exact vault name if not listed.

### Known vault → Foundry name mappings

| Vault name | Foundry actor name |
|---|---|
| Princesa Rao | Princess Rao |
| Principe Harrik | Prince Harrik |
| Rey Oleb | King Oleb XVI |
| Johnny Belen | Jonny Belem |
| Thao Poluc | Imperial Consul Thao Poloc |
| Henshaw | Launch Pilot Henshaw |
| Petir Vallis | Petyr Vallis |
| Provoste Falx | Provost Falx |
| Goizader | Goizeder |

If the actor is still not found, search `game.actors` for a partial/fuzzy match and ask the user to confirm before proceeding.

### Slug convention

Used for webp filenames — apply to the **Foundry actor name** (not vault name):

```
actorName.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_')
```

Examples:
- `"King Oleb XVI"` → `"king_oleb_xvi"`
- `"Imperial Consul Thao Poloc"` → `"imperial_consul_thao_poloc"`
- `"Rachando"` → `"rachando"`

---

## Step 2 — Upload PNG(s) to Foundry portraits folder

**Important**: `file_upload` limit is 10 MB combined per call. Split into batches if processing multiple characters (roughly 5–6 PNGs per batch at ~1.2 MB each).

**2a. Open FilePicker and patch the file input:**

```javascript
// Open the FilePicker pointing at the portraits folder
const fp = new FilePicker({
  type: "image",
  current: "worlds/pirates-of-drinax/images/portraits/",
  callback: (path) => console.log("selected:", path),
});
fp.render(true);
```

Wait ~500 ms, then patch the input and attach the upload listener:

```javascript
(async () => {
  await new Promise(r => setTimeout(r, 500));
  const originalInput = document.querySelector('input[type="file"]');
  const newInput = originalInput.cloneNode(true);
  newInput.multiple = true;
  newInput.id = "patched-upload-input";
  originalInput.parentNode.replaceChild(newInput, originalInput);

  window._uploadResults = [];
  newInput.addEventListener('change', async function() {
    for (const file of Array.from(newInput.files)) {
      try {
        await FilePicker.upload("data", "worlds/pirates-of-drinax/images/portraits/", file, {});
        window._uploadResults.push(`OK: ${file.name}`);
      } catch(e) {
        window._uploadResults.push(`ERR: ${file.name}: ${e.message}`);
      }
    }
    console.log('Uploads done:', window._uploadResults.join(', '));
  });
  return "Input patched";
})()
```

**2b. Locate the file input and upload:**

Use `mcp__Claude_in_Chrome__find` with query `"file input for upload"` to get the ref, then call `mcp__Claude_in_Chrome__file_upload` with the Windows paths from `z_Assets\`.

**2c. Wait for completion (~8s per batch):**

```javascript
(async () => {
  await new Promise(r => setTimeout(r, 8000));
  return window._uploadResults.join('\n');
})()
```

All entries should read `OK: <filename>`. Re-upload any that show `ERR:`.

---

## Step 3 — Generate Avatar + Token webp via canvas, update actor paths

Run this single script in Foundry (via `mcp__Claude_in_Chrome__javascript_tool`). Populate the `actors` array from Step 1.

```javascript
(async () => {
  const SIZE = 400;
  const FRAME_PATH = "/modules/vtta-tokenizer/img/default-frame-npc.png";
  const PORTRAITS_BASE = "/worlds/pirates-of-drinax/images/portraits/";

  // Populate from Step 1 — one entry per character
  const actors = [
    { actorName: "Foundry Actor Name", portrait: "vault_image.png", slug: "foundry_actor_name" },
    // add more entries...
  ];

  const loadImage = (src) => new Promise((res, rej) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => res(img);
    img.onerror = () => rej(new Error(`Failed: ${src}`));
    img.src = src + "?_=" + Date.now();
  });

  const canvasToBlob = (c) => new Promise(r => c.toBlob(r, "image/webp", 0.92));

  // Cover-fill square — Avatar (full portrait, no clip)
  const drawCover = (ctx, img, size) => {
    const scale = Math.max(size / img.width, size / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    ctx.drawImage(img, (size - w) / 2, (size - h) / 2, w, h);
  };

  // Cover-fill clipped to circle — Token portrait layer
  const drawCoverCircle = (ctx, img, size) => {
    const scale = Math.max(size / img.width, size / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    ctx.save();
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.clip();
    ctx.drawImage(img, (size - w) / 2, (size - h) / 2, w, h);
    ctx.restore();
  };

  const frame = await loadImage(FRAME_PATH);
  const results = [];

  for (const { actorName, portrait, slug } of actors) {
    const actor = game.actors.find(a => a.name === actorName);
    if (!actor) { results.push(`SKIP ${actorName}: actor not found`); continue; }

    let img;
    try { img = await loadImage(PORTRAITS_BASE + portrait); }
    catch(e) { results.push(`SKIP ${actorName}: ${e.message}`); continue; }

    // Avatar: full portrait, square cover crop
    const avatarCanvas = document.createElement("canvas");
    avatarCanvas.width = SIZE; avatarCanvas.height = SIZE;
    drawCover(avatarCanvas.getContext("2d"), img, SIZE);

    // Token: portrait clipped to circle + wooden ring frame on top
    const tokenCanvas = document.createElement("canvas");
    tokenCanvas.width = SIZE; tokenCanvas.height = SIZE;
    const tctx = tokenCanvas.getContext("2d");
    drawCoverCircle(tctx, img, SIZE);
    tctx.drawImage(frame, 0, 0, SIZE, SIZE);

    await FilePicker.upload("data", "tokenizer/npc-images",
      new File([await canvasToBlob(avatarCanvas)], `${slug}.Avatar.webp`, { type: "image/webp" }), {});
    await FilePicker.upload("data", "tokenizer/npc-images",
      new File([await canvasToBlob(tokenCanvas)],  `${slug}.Token.webp`,  { type: "image/webp" }), {});

    const ts = Date.now();
    await actor.update({
      "img":                        `tokenizer/npc-images/${slug}.Avatar.webp?${ts}`,
      "prototypeToken.texture.src": `tokenizer/npc-images/${slug}.Token.webp?${ts}`,
    });

    results.push(`✅ ${actorName}`);
    console.log(`✅ ${actorName}`);
  }

  window._tokenizeResults = results;
  return results.join('\n');
})()
```

---

## Step 4 — Verify

```javascript
// Replace with actual Foundry actor names processed
const names = ["Foundry Actor Name 1", "Foundry Actor Name 2"];
names.map(n => {
  const a = game.actors.find(a => a.name === n);
  if (!a) return `${n}: NOT FOUND`;
  const ok = a.img?.startsWith("tokenizer/npc-images/") &&
             !a.img.includes("vespexer") &&
             !a.img.includes("mystery-man");
  return `${ok ? "✅" : "❌"} ${n}: ${a.img}`;
}).join('\n')
```

All actors should show ✅ with a `tokenizer/npc-images/<slug>.Avatar.webp?<timestamp>` path.

---

## Constraints

- **Never use `await` at the top level** in the Foundry console — always wrap async code in `(async () => { ... })()`.
- **`file_upload` limit is 10 MB per call** — batch uploads accordingly (roughly 5–6 portrait PNGs per call).
- **`actor.update()` is always required after uploading webps** — Foundry does not auto-update actor image paths.
- **Cache-busting timestamp** (`?${Date.now()}`) must be appended to webp paths in `actor.update()` to force Foundry to reload the image.

## Audit Trail
- [2026-06-15] Created from vault-image-sync-foundry session. Workflow verified live against 12 NPCs.
