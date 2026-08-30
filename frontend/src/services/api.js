import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchSimulationState = async () => {
  const res = await api.get('/simulation/state');
  return res.data;
};

export const startSimulation = async () => {
  const res = await api.post('/simulation/start');
  return res.data;
};

export const pauseSimulation = async () => {
  const res = await api.post('/simulation/pause');
  return res.data;
};

export const resetSimulation = async () => {
  const res = await api.post('/simulation/reset');
  return res.data;
};

export const tickSimulation = async () => {
  const res = await api.post('/simulation/tick');
  return res.data;
};

export const addHazard = async (zone_id, type, severity, description, node_id = null, edge_id = null) => {
  const res = await api.post('/simulation/hazard', { zone_id, type, severity, description, node_id, edge_id });
  return res.data;
};

export const removeHazard = async (hazard_id) => {
  const res = await api.delete(`/simulation/hazard/${hazard_id}`);
  return res.data;
};

export const updateCrowd = async (zone_id, density, count) => {
  const res = await api.post('/simulation/crowd', { zone_id, density, count });
  return res.data;
};

export const toggleEdgeBlock = async (edge_id, is_blocked = null) => {
  const res = await api.post('/simulation/edge/block', { edge_id, is_blocked });
  return res.data;
};

export const loadScenario = async (scenario_name) => {
  const res = await api.post(`/simulation/scenario/${scenario_name}`);
  return res.data;
};

export const recalculateRoute = async (weights = null) => {
  const res = await api.post('/route/recalculate', weights);
  return res.data;
};

export const fetchPredictions = async () => {
  const res = await api.get('/prediction');
  return res.data;
};

export default api;
