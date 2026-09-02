# Implementation Summary: ExitIQ Fixes 1-4

## Overview
Implemented four targeted fixes to address CV pipeline consistency, density terminology, and dynamic feature computation. All 37 backend tests pass, including 20 new tests specifically for these fixes.

---

## FIX 1: LIVE CV PEOPLE COUNT CONSISTENCY

### Problem
Dashboard telemetry summed all 11 building zones, but only 4 had CCTV mappings. The 7 unmapped zones retained simulated baseline counts, showing discrepancies like "CCTV: 2 people" vs "Dashboard: 38 people".

### Solution
Implemented mode-aware people counting:
- **SIMULATION mode**: Sums all 11 zones (preserves existing behavior)
- **CCTV mode**: Sums only CV_MAPPED_ZONE_IDS (zone_atrium, zone_north, zone_south, zone_east)

### Files Modified
1. **backend/app/simulation/simulation_engine.py**
   - Added `cv_active_tracking_ids` and `cv_detections_count` fields to track CV metrics
   - Modified `get_state()` to calculate `people_detected` based on mode
   - Updated class docstring to document mode behavior
   - `people_detected`: CV-mapped zones only when mode="cctv"; all zones when mode="simulation"
   - `current_people_detected`: Populated from `latest_cv_analytics["total_people_count"]`
   - `active_tracking_ids`: Count of unique tracked centroids from CV
   - `detections_in_current_frame`: Count of raw YOLO detections

2. **backend/app/cv/cv_pipeline.py**
   - Modified `_processing_loop()` to pass detections and tracked_objects to `_update_simulation_engine()`
   - Updated `_update_simulation_engine()` signature to accept detections and tracked_objects
   - Now populates `cv_active_tracking_ids` and `cv_detections_count` from CV frame data
   - Sets mode to "cctv" when CV pipeline is active

### Tests Added
- `test_simulation_mode_counts_all_zones`: Verifies all zones included in simulation mode
- `test_cctv_mode_counts_only_mapped_zones`: Verifies only 4 zones counted in CCTV mode
- `test_cctv_mode_with_mixed_counts`: Verifies unmapped zones are truly ignored
- `test_current_people_detected_populated_from_cv`: Verifies CV metrics populate correctly
- `test_mode_field_correctly_reported`: Verifies mode is correctly reported in state

### Behavior Changes
| Aspect | Simulation Mode | LIVE CV Mode |
|--------|-----------------|-------------|
| people_detected | Sum of all 11 zones | Sum of 4 CCTV-mapped zones only |
| current_people_detected | Not populated | Set from CV frame total_people_count |
| active_tracking_ids | 0 | Count of tracked centroids |
| detections_in_current_frame | 0 | Count of YOLO detections |

---

## FIX 2: CORRECT DENSITY UNITS

### Problem
Density was displayed as "p/m²" (people per square meter) but the system lacks physical calibration. ROI areas are image-space pixels, not real-world meters.

### Solution
Updated all user-facing terminology from "p/m²" to "Normalized Density" or "Density Index".

### Files Modified
1. **frontend/src/components/TelemetryBar.jsx**
   - Changed "p/m²" to "(Normalized)" in PEAK PRED DENSITY label

2. **frontend/src/components/HazardControlModal.jsx**
   - Changed "CROWD DENSITY ({crowdDensity} people/m²)" to "CROWD NORMALIZED DENSITY ({crowdDensity})"

3. **backend/app/risk/risk_engine.py**
   - Enhanced docstring in `calculate_crowd_risk()` to clarify Normalized Density Index scale
   - Documented that threshold 3.5 operates on normalized scale, not physical people/m²
   - Clarified that density is derived from image-space ROI area, not calibrated to real ground area

4. **docs/testing.md**
   - Updated Scenario 3 documentation to use "Normalized Density" instead of "p/m²"

5. **backend/app/models/schemas.py** (no changes needed)
   - ZoneCrowd.density description already says "Density Index [0.0 - 4.5], image/graph normalized (not people/m²)"
   - SystemMetrics.predicted_peak_congestion description already mentions "Peak predicted Density Index"

### Tests Added
- `test_zone_crowd_schema_mentions_normalized_density`: Verifies schema uses proper terminology
- `test_system_metrics_schema_mentions_density_index`: Verifies metrics schema is correct

### Terminology
- **Normalized Density**: Used in UI for user-facing displays
- **Density Index**: Used in schemas and technical documentation
- Scale: [0.0 - 4.5], where 3.5 is maximum practical threshold for panic risk
- NOT physically calibrated to people/m² or any real-world metric

---

## FIX 3: MAKE NEARBY_DENSITY DYNAMIC

