
/**
 * XcceptaPay API — Offline-friendly / Dev-friendly server
 * - Health endpoint
 * - Optional auth bypass for dev (DEV_NO_AUTH=true)
 * - In-memory fallback if Mongo is down (USE_DB=false or connection fails)
 * - Claims: /claims/verify, /claims/queue, /claims/settle
 * - Devices: /devices/register
 * - Receipts: /receipts
 * - Settlement can be simulated (DEV_SIMULATE_SETTLEMENT=true) without XRPL access
 */

require("dotenv").config({ override: true });



const express = require("express");
const cors = require("cors");
const crypto = require("crypto");

const USE_DB = process.env.USE_DB === "true";
const DEV_NO_AUTH = process.env.DEV_NO_AUTH !== "false"; // default true
const DEV_SIMULATE_SETTLEMENT = process.env.DEV_SIMULATE_SETTLEMENT !== "false"; // default true
const EXPOSURE_CAP_DROPS = Number(process.env.EXPOSURE_CAP_DROPS || 1500000);
const DEV_SIG_VERIFY_MODE = process.env.DEV_SIG_VERIFY_MODE || "auto"; 
const app = express();
app.use(express.json());
app.use(cors());

// ---------- Optional Mongo (fallback to memory if disabled/unavailable) ----------
let mongoose, User, DbReady = false;
if (USE_DB) {
  try { mongoose = require("mongoose"); } catch (e) { console.warn("mongoose not installed; falling back to memory store."); }
}
if (USE_DB && mongoose) {
  const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017/xcceptapay";
  const userSchema = new mongoose.Schema({
    username: { type: String, required: true },
    email:    { type: String, required: true, unique: true },
    password: { type: String, required: true },
    balance:  { type: Number, default: 0 },
    wallet:   { type: String, default: "" },
    seed:     { type: String, default: "" },
    transaction_history: [{ date: String, amount: Number, recipient: String, status: String }],
    role: { type: String, enum: ["user","admin"], default: "user" }
  }, { timestamps: true });
  User = mongoose.model("User", userSchema);
  mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => { DbReady = true; console.log("[DB] Connected to MongoDB"); })
    .catch(err => { console.warn("[DB] Connection error; using in-memory store:", err.message); DbReady = false; });
}

// ---------- In-memory fallback stores ----------
const mem = {
  devices: new Map(),    // device_id -> { device_id, dest_tag, exposure_cap_drops }
  channels: new Map(),   // channel_id -> { channel_id, dest_address, dest_tag, last_settled_drops:0, last_seen_drops:0 }
  claims: new Map(),     // channel_id -> { amount_drops, signature, pubkey, seenAt }
  receipts: [],          // { channel_id, tx_hash, amount_drops, ledger_index, settledAt }
};
// at top of file
const { Client, Wallet } = require("xrpl");
console.log("[merchant address]", Wallet.fromSeed(process.env.MERCHANT_SEED).address);
// helper to settle highest queued claim:
async function settleHighestQueuedClaimREAL({ rpcUrl, merchantSeed, popNextClaim }) {
  const client = new Client(rpcUrl);             // e.g. wss://s.altnet.rippletest.net:51233
  await client.connect();

  try {
    const wallet = Wallet.fromSeed(merchantSeed); // MERCHANT_SEED (TESTNET)
    const { claim } = popNextClaim();             // { channel_id, amount_drops, signature, pubkey, ... }
    if (!claim) {
      return { ok: false, reason: "no_claims" };
    }

    // NOTE: For a signed “off-ledger claim”, the receiver (merchant) submits:
    // - Account: merchant address (wallet.address)
    // - Channel: channel_id
    // - Amount: cumulative amount authorized by the signature
    // - Balance: total delivered after this claim (for XRP delivery)
    // - PublicKey: payer’s channel public key (must match PayChannel.PublicKey)
    // - Signature: signed by payer over {channel_id, amount}
    //
    // Both Amount and Balance should equal the same cumulative drops.
    // See XRPL docs: PaymentChannelClaim fields. :contentReference[oaicite:0]{index=0}
    const tx = {
      TransactionType: "PaymentChannelClaim",
      Account: wallet.address,
      Channel: claim.channel_id,
      Amount: String(claim.amount_drops),   // cumulative (must match signed message)
      Balance: String(claim.amount_drops),  // new total delivered by channel
      PublicKey: claim.pubkey,              // hex, must match PayChannel.PublicKey
      Signature: claim.signature            // 128-hex signature from buyer
      // Optional flags, e.g., tfClose to close immediately:
      // Flags: 0x00020000
    };

    const prepared = await client.autofill(tx);
    const signed = wallet.sign(prepared);
    const result = await client.submitAndWait(signed.tx_blob);

    if (result?.result?.engine_result === "tesSUCCESS") {
      return {
        ok: true,
        simulated: false,
        tx_hash: result.result.tx_json.hash,
      };
    }
    return {
      ok: false,
      reason: "xrpl_submit_error",
      error: result?.result?.engine_result || "unknown_engine_result",
      detail: result?.result,
    };
  } finally {
    try { await client.disconnect(); } catch (_) {}
  }
}


