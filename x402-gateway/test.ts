import { config } from 'dotenv';
import { spawn, execSync } from 'child_process';
import { ALGORAND_TESTNET_CAIP2, USDC_TESTNET_ASA_ID } from '@x402/avm';

config();

const port = process.env.PORT || '4021';
const avmAddress = process.env.AVM_ADDRESS;
const paymentAmount = process.env.PAYMENT_AMOUNT_USDC || '0.005';

// Correction 3: Fail clearly if AVM_ADDRESS is missing
if (!avmAddress) {
  console.error('❌ Error: AVM_ADDRESS environment variable is missing. Cannot run integration tests.');
  process.exit(1);
}

// Convert float to atomic units (decimals = 6 for USDC)
const expectedAtomicAmount = Math.round(parseFloat(paymentAmount) * 1000000);

async function runTests() {
  console.log('🏃 Spawning ExitIQ x402 Gateway process...');
  
  // Spawn the gateway server using tsx
  const gatewayProcess = spawn('npx', ['tsx', 'index.ts'], {
    shell: true,
    stdio: 'pipe',
    env: { ...process.env, MOCK_FACILITATOR: 'true' },
  });

  // Log gateway server stdout/stderr for transparency
  gatewayProcess.stdout.on('data', (data) => {
    console.log(`[Gateway Output] ${data.toString().trim()}`);
  });

  gatewayProcess.stderr.on('data', (data) => {
    console.error(`[Gateway Error] ${data.toString().trim()}`);
  });

  // Ensure process is terminated on exit
  let cleaned = false;
  const cleanUp = () => {
    if (cleaned) return;
    cleaned = true;
    try {
      gatewayProcess.stdout.destroy();
      gatewayProcess.stderr.destroy();
      if (gatewayProcess.pid) {
        if (process.platform === 'win32') {
          execSync(`taskkill /pid ${gatewayProcess.pid} /f /t`, { stdio: 'ignore' });
        } else {
          gatewayProcess.kill('SIGTERM');
        }
      }
    } catch {}
  };
  process.on('exit', cleanUp);
  process.on('SIGINT', cleanUp);
  process.on('SIGTERM', cleanUp);

  // Poll /health until server is ready (timeout after 15 seconds)
  console.log('Polling /health endpoint...');
  let isReady = false;
  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://localhost:${port}/health`);
      if (res.status === 200) {
        const body = await res.json();
        if (body.status === 'OK') {
          isReady = true;
          break;
        }
      }
    } catch (e) {
      // Server not started yet
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  if (!isReady) {
    console.error('❌ Error: Gateway failed to start or did not become healthy within 15s.');
    gatewayProcess.kill();
    process.exit(1);
  }

  console.log('✅ Gateway is online. Running unpaid 402 challenge test...');

  try {
    // Perform unpaid request
    const res = await fetch(`http://localhost:${port}/api/v1/paid/emergency-analysis`);
    
    console.log(`- Response Status: ${res.status} (Expected: 402)`);
    if (res.status !== 402) {
      throw new Error(`Expected HTTP status 402, got ${res.status}`);
    }
    console.log('✅ Test 1: Unpaid request returned HTTP 402 Payment Required.');

    // Print all headers for visibility
    console.log('--- Response Headers ---');
    res.headers.forEach((val, key) => {
      console.log(`  ${key}: ${val}`);
    });
    console.log('------------------------');

    // Parse response body or decode base64 payment-required header
    const paymentRequiredHeader = res.headers.get('payment-required');
    let body: any = {};
    if (paymentRequiredHeader) {
      const decodedText = Buffer.from(paymentRequiredHeader, 'base64').toString('utf8');
      body = JSON.parse(decodedText);
      console.log('✅ Decoded payment-required JSON Header:', JSON.stringify(body, null, 2));
    } else {
      body = await res.json();
      console.log('Parsed 402 JSON Body:', JSON.stringify(body, null, 2));
    }

    // Validate headers
    if (!paymentRequiredHeader) {
      throw new Error('Missing payment-required header in 402 response');
    }
    console.log('✅ Test 2: payment-required header is present.');

    // Correction 2: Verify specific x402 V2 parameters
    // Check version (handle multiple forms like 2, "2", "2.0")
    const versionStr = String(body.x402Version || body.version || '');
    if (!versionStr.startsWith('2')) {
      throw new Error(`Expected x402 version 2, got ${versionStr}`);
    }
    console.log('✅ Test 3: x402Version is 2.');

    // Resolve requirement object (could be at root, in accepts, or inside requirements)
    let req: any = null;
    if (body.requirements) {
      req = Array.isArray(body.requirements) ? body.requirements[0] : body.requirements;
    } else if (body.accepts) {
      req = Array.isArray(body.accepts) ? body.accepts[0] : body.accepts;
    } else {
      req = body;
    }

    if (!req) {
      throw new Error('Could not parse requirements object from body.');
    }

    console.log('Extracted Requirement Object for Verification:', JSON.stringify(req, null, 2));

    // scheme = exact
    const scheme = req.scheme;
    if (scheme !== 'exact') {
      throw new Error(`Expected scheme exact, got ${scheme}`);
    }
    console.log('✅ Test 4: scheme is exact.');

    // network = ALGORAND_TESTNET_CAIP2
    const network = req.network;
    if (network !== ALGORAND_TESTNET_CAIP2) {
      throw new Error(`Expected network ${ALGORAND_TESTNET_CAIP2}, got ${network}`);
    }
    console.log('✅ Test 5: network is ALGORAND_TESTNET_CAIP2.');

    // asset = USDC_TESTNET_ASA_ID (10458941)
    // Could be in asset property or in extra.asset
    const asset = String(req.asset || (req.extra && req.extra.asset) || '');
    if (asset !== String(USDC_TESTNET_ASA_ID)) {
      throw new Error(`Expected asset ${USDC_TESTNET_ASA_ID}, got ${asset}`);
    }
    console.log('✅ Test 6: asset is USDC_TESTNET_ASA_ID (10458941).');

    // payTo = AVM_ADDRESS
    const payTo = req.payTo;
    if (payTo !== avmAddress) {
      throw new Error(`Expected payTo ${avmAddress}, got ${payTo}`);
    }
    console.log('✅ Test 7: payTo matches configured AVM_ADDRESS.');

    // amount = exactly 5000 atomic units for 0.005 USDC
    const amountVal = String(req.amount || req.maxAmountRequired || '');
    if (amountVal !== String(expectedAtomicAmount)) {
      throw new Error(`Expected amount ${expectedAtomicAmount} atomic units, got ${amountVal}`);
    }
    console.log(`✅ Test 8: amount is exactly ${expectedAtomicAmount} atomic units.`);

    console.log('\n🎉 ALL INTEGRATION VALIDATION TESTS PASSED SUCCESSFULLY! 🎉');

  } catch (error: any) {
    console.error('❌ Integration Test Failed:', error.message);
    cleanUp();
    process.exit(1);
  }

  cleanUp();
  process.exit(0);
}

runTests();
