/**
 * Hurricane Digital Twin Sub-Domain
 * Dedicated domain model focused strictly on vortex dynamics, eyewall physics,
 * maximum potential intensity (MPI), storm surge, and tropical cyclone structure.
 */

import { StormCategory } from '../../types/weatherEcology';

export interface EyewallDynamics {
  eyeRadiusNm: number;
  eyewallMaxReflectivityDbz: number;
  eyewallReplacementCyclePhase: 'stable_core' | 'secondary_eyewall_forming' | 'concentric_eyewalls' | 'outer_eyewall_collapse';
  convectiveAsymmetryRatio: number; // [0-1]
}

export interface VortexCoreMetrics {
  centralPressureMb: number;
  maximumSustainedWindKts: number;
  peakWindGustKts: number;
  radiusOfMaximumWindsNm: number;
  quadrant34ktWindRadiusNm: { NE: number; SE: number; SW: number; NW: number };
  quadrant50ktWindRadiusNm: { NE: number; SE: number; SW: number; NW: number };
  quadrant64ktWindRadiusNm: { NE: number; SE: number; SW: number; NW: number };
}

export interface HurricaneTwinState {
  stormId: string;
  stormName: string;
  category: StormCategory;
  lat: number;
  lon: number;
  headingDeg: number;
  speedKts: number;
  vortexCore: VortexCoreMetrics;
  eyewall: EyewallDynamics;
  estimatedStormSurgePeakFt: number;
  rapidIntensificationProbability: number; // [0-1]
  maximumPotentialIntensityKts: number;
}
