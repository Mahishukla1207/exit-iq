# Implementation Plan: Pera Wallet & x402 Client Integration for ExitIQ Testnet Payments

Integrate **Pera Wallet** and **x402 V2 AVM Client** (`@x402/core` and `@x402/avm`) into the ExitIQ React/Vite frontend to execute the first real end-to-end Algorand Testnet payment (0.005 USDC ASA 10458941) for protected real-time emergency evacuation intelligence (`GET /api/v1/paid/emergency-analysis`).

## User Review Required

> [!IMPORTANT]
> **No Seed Phrase / Private Key Needed**: All transaction signing will occur securely inside Pera Wallet via `@perawallet/connect`.
>
> **Live Testnet Execution**: The payment will use the real GoPlausible facilitator (`https://facilitator.goplausible.xyz`), real Algorand Testnet, real USDC ASA 10458941 (0.005 USDC / 5,000 atomic units), and will return real ExitIQ simulation & ML prediction intelligence upon settlement.

---

## Technical Architecture & Findings

### Package Inspection & Protocol Compatibility
1. **Installed Protocol Versions**:
   - `@x402/core` version `2.24.0`
   - `@x402/avm` version `2.24.0`
2. **AVM Client & Signer Architecture**:
   - `@x402/avm/exact/client` provides `ExactAvmScheme(signer, config)` which expects a `ClientAvmSigner`:
     ```typescript
     interface ClientAvmSigner {
       address: string;
       signTransactions(txns: Uint8Array[], indexesToSign?: number[]): Promise<(Uint8Array | null)[]>;
     }
     ```
   - `@x402/core/client` provides `x402Client` and `x402HTTPClient`.
   - `PeraWalletConnect` provides `signTransaction(signerTransactions: SignerTransaction[][], signerAddress?: string): Promise<Uint8Array[]>`.
   - By creating a lightweight bridge between `ClientAvmSigner` and `PeraWalletConnect` using `algosdk.decodeUnsignedTransaction`, we achieve native, seamless signing without any mock keys.

---

## Proposed Changes

### Frontend Dependencies

#### [MODIFY] [package.json](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/package.json)
Install required client dependencies:
- `@perawallet/connect`: `^1.3.6` (Pera Wallet browser connector)
- `algosdk`: `^2.7.0` (Algorand transaction decoder for Pera signer payload)
- `@x402/core`: `^2.24.0` (x402 HTTP & Client engine)
- `@x402/avm`: `^2.24.0` (AVM exact payment scheme & network constants)
- `vite-plugin-node-polyfills`: `^0.22.0` (Polyfills for `Buffer` and crypto primitives in browser build)

#### [MODIFY] [vite.config.js](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/vite.config.js)
Enable `nodePolyfills({ include: ['buffer', 'process'] })` so `algosdk` and msgpack encode/decode operate cleanly in browser Vite dev and production bundles.

---

### Payment Service Layer

#### [NEW] [frontend/src/services/x402Payment.js](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/src/services/x402Payment.js)
Encapsulate all Pera Wallet & x402 payment logic:
1. **`PeraWalletConnect` instance**: Handles `connect()`, `reconnectSession()`, and `disconnect()`.
2. **`createPeraAvmSigner(accountAddress)`**: Adapts Pera to `ClientAvmSigner.signTransactions()`.
3. **`createX402HttpClient(accountAddress)`**: Initializes `x402Client` registered with `ExactAvmScheme(peraSigner)` and wraps it with `x402HTTPClient`.
4. **`executePaidEmergencyAnalysis(accountAddress, onStatusUpdate)`**:
   - Issues initial request to `http://localhost:4021/api/v1/paid/emergency-analysis`.
   - On HTTP 402, decodes `payment-required` header.
   - Calls `httpClient.createPaymentPayload(paymentRequired)` (triggers Pera wallet signing prompt).
   - Encodes payment payload into `PAYMENT-SIGNATURE` HTTP header.
   - Retries `GET /api/v1/paid/emergency-analysis` with header.
   - Extracts and validates HTTP 200 payload and `payment-response` settlement header.
   - Returns full intelligence + settlement payload.

---

### UI Components

#### [MODIFY] [frontend/src/components/Header.jsx](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/src/components/Header.jsx)
- Add Pera Wallet Connect button.
- Display connection status pill:
  - If disconnected: "Connect Pera Wallet" with Pera icon.
  - If connected: Shows truncated address `ABCD...WXYZ`, Algorand Testnet indicator, and Disconnect option.

#### [MODIFY] [frontend/src/components/IntelligencePanel.jsx](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/src/components/IntelligencePanel.jsx)
- Add a 3rd tab or dedicated action section: **"x402 PAID INTEL"**.
- Interactive Trigger: **"Request Live Emergency Analysis (0.005 USDC)"**.
- Step-by-step progress tracking:
  1. `[1/4]` Challenged: HTTP 402 Payment Required received.
  2. `[2/4]` Signing: Prompting Pera Wallet for signature.
  3. `[3/4]` Settlement: GoPlausible Facilitator settling on Algorand Testnet.
  4. `[4/4]` Verified: Live Emergency Analysis received with on-chain settlement proof.
- Full visualization of real-time intelligence returned by the gateway (crowd metrics, ML congestion predictions, evacuation path, risk cost, and settlement signature / Tx ID).

#### [MODIFY] [frontend/src/App.jsx](file:///c:/Users/Mahi%20Shukla/Downloads/ExitIQ/frontend/src/App.jsx)
- Manage `connectedAccount` state and auto-reconnect on mount (`peraWallet.reconnectSession()`).
- Provide callbacks to Header and IntelligencePanel.

---

## Verification Plan

### Automated / Gateway Verification
1. Ensure `x402-gateway` runs with real GoPlausible facilitator (`MOCK_FACILITATOR` disabled):
   ```bash
   cd x402-gateway && npm run dev
   ```
2. Verify FastAPI backend is running on `http://localhost:8000`.
3. Verify Vite frontend runs cleanly without build/bundle errors:
   ```bash
   cd frontend && npm run dev
   ```

### Manual Real End-to-End Test
1. Open `http://localhost:3000`.
2. Connect Pera Wallet on Algorand Testnet.
3. Click "Request Live Emergency Analysis (0.005 USDC)".
4. Approve transaction in Pera Wallet (0.005 USDC ASA 10458941 + 0.001 ALGO fee).
5. Verify live settlement on-chain and display of ExitIQ emergency evacuation response.