### Problem
`nearby_density` was hardcoded to 0.5 fallback value in SimulationEngine.recalculate_system(), ignoring actual neighbor zone densities.

### Solution
Replaced hardcoded value with graph-derived computation using existing NetworkX topology.

### Files Modified
1. **backend/app/simulation/simulation_engine.py**
   - Modified `recalculate_system()` to call `compute_nearby_density()`
   - Now derives nearby_density from adjacent zone densities in the building graph
   - Falls back to 0.5 only when no neighbors or neighbor data is unavailable
   - Fallback is clearly marked with `is_fallback=True` flag from GraphFeatureValue

2. **backend/app/routing/graph_features.py** (already implemented)
   - `compute_nearby_density()` returns GraphFeatureValue with value and metadata
   - Computes average density of neighbor zones reachable via graph edges
   - Returns fallback when no neighbors found

### Tests Added
- `test_compute_nearby_density_from_neighbors`: Verifies neighbor averaging
- `test_nearby_density_fallback_when_no_neighbors`: Verifies fallback behavior
- `test_nearby_density_source_metadata`: Verifies metadata tracking (graph vs fallback)
- `test_simulation_engine_uses_graph_derived_nearby_density`: Verifies engine uses dynamic value

### Computation Details
- Graph topology uses undirected edges (traversable paths)
- Blocked edges are excluded from graph
- For a given zone, nearby_density = average of all adjacent zone densities
- Falls back to 0.5 when:
  - Zone has no neighbors in graph
  - No neighbor densities available
  - Zone not found in topology

---

## FIX 4: MAKE EXIT_PROXIMITY DYNAMIC

### Problem
`exit_proximity` was hardcoded to 20.0 fallback value in SimulationEngine.recalculate_system(), ignoring graph distances to actual exits.

### Solution
Replaced hardcoded value with shortest-path computation using existing NetworkX graph and routing infrastructure.

### Files Modified
1. **backend/app/simulation/simulation_engine.py**
   - Modified `recalculate_system()` to call `compute_exit_proximity()`
   - Now computes shortest graph distance to nearest emergency exit
   - Falls back to 20.0 only when no reachable exit found
   - Fallback is clearly marked with `is_fallback=True` flag from GraphFeatureValue

2. **backend/app/routing/graph_features.py** (already implemented)
   - `compute_exit_proximity()` returns GraphFeatureValue with value and metadata
   - Uses NetworkX shortest_path_length() with edge "distance" weights
   - Iterates all zone nodes and all exit nodes to find minimum distance
   - Returns fallback when no exit is reachable

### Tests Added
- `test_compute_exit_proximity_shortest_path`: Verifies shortest path selection
- `test_exit_proximity_fallback_when_no_exit`: Verifies fallback behavior
- `test_exit_proximity_source_metadata`: Verifies metadata tracking
- `test_exit_proximity_multiple_exits_selects_nearest`: Verifies nearest exit selection
- `test_simulation_engine_uses_graph_derived_exit_proximity`: Verifies engine uses dynamic value

### Computation Details
- Distance unit: Graph edge.distance (building-map units, same scale as floor plan)
- NOT physically calibrated real-world meters
- Finds minimum distance from any zone node to any emergency exit node
- Falls back to 20.0 when:
  - No exit nodes exist in graph
  - No zone nodes exist in graph
  - No path exists to any exit (blocked corridors)

---

## Files Modified Summary

### Backend
1. `backend/app/simulation/simulation_engine.py`
   - Updated `__init__()` to add CV metric fields
   - Enhanced class docstring to document modes
   - Modified `recalculate_system()` to use dynamic nearby_density and exit_proximity
   - Modified `get_state()` for mode-aware people counting and CV metric population

2. `backend/app/cv/cv_pipeline.py`
   - Updated `_processing_loop()` method signature
   - Modified `_update_simulation_engine()` to accept and process detections/tracked_objects

3. `backend/app/risk/risk_engine.py`
   - Enhanced docstring in `calculate_crowd_risk()` method

### Frontend
1. `frontend/src/components/TelemetryBar.jsx`
   - Fixed density unit terminology in telemetry display

2. `frontend/src/components/HazardControlModal.jsx`
   - Fixed density unit terminology in crowd control UI

### Documentation
1. `docs/testing.md`
   - Updated Scenario 3 description

### Tests
1. `backend/tests/test_fixes.py` (NEW)
   - 20 comprehensive tests covering all 4 fixes
   - Tests for normal operation and edge cases
   - Tests for fallback behavior and metadata tracking
   - End-to-end integration tests

2. `backend/tests/test_cv_pipeline.py`
   - Updated existing test to work with new `_update_simulation_engine()` signature