// ---------- Dev auth (bypass or JWT) ----------
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");

function authMiddleware(req, res, next) {
  if (DEV_NO_AUTH) { req.user = { id: "dev", role: "admin" }; return next(); }
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) return res.status(401).json({ error: "Unauthorized" });
  const token = authHeader.split(" ")[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || "dev_secret");
    req.user = { id: decoded.id, role: decoded.role };
    next();
  } catch (err) { return res.status(401).json({ error: "Invalid token" }); }
}

// ---------- Health ----------
// at top of file if not already
app.get("/health", (req, res) => {
  let merchantAddress = null;
  try { merchantAddress = Wallet.fromSeed(process.env.MERCHANT_SEED).address; } catch (_) {}
  res.json({
    ok: true,
    db: USE_DB ? (DbReady ? "connected" : "fallback-memory") : "disabled",
    dev_no_auth: DEV_NO_AUTH,
    simulate_settlement: DEV_SIMULATE_SETTLEMENT,
    exposure_cap_drops: EXPOSURE_CAP_DROPS,
    rpc_url: process.env.RPC_URL || null,
    submit_mode: DEV_SIMULATE_SETTLEMENT ? "simulated" : "real",
    merchant_address: merchantAddress
  });
});



// Inspect a Payment Channel on-ledger (by channel_id a.k.a. LedgerIndex)
app.get("/channels/inspect", authMiddleware, async (req, res) => {
  const { channel_id } = req.query || {};
  if (!channel_id) return res.status(400).json({ error: "channel_id required" });

  try {
    const { Client } = require("xrpl");
    const rpcUrl = process.env.RPC_URL || "wss://s.altnet.rippletest.net:51233";
    const client = new Client(rpcUrl);
    await client.connect();
    const resp = await client.request({ command: "ledger_entry", index: channel_id, ledger_index: "validated" });
    await client.disconnect();
    return res.json(resp?.result || {});
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
});

// ---------- Devices ----------
let nextDestTag = 700000;
app.post("/devices/register", authMiddleware, (req, res) => {
  const { device_id, exposure_cap_drops } = req.body || {};
  if (!device_id) return res.status(400).json({ error: "device_id required" });
  const dest_tag = nextDestTag++;
  mem.devices.set(device_id, { device_id, dest_tag, exposure_cap_drops: Number(exposure_cap_drops || EXPOSURE_CAP_DROPS) });
  return res.json({ device_id, dest_tag, exposure_cap_drops: Number(exposure_cap_drops || EXPOSURE_CAP_DROPS) });
});

// ---------- Claims helpers (verify) ----------
let rippleKeypairs;
try {
  ({ encodeForSigningClaim } = require("ripple-binary-codec"));
  rippleKeypairs = require("ripple-keypairs");
  console.log("[XRPL] libs loaded");
} catch (e) { console.warn("[XRPL] libs not installed; /claims/verify will pass in DEV."); }

const { encodeForSigningClaim } = require("ripple-binary-codec");
const { verify: rippleVerify } = require("ripple-keypairs");

/**
 * Verify a PayChannel claim entirely offline.
 * Expects:
 *   claim = {
 *     channel_id: 64-hex,
 *     amount_drops: "NNN" (string of drops, cumulative),
 *     signature: hex,
 *     pubkey: hex (0xED + 32B Ed25519 key or 33B secp)
 *   }
 * Returns: { valid: boolean, reason?: string, detail?: string }
 */
function verifyClaim(claim) {
  try {
    const channel = String(claim.channel_id || "").trim();
    const amount  = String(claim.amount_drops || "").trim();
    const sigHex  = String(claim.signature || "").trim();
    const pubHex  = String(claim.pubkey || "").trim().toUpperCase();

    if (!/^[A-F0-9]{64}$/i.test(channel)) {
      return { valid: false, reason: "bad_channel" };
    }
    if (!/^\d+$/.test(amount)) {
      return { valid: false, reason: "bad_amount" };
    }
    if (!/^[a-fA-F0-9]+$/.test(sigHex)) {
      return { valid: false, reason: "bad_signature_hex" };
    }
    if (!/^[A-F0-9]+$/.test(pubHex)) {
      return { valid: false, reason: "bad_pubkey_hex" };
    }

    // IMPORTANT: JS version takes a single object, not two args
    let msgHex;
    try {
      msgHex = encodeForSigningClaim({ channel, amount });
    } catch (e) {
      return { valid: false, reason: "encode_error", detail: String(e) };
    }

    // ripple-keypairs: verify(messageHex, signatureHex, publicKeyHex) -> boolean
    let ok = false;
    try {
      ok = !!rippleVerify(msgHex, sigHex, pubHex);
    } catch (e) {
      return { valid: false, reason: "verify_exception", detail: String(e) };
    }

    return ok ? { valid: true } : { valid: false, reason: "bad_signature" };
  } catch (e) {
    return { valid: false, reason: "verify_exception_top", detail: String(e) };
  }
}


// ---------- Claims ----------
app.post("/claims/verify", (req, res) => {
  return res.json(verifyClaim(req.body || {}));
});

app.post("/claims/queue", authMiddleware, (req, res) => {
  const { channel_id, amount_drops, signature, pubkey, device_id } = req.body || {};
  const amt = Number(amount_drops);
  if (!channel_id || !Number.isFinite(amt)) return res.status(400).json({ accepted: false, reason: "bad_request" });

  const v = verifyClaim({ channel_id, amount_drops: amt, signature, pubkey });
  if (!v.valid) return res.status(400).json({ accepted: false, reason: v.reason || "invalid_signature" });
  if (!v.valid) {
    console.error("[verify] failed:", v);
    return res.status(400).json({ accepted: false, reason: "verify_error", detail: v.reason });
  }


  let ch = mem.channels.get(channel_id);
  if (!ch) { ch = { channel_id, dest_address: "(unknown)", dest_tag: 0, last_settled_drops: 0, last_seen_drops: 0 }; mem.channels.set(channel_id, ch); }

  let cap = EXPOSURE_CAP_DROPS;
  if (device_id && mem.devices.has(device_id)) { cap = Number(mem.devices.get(device_id).exposure_cap_drops || EXPOSURE_CAP_DROPS); }

  const lastSeen = Number(ch.last_seen_drops || 0);
  const settled = Number(ch.last_settled_drops || 0);
  if (amt <= lastSeen) return res.status(409).json({ accepted: false, reason: "stale_or_lower_amount" });
  if ((amt - settled) > cap) return res.status(402).json({ accepted: false, reason: "exposure_cap_exceeded" });

  ch.last_seen_drops = amt;
  mem.claims.set(channel_id, { channel_id, amount_drops: amt, signature, pubkey, seenAt: new Date().toISOString() });
  return res.json({ accepted: true });
});

// Settlement (simulated by default)
app.post("/claims/settle", authMiddleware, async (req, res) => {
  const { channel_id } = req.body || {};
  let targetId = channel_id;
  if (!targetId) {
    for (const [cid, claim] of mem.claims.entries()) {
      if (!targetId) targetId = cid;
      else {
        const cAmt = Number(claim.amount_drops || 0);
        const tAmt = Number(mem.claims.get(targetId)?.amount_drops || 0);
        if (cAmt > tAmt) targetId = cid;
      }
    }
  }
  if (!targetId) return res.json({ ok: false, reason: "no_claims" });
  const ch = mem.channels.get(targetId);
  const claim = mem.claims.get(targetId);
  if (!ch || !claim) return res.json({ ok: false, reason: "not_found" });

  if (DEV_SIMULATE_SETTLEMENT || !process.env.MERCHANT_SEED) {
    const fakeHash = "FAKE_" + crypto.randomBytes(16).toString("hex");
    ch.last_settled_drops = Number(claim.amount_drops);
    mem.receipts.push({ channel_id: targetId, tx_hash: fakeHash, amount_drops: Number(claim.amount_drops), ledger_index: 0, settledAt: new Date().toISOString() });
    mem.claims.delete(targetId);
    return res.json({ ok: true, tx_hash: fakeHash, simulated: true });
  }

  try {
    const { Client, Wallet } = require("xrpl");
    const rpcUrl = process.env.RPC_URL || "wss://s.altnet.rippletest.net:51233";
    const client = new Client(rpcUrl);
    await client.connect();

    const wallet = Wallet.fromSeed(process.env.MERCHANT_SEED);

    const tx = {
      TransactionType: "PaymentChannelClaim",
      Account: wallet.address,           // must equal channel.Destination
      Channel: targetId,
      Amount: String(claim.amount_drops),
      Balance: String(claim.amount_drops),
      PublicKey: claim.pubkey,
      Signature: claim.signature
    };

    const prepared = await client.autofill(tx);
    const signed = wallet.sign(prepared);
    const subRes = await client.submitAndWait(signed.tx_blob);

    // pull success signal from either top-level engine_result or meta.TransactionResult
    const eng = subRes?.result?.engine_result || subRes?.engine_result;
    const meta = subRes?.result?.meta;
    const metaResult = meta?.TransactionResult;
    const txh = subRes?.result?.tx_json?.hash || subRes?.result?.hash;

    const isSuccess =
      (eng === "tesSUCCESS") ||
      (metaResult === "tesSUCCESS") ||
      (!!txh && subRes?.result?.validated === true) ||
      (!!txh && subRes?.result?.validated_ledger_index); // defensive

    if (isSuccess && txh) {
      ch.last_settled_drops = Number(claim.amount_drops);
      mem.receipts.push({
        channel_id: targetId,
        tx_hash: txh,
        amount_drops: Number(claim.amount_drops),
        ledger_index: subRes?.result?.validated_ledger_index || subRes?.result?.ledger_index || 0,
        settledAt: new Date().toISOString(),
      });
      mem.claims.delete(targetId);
      await client.disconnect();
      return res.json({ ok: true, tx_hash: txh, simulated: false });
    }

    await client.disconnect();
    return res.status(500).json({
      ok: false,
      reason: "xrpl_submit_error",
      error: eng || metaResult || "unknown_engine_result",
      detail: subRes?.result || subRes,
    });
  } catch (e) {
    return res.status(500).json({ ok: false, reason: "xrpl_submit_error", error: e.message });
  }



});

// Receipts listing
app.get("/receipts", authMiddleware, (req, res) => {
  const { channel_id } = req.query || {};
  const list = channel_id ? mem.receipts.filter(r => r.channel_id === channel_id) : mem.receipts;
  return res.json(list);
});

// Minimal dev auth
app.post("/auth/register", async (req, res) => {
  if (!USE_DB || !DbReady || !User) {
    const { email="dev@example.com", role="admin" } = req.body || {};
    const token = jwt.sign({ id: "dev", role }, process.env.JWT_SECRET || "dev_secret", { expiresIn: "1d" });
    return res.json({ message: "Dev register (no DB)", token, user: { id: "dev", email, role } });
  }
  try {
    const { username, email, password, role } = req.body;
    const existing = await User.findOne({ email });
    if (existing) return res.status(400).json({ error: "Email already in use." });
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    const newUser = new User({ username, email, password: hashedPassword, role });
    const savedUser = await newUser.save();
    return res.status(201).json(savedUser);
  } catch (err) { return res.status(400).json({ error: err.message }); }
});

app.post("/auth/login", async (req, res) => {
  if (!USE_DB || !DbReady || !User) {
    const { role="admin" } = req.body || {};
    const token = jwt.sign({ id: "dev", role }, process.env.JWT_SECRET || "dev_secret", { expiresIn: "1d" });
    return res.json({ message: "Dev login (no DB)", token, user: { id: "dev", role } });
  }
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.status(400).json({ error: "Invalid credentials" });
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ error: "Invalid credentials" });
    const token = jwt.sign({ id: user._id, role: user.role }, process.env.JWT_SECRET || "dev_secret", { expiresIn: "1d" });
    return res.json({ message: "Login successful", token, user: { id: user._id, email: user.email, role: user.role } });
  } catch (err) { return res.status(400).json({ error: err.message }); }
});

// Start
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => { console.log(`Dev API running on port ${PORT}`); });
