import { PeraWalletConnect } from '@perawallet/connect';
import algosdk from 'algosdk';
import { x402Client, x402HTTPClient } from '@x402/core/client';
import { ExactAvmScheme } from '@x402/avm/exact/client';
import { ALGORAND_TESTNET_CAIP2 } from '@x402/avm';

// Initialize singleton PeraWalletConnect instance
export const peraWallet = new PeraWalletConnect({
  shouldShowSignTxnToast: true,
});

/**
 * Adapter that bridges PeraWalletConnect to the x402 ClientAvmSigner interface.
 * Implements: signTransactions(txns: Uint8Array[], indexesToSign?: number[]): Promise<(Uint8Array | null)[]>
 */
export class PeraAvmSigner {
  constructor(address, peraWalletInstance = peraWallet) {
    this.address = address;
    this.peraWallet = peraWalletInstance;
  }

  /**
   * Signs transactions using Pera Wallet.
   * @param {Uint8Array[]} txns - Array of unsigned transaction bytes
   * @param {number[]} [indexesToSign] - Optional list of transaction indexes to sign
   * @returns {Promise<(Uint8Array | null)[]>} Array of signed transaction bytes
   */
  async signTransactions(txns, indexesToSign) {
    if (!txns || txns.length === 0) {
      return [];
    }

    // Decode unsigned msgpack transaction bytes into algosdk Transaction objects for Pera
    const signerTxns = txns.map((txnBytes, index) => {
      const decodedTxn = algosdk.decodeUnsignedTransaction(txnBytes);
      const shouldSign = !indexesToSign || indexesToSign.includes(index);
      return {
        txn: decodedTxn,
        // Empty signers array signals to Pera that this transaction does not require signing by this account
        signers: shouldSign ? undefined : [],
      };
    });

    // Pera expects an array of transaction groups: SignerTransaction[][]
    const signedTxns = await this.peraWallet.signTransaction([signerTxns], this.address);
    return signedTxns;
  }
}

/**
 * Creates an x402HTTPClient configured for Algorand Testnet with the Pera wallet signer.
 */
export function createX402Client(signer) {
  const client = new x402Client();
  
  // Register ExactAvmScheme for Algorand Testnet CAIP-2 and wildcard
  const scheme = new ExactAvmScheme(signer);
  client.register(ALGORAND_TESTNET_CAIP2, scheme);
  client.register('algorand:*', scheme);
  
  // Disable spend controls cap to prevent blocking arbitrary non-default configurations
  client.setSpendControls(false);

  return new x402HTTPClient(client);
}

/**
 * Reconnect existing Pera Wallet session on initial load.
 * @param {Function} onAccountChange - Callback when account state changes
 */
export async function reconnectPeraSession(onAccountChange) {
  try {
    const accounts = await peraWallet.reconnectSession();
    peraWallet.connector?.on('disconnect', () => {
      if (onAccountChange) onAccountChange(null);
    });
    if (accounts && accounts.length > 0) {
      if (onAccountChange) onAccountChange(accounts[0]);
      return accounts[0];
    }
  } catch (error) {
    console.warn('Pera session reconnect error:', error);
  }
  return null;
}

/**
 * Connect to Pera Wallet.
 * @param {Function} onAccountChange - Callback when account state changes
 */
export async function connectPeraWallet(onAccountChange) {
  try {
    const accounts = await peraWallet.connect();
    peraWallet.connector?.on('disconnect', () => {
      if (onAccountChange) onAccountChange(null);
    });
    if (accounts && accounts.length > 0) {
      if (onAccountChange) onAccountChange(accounts[0]);
      return accounts[0];
    }
  } catch (error) {
    if (error?.data?.type !== 'CONNECT_MODAL_CLOSED') {
      console.error('Pera Wallet connection error:', error);
    }
    throw error;
  }
  return null;
}

/**
 * Disconnect Pera Wallet session.
 * @param {Function} onAccountChange - Callback when account state changes
 */
export async function disconnectPeraWallet(onAccountChange) {
  try {
    await peraWallet.disconnect();
    if (onAccountChange) onAccountChange(null);
  } catch (error) {
    console.error('Pera disconnect error:', error);
  }
}

