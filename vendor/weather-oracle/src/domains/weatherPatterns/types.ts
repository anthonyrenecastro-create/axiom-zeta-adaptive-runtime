/**
 * General Weather Patterns Sub-Domain
 * Handles synoptic-scale atmospheric dynamics, jet stream oscillations,
 * barometric pressure systems, and regional thermodynamic fields.
 */

export type SynopticSystemType = 'subtropical_high' | 'upper_trough' | 'cold_front' | 'atmospheric_river' | 'mjo_active_phase';

export interface SynopticFeature {
  id: string;
  name: string;
  type: SynopticSystemType;
  centerLat: number;
  centerLon: number;
  pressureMb: number;
  steeringVectorKts: { u: number; v: number }; // Directional eastward/northward components
  steeringAngleDeg: number;
  influenceRadiusNm: number;
}

export interface WeatherPatternState {
  timestamp: string;
  jetStreamLatitude: number;
  mjoPhase: number; // Madden-Julian Oscillation phase [1-8]
  teleconnectionIndices: {
    naoIndex: number; // North Atlantic Oscillation [-3 to +3]
    amoIndex: number; // Atlantic Multidecadal Oscillation [°C anomaly]
    pnaIndex: number; // Pacific/North American pattern
  };
  synopticFeatures: SynopticFeature[];
  ambientEnvironmentalShearKts: number;
  meanSteeringFlowKts: number;
  meanSteeringDirectionDeg: number;
  seaSurfaceTempGridC: number;
}