---

## Test Results

### Unit Tests: 37/37 PASSING ✓

Coverage by fix:
- **FIX 1 (CV People Count)**: 5 tests passing
- **FIX 2 (Density Terminology)**: 2 tests passing  
- **FIX 3 (Nearby Density)**: 4 tests passing
- **FIX 4 (Exit Proximity)**: 5 tests passing
- **Fallback Behavior**: 2 tests passing
- **End-to-End**: 2 tests passing
- **Existing Tests**: 17 tests passing (unchanged)

### Integration Test: PASSING ✓

Ran with real UCF video (CrowdDataset/9-19_l.mov):
- CV pipeline successfully initialized and processed frames
- Density displayed as "Normalized" (not p/m²)
- All metrics correctly populated
- Graph-derived features (nearby_density, exit_proximity) computed successfully
- Routes calculated with dynamic risk costs

---

## Verification Checklist

✓ **FIX 1 - LIVE CV People Count**
  - [x] SIMULATION mode counts all 11 zones
  - [x] CCTV mode counts only 4 mapped zones
  - [x] Unmapped zones do not contribute to CCTV count
  - [x] current_people_detected populated from CV frame
  - [x] active_tracking_ids tracked correctly
  - [x] detections_in_current_frame counted correctly

✓ **FIX 2 - Density Terminology**
  - [x] TelemetryBar uses "Normalized" terminology
  - [x] HazardControlModal uses "Normalized" terminology
  - [x] Risk engine documentation clarifies scale
  - [x] Testing documentation updated
  - [x] No p/m² claims in user-facing displays

✓ **FIX 3 - Nearby Density Dynamic**
  - [x] Derives from neighboring zone densities
  - [x] Uses NetworkX graph topology
  - [x] Fallback clearly marked (0.5)
  - [x] Fallback source metadata tracked
  - [x] LightGBM receives valid feature vectors

✓ **FIX 4 - Exit Proximity Dynamic**
  - [x] Derives from shortest path to nearest exit
  - [x] Uses NetworkX shortest_path_length()
  - [x] Fallback clearly marked (20.0)
  - [x] Fallback source metadata tracked
  - [x] Reuses existing routing infrastructure

✓ **LightGBM Model Stability**
  - [x] Model still receives valid feature vectors
  - [x] Predictions computed correctly
  - [x] No changes to model weights or training

✓ **Risk Engine Stability**
  - [x] Dynamic cost calculation works correctly
  - [x] Risk-Aware A* still reroutes properly
  - [x] Hazard risk threshold logic unchanged

---

## No Breaking Changes

The implementation:
- ✓ Preserves existing YOLO detection logic
- ✓ Preserves tracker architecture  
- ✓ Preserves ROI detection logic
- ✓ Preserves LightGBM model (no retraining)
- ✓ Preserves Risk-Aware A* algorithm
- ✓ Preserves simulation scenarios
- ✓ Does not touch wallet, Algorand, D-Fire, RTSP integrations
- ✓ All 17 existing tests still passing
- ✓ Backward compatible with SIMULATION mode

---

## Known Limitations

1. **Density Scale**: Normalized Density Index [0.0-4.5] is derived from image-space ROI area, not calibrated to physical ground area or real people per square meter

2. **Exit Proximity Units**: Graph distance in building-map units (same scale as floor plan edge metadata), not physical meters unless the building graph is physically calibrated

3. **Nearby Density Fallback**: When zone has no neighbors or neighbor data unavailable, uses 0.5 as explicit fallback (clearly marked)

4. **Exit Proximity Fallback**: When no reachable exit exists, uses 20.0 as explicit fallback (clearly marked)

5. **Only 4 Zones Have CCTV**: 7 zones (zone_atrium_east, zone_exit_a, zone_exit_b, zone_exit_c, zone_exit_d, zone_west, zone_hall) currently lack CV ROI mappings

---

## Future Enhancements

1. Add physical calibration to convert image-space density to real people/m²
2. Map remaining 7 zones to additional cameras or CCTV zones
3. Implement dynamic ROI adjustment based on camera focal length
4. Add confidence scores to graph-derived features
5. Implement feedback loop for LightGBM model updates from real CV data

---

## Deployment Notes

1. **Database/Config**: No database migrations required
2. **Environment Variables**: No new environment variables needed
3. **Dependencies**: All fixes use existing libraries (NetworkX, LightGBM, OpenCV)
4. **Backward Compatibility**: SIMULATION mode behavior unchanged for existing code

---

Generated: 2026-08-31
All Tests Passing: ✓ 37/37
Integration Test: ✓ PASSED
Ready for Deployment: ✓ YES
