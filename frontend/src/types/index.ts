export interface HealthResponse {
  ok: boolean;
  db: string;
  dev_no_auth: boolean;
  simulate_settlement: boolean;
  exposure_cap_drops: number;
  rpc_url: string | null;
  submit_mode: string;
  merchant_address: string | null;
}

export interface Device {
  device_id: string;
  dest_tag: number;
  exposure_cap_drops: number;
}

export interface Claim {
  channel_id: string;
  amount_drops: string | number;
  signature: string;
  pubkey: string;
  device_id?: string;
  seenAt?: string;
}

export interface ClaimQueueResponse {
  accepted: boolean;
  reason?: string;
  detail?: string;
}

export interface SettlementResponse {
  ok: boolean;
  tx_hash?: string;
  simulated?: boolean;
  reason?: string;
  error?: string;
  detail?: any;
}

export interface Receipt {
  channel_id: string;
  tx_hash: string;
  amount_drops: number;
  ledger_index: number;
  settledAt: string;
}

export interface ChannelInfo {
  channel_id: string;
  dest_address?: string;
  dest_tag?: number;
  last_settled_drops?: number;
  last_seen_drops?: number;
}

export interface ChannelInspectResponse {
  node?: {
    Account: string;
    Destination: string;
    Amount: string;
    Balance: string;
    PublicKey: string;
    SettleDelay: number;
    DestinationTag?: number;
    CancelAfter?: number;
    Expiration?: number;
  };
  ledger_index?: number;
  validated?: boolean;
}

export interface DashboardStats {
  totalClaims: number;
  totalSettled: number;
  totalRevenue: number;
  pendingClaims: number;
  activeChannels: number;
  registeredDevices: number;
}
