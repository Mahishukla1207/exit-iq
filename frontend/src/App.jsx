import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from './components/Header';
import ScenarioBar from './components/ScenarioBar';
import FloorMapCanvas from './components/FloorMapCanvas';
import CCTVStreamPlayer from './components/CCTVStreamPlayer';
import IntelligencePanel from './components/IntelligencePanel';
import TelemetryBar from './components/TelemetryBar';
import HazardControlModal from './components/HazardControlModal';

import {
  API_BASE_URL,
  fetchSimulationState,
  startSimulation,
  pauseSimulation,
  resetSimulation,
  loadScenario,
  toggleEdgeBlock,
  addHazard,
  removeHazard,
  updateCrowd,
  setSimulationMode,
} from './services/api';

import {
  reconnectPeraSession,
  connectPeraWallet,
  disconnectPeraWallet,
  executePaidEmergencyAnalysis,
} from './services/x402Payment';

import { speakEmergencyAlert } from './utils/audio';

export default function App() {
  const [mode, setMode] = useState('simulation');
  const [state, setState] = useState(null);
  const [isHazardModalOpen, setIsHazardModalOpen] = useState(false);
  const [selectedNodeForModal, setSelectedNodeForModal] = useState(null);
  const [errorStr, setErrorStr] = useState(null);

  // Pera Wallet & x402 Payment States
  const [peraAccount, setPeraAccount] = useState(null);
  const [isPeraConnecting, setIsPeraConnecting] = useState(false);
  const [isPaying, setIsPaying] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [paidData, setPaidData] = useState(null);

  const prevExitRef = useRef(null);

  // Auto-reconnect active Pera Wallet session
  useEffect(() => {
    reconnectPeraSession((acc) => setPeraAccount(acc));
  }, []);

  const handleConnectPera = async () => {
    setIsPeraConnecting(true);
    try {
      await connectPeraWallet((acc) => setPeraAccount(acc));
    } catch (err) {
      console.warn('Pera connection failed/aborted:', err);
    } finally {
      setIsPeraConnecting(false);
    }
  };

  const handleDisconnectPera = async () => {
    await disconnectPeraWallet(() => setPeraAccount(null));
  };

  const handleExecutePayment = async () => {
    if (!peraAccount) {
      handleConnectPera();
      return;
    }

    setIsPaying(true);
    try {
      const result = await executePaidEmergencyAnalysis(peraAccount, (status) => {
        setPaymentStatus(status);
      });
      if (result && result.data) {
        setPaidData(result.data);
      }
    } catch (err) {
      console.error('Paid emergency analysis error:', err);
    } finally {
      setIsPaying(false);
    }
  };

  const loadState = useCallback(async () => {
    try {
      const data = await fetchSimulationState();
      setState(data);
      setErrorStr(null);

      // Speak audio announcement if target exit changed or emergency alert triggered
      if (data && data.active_route) {
        const currentExit = data.active_route.target_exit_name;
        if (prevExitRef.current && prevExitRef.current !== currentExit) {
          if (!data.active_route.is_safe) {
            speakEmergencyAlert("Attention: All evacuation routes blocked. Seek designated emergency shelter immediately.");
          } else {
            speakEmergencyAlert(`Attention: Emergency route updated. Recommended exit is ${currentExit}.`);
          }
        }
        prevExitRef.current = currentExit;
      }
    } catch (err) {
      console.warn('Backend API connection offline:', err.message);
      setErrorStr(`Backend offline. Ensure FastAPI backend is reachable at ${API_BASE_URL}.`);
    }
  }, []);

  useEffect(() => {
    loadState();
    const interval = setInterval(loadState, 1000);
    return () => clearInterval(interval);
  }, [loadState]);

  const handleSelectScenario = async (scenarioId) => {
    try {
      const res = await loadScenario(scenarioId);
      if (res && res.state) setState(res.state);
    } catch (err) {
      console.error('Failed to load scenario:', err);
    }
  };

  const handleToggleRun = async () => {
    try {
      if (state?.is_running) {
        await pauseSimulation();
      } else {
        await startSimulation();
      }
      loadState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = async () => {
    try {
      const res = await resetSimulation();
      if (res && res.state) setState(res.state);
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleEdgeBlock = async (edgeId) => {
    try {
      await toggleEdgeBlock(edgeId);
      loadState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleNodeClick = (node) => {
    setSelectedNodeForModal(node);
    setIsHazardModalOpen(true);
  };

  const handleInjectHazard = async (zone_id, type, severity, description, node_id = null) => {
    try {
      await addHazard(zone_id, type, severity, description, node_id);
      loadState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRemoveHazard = async (hazard_id) => {
    try {
      await removeHazard(hazard_id);
      loadState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateCrowd = async (zone_id, density, count) => {
    try {
      await updateCrowd(zone_id, density, count);
      loadState();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetMode = async (newMode) => {
    setMode(newMode);
    try {
      await setSimulationMode(newMode);
      loadState();
    } catch (err) {
      console.warn('Failed to sync mode with backend:', err);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#090d16] text-[#f3f4f6]">
      {/* 1. Tactical Header */}
      <Header
        mode={mode}
        setMode={handleSetMode}
        activeScenario={state?.active_scenario}
        onRefresh={loadState}
        peraAccount={peraAccount}
        onConnectPera={handleConnectPera}
        onDisconnectPera={handleDisconnectPera}
        isPeraConnecting={isPeraConnecting}
      />

      {/* 2. Scenario & Simulation Action Bar */}
      <ScenarioBar
        activeScenario={state?.active_scenario}
        onSelectScenario={handleSelectScenario}
        isRunning={state?.is_running}
        tick={state?.tick}
        onToggleRun={handleToggleRun}
        onReset={handleReset}
        onOpenHazardModal={() => setIsHazardModalOpen(true)}
      />

      {/* Connection Warning Banner if backend unavailable */}
      {errorStr && (
        <div className="bg-rose-950/80 border-b border-rose-600/50 px-6 py-2 text-xs font-mono text-rose-200 flex items-center justify-between">
          <span>⚠️ {errorStr}</span>
          <span className="text-[10px] text-rose-400">Run from project root: python run_backend.py</span>
        </div>
      )}

      {/* 3. Main Operational Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left/Center: Building Evacuation Map OR CCTV Stream Player */}
        <div className="flex-1 relative bg-grid-tactical">
          {mode === 'simulation' ? (
            <FloorMapCanvas
              state={state}
              onToggleEdgeBlock={handleToggleEdgeBlock}
              onNodeClick={handleNodeClick}
            />
          ) : (
            <CCTVStreamPlayer state={state} />
          )}
        </div>

        {/* Right: Emergency Intelligence & Explainability Panel */}
        <IntelligencePanel
          state={state}
          onRemoveHazard={handleRemoveHazard}
          peraAccount={peraAccount}
          onConnectPera={handleConnectPera}
          onExecutePayment={handleExecutePayment}
          paymentStatus={paymentStatus}
          paidData={paidData}
          isPaying={isPaying}
        />
      </div>

      {/* 4. Bottom System Telemetry Metrics Bar */}
      <TelemetryBar metrics={state?.metrics} />

      {/* Hazard / Crowd Control Injection Modal */}
      <HazardControlModal
        isOpen={isHazardModalOpen}
        onClose={() => {
          setIsHazardModalOpen(false);
          setSelectedNodeForModal(null);
        }}
        onInjectHazard={handleInjectHazard}
        onUpdateCrowd={handleUpdateCrowd}
        selectedNode={selectedNodeForModal}
      />
    </div>
  );
}

