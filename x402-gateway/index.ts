import { config } from 'dotenv';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serve } from '@hono/node-server';
import { paymentMiddleware, x402ResourceServer } from '@x402/hono';
import { ExactAvmScheme } from '@x402/avm/exact/server';
import { HTTPFacilitatorClient } from '@x402/core/server';
import { ALGORAND_TESTNET_CAIP2, USDC_TESTNET_ASA_ID } from '@x402/avm';

// Load env variables
config();

const avmAddress = process.env.AVM_ADDRESS;
const facilitatorUrl = process.env.FACILITATOR_URL || 'https://facilitator.goplausible.xyz';
const exitIqBackendUrl = process.env.EXITIQ_BACKEND_URL || 'http://localhost:8000';
const port = parseInt(process.env.PORT || '4021', 10);
const paymentAmount = process.env.PAYMENT_AMOUNT_USDC || '0.005';

// Clear failure if AVM_ADDRESS is missing
if (!avmAddress) {
  console.error('❌ Error: AVM_ADDRESS environment variable is missing.');
  process.exit(1);
}

// Convert payment float price (e.g. 0.005) to price string (e.g. "$0.005")
const priceStr = `$${paymentAmount}`;

console.log('==================================================');
console.log('ExitIQ x402 Payment Gateway (V2)');
console.log(`- Receiver Address (payTo): ${avmAddress}`);
console.log(`- Facilitator URL: ${facilitatorUrl}`);
console.log(`- ExitIQ Backend Proxy: ${exitIqBackendUrl}`);
console.log(`- Configured Price: ${priceStr} USDC`);
console.log(`- Expected Atomic Amount: ${Math.round(parseFloat(paymentAmount) * 1000000)} units`);
console.log(`- Port: ${port}`);
console.log('==================================================');

const app = new Hono();

// Enable CORS
app.use('/*', cors());

// Initialize facilitator and resource server
const facilitatorClient = new HTTPFacilitatorClient({ url: facilitatorUrl });
const x402Server = new x402ResourceServer(facilitatorClient);
x402Server.register('algorand:*', new ExactAvmScheme());

// Set up payment requirements configuration
const paymentRoutes = {
  'GET /api/v1/paid/emergency-analysis': {
    accepts: [
      {
        scheme: 'exact' as const,
        network: ALGORAND_TESTNET_CAIP2 as `${string}:${string}`,
        payTo: avmAddress,
        price: priceStr,
        extra: { asset: Number(USDC_TESTNET_ASA_ID) }, // 10458941
      },
    ],
    description: 'ExitIQ Paid Real-Time Emergency Evacuation Analysis',
  },
};

// Mount x402 payment middleware on the paid endpoint
app.use('/api/v1/paid/emergency-analysis', paymentMiddleware(paymentRoutes, x402Server));

// Define paid route handler (runs ONLY if payment is verified on-chain)
app.get('/api/v1/paid/emergency-analysis', async (c) => {
  try {
    console.log('✓ x402 Payment Verified. Querying real ExitIQ backend...');
    
    // Proxy request to the actual FastAPI backend
    const response = await fetch(`${exitIqBackendUrl}/api/v1/simulation/state`);
    if (!response.ok) {
      return c.json({ error: 'Failed to retrieve intelligence from backend' }, 500);
    }
    
    const state = await response.json();
    
    // Extract real crowd zones details
    const crowdInfo = Object.entries(state.crowd_zones || {}).map(([zoneId, zone]: [string, any]) => ({
      zone_id: zoneId,
      count: zone.count,
      density: zone.density,
      avg_speed: zone.avg_speed,
      inflow_rate: zone.inflow_rate,
      outflow_rate: zone.outflow_rate
    }));
    
    // Extract LightGBM predictions
    const predictions = Object.entries(state.predictions || {}).map(([zoneId, pred]: [string, any]) => ({
      zone_id: zoneId,
      current_density: pred.current_density,
      predicted_density_1m: pred.predicted_density_1m,
      predicted_density_3m: pred.predicted_density_3m,
      predicted_congestion_prob: pred.predicted_congestion_prob,
      trend: pred.trend
    }));

    // Retrieve headers and middleware context
    const signature = c.req.header('Payment-Signature') || c.req.header('X-Payment') || null;
    const x402Context = (c as any).get?.('x402') || (c as any).get?.('payment') || null;

    const result = {
      people_crowd_info: crowdInfo,
      active_hazards: state.hazards || [],
      congestion_predictions: predictions,
      risk_info: {
        risk_weights: state.risk_weights,
        highest_risk_zone: state.metrics?.highest_risk_zone,
        highest_risk_score: state.metrics?.highest_risk_score,
        predicted_peak_congestion: state.metrics?.predicted_peak_congestion
      },
      recommended_evacuation_route: state.active_route ? {
        route_id: state.active_route.route_id,
        start_node: state.active_route.start_node,
        target_exit: state.active_route.target_exit,
        target_exit_name: state.active_route.target_exit_name,
        path_nodes: state.active_route.path_nodes,
        path_edges: state.active_route.path_edges,
        steps: state.active_route.steps,
        is_safe: state.active_route.is_safe,
        explanation_summary: state.active_route.explanation_summary,
        explanation_details: state.active_route.explanation_details
      } : null,
      route_cost: state.metrics?.route_cost || 0.0,
      route_explanation: state.active_route?.explanation_summary || 'No active route calculated.',
      timestamp: new Date().toISOString(),
      // Report actual settlement info from middleware/request headers (no fabrication)
      settlement: {
        payment_signature: signature,
        x402_context: x402Context
      }
    };
    
    return c.json(result);
  } catch (error: any) {
    console.error('❌ Error in gateway route handler:', error);
    return c.json({ error: 'Gateway Internal Error connecting to ExitIQ Backend', details: error.message }, 500);
  }
});

// Health check endpoint
app.get('/health', (c) => {
  return c.json({ status: 'OK', service: 'ExitIQ x402 Gateway' });
});

serve({
  fetch: app.fetch,
  port: port,
});