/**
 * Executes a full end-to-end x402 payment flow for ExitIQ Emergency Analysis.
 * 
 * 1. Makes unpaid GET request -> gets HTTP 402 challenge.
 * 2. Parses requirement with x402HTTPClient.
 * 3. Constructs Algorand Testnet USDC ASA 10458941 transaction and requests signature from Pera Wallet.
 * 4. Retries request with base64 PAYMENT-SIGNATURE header.
 * 5. Facilitator settles transaction on Testnet and Gateway returns HTTP 200 with real evacuation intelligence.
 * 
 * @param {string} accountAddress - Connected Pera Algorand address
 * @param {Function} onStatusUpdate - Status reporting callback
 */
export async function executePaidEmergencyAnalysis(accountAddress, onStatusUpdate = () => {}) {
  const gatewayUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:4021';
  const endpoint = `${gatewayUrl}/api/v1/paid/emergency-analysis`;

  try {
    // Step 1: Initial unpaid request to retrieve HTTP 402 challenge
    onStatusUpdate({
      step: 1,
      totalSteps: 4,
      title: 'Querying Gateway (Unpaid Check)',
      status: 'pending',
      details: `Initiating request to ${endpoint}...`,
    });

    const unpaidRes = await fetch(endpoint);

    if (unpaidRes.status === 200) {
      const data = await unpaidRes.json();
      onStatusUpdate({
        step: 4,
        totalSteps: 4,
        title: 'Emergency Analysis Verified',
        status: 'success',
        details: 'Resource already paid or accessible.',
      });
      return { data, isPaid: true };
    }

    if (unpaidRes.status !== 402) {
      throw new Error(`Expected HTTP 402 Payment Required, received status ${unpaidRes.status}`);
    }

    // Step 2: Parse HTTP 402 challenge
    let challengeBody = null;
    try {
      challengeBody = await unpaidRes.json();
    } catch {
      // JSON body is optional when header is present
    }

    onStatusUpdate({
      step: 2,
      totalSteps: 4,
      title: 'HTTP 402 Challenge Received',
      status: 'signing',
      details: 'Prompting Pera Wallet to approve 0.005 USDC (ASA 10458941) payment on Testnet...',
    });

    // Step 3: Create x402 client with Pera signer and generate payment payload
    const signer = new PeraAvmSigner(accountAddress, peraWallet);
    const httpClient = createX402Client(signer);

    const paymentRequired = httpClient.getPaymentRequiredResponse(
      (name) => unpaidRes.headers.get(name),
      challengeBody
    );

    // This prompts Pera Wallet to display the signing modal
    const paymentPayload = await httpClient.createPaymentPayload(paymentRequired);

    // Step 4: Encode PAYMENT-SIGNATURE header
    const paymentHeaders = httpClient.encodePaymentSignatureHeader(paymentPayload);

    // Step 5: Retry request with payment signature header for facilitator verification & settlement
    onStatusUpdate({
      step: 3,
      totalSteps: 4,
      title: 'Settling on Algorand Testnet',
      status: 'settling',
      details: 'Submitting signed transaction to GoPlausible Facilitator for on-chain settlement...',
    });

    const paidRes = await fetch(endpoint, {
      method: 'GET',
      headers: {
        ...paymentHeaders,
      },
    });

    if (!paidRes.ok) {
      let errDetails = `HTTP ${paidRes.status}`;
      try {
        const errJson = await paidRes.json();
        errDetails = errJson.error || errJson.message || errDetails;
      } catch {
        // use status text
      }
      throw new Error(`Gateway settlement failed: ${errDetails}`);
    }

    const intelData = await paidRes.json();
    const settleHeader = paidRes.headers.get('payment-response');
    let settleResponse = null;
    if (settleHeader) {
      try {
        settleResponse = httpClient.getPaymentSettleResponse((name) => paidRes.headers.get(name));
      } catch (e) {
        console.warn('Could not parse payment-response header:', e);
      }
    }

    onStatusUpdate({
      step: 4,
      totalSteps: 4,
      title: 'Payment Confirmed & Verified',
      status: 'success',
      details: 'Live emergency intelligence payload unlocked successfully.',
    });

    return {
      data: intelData,
      settleResponse: settleResponse || intelData.settlement,
      isPaid: true,
    };
  } catch (error) {
    onStatusUpdate({
      step: 0,
      totalSteps: 4,
      title: 'Payment / Settlement Failed',
      status: 'error',
      details: error.message || 'Transaction was rejected or settlement timed out.',
    });
    throw error;
  }
}
