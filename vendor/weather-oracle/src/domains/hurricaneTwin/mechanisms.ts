/**
 * Hurricane Digital Twin Domain Mechanisms
 * Specialized vortex physics, MPI calculation, and eyewall cycle modeling.
 */

import { HurricaneTwinState } from './types';

export function createInitialHurricaneTwinState(): HurricaneTwinState {
  return {
    stormId: 'AL142026',
    stormName: 'Milton',
    category: 'Cat4',
    lat: 25.8,
    lon: -84.2,
    headingDeg: 42,
    speedKts: 14,
    vortexCore: {
      centralPressureMb: 938,
      maximumSustainedWindKts: 130,
      peakWindGustKts: 155,
      radiusOfMaximumWindsNm: 14,
      quadrant34ktWindRadiusNm: { NE: 180, SE: 150, SW: 110, NW: 140 },
      quadrant50ktWindRadiusNm: { NE: 90, SE: 80, SW: 60, NW: 75 },
      quadrant64ktWindRadiusNm: { NE: 45, SE: 40, SW: 30, NW: 35 }
    },
    eyewall: {
      eyeRadiusNm: 14,
      eyewallMaxReflectivityDbz: 58.5,
      eyewallReplacementCyclePhase: 'secondary_eyewall_forming',
      convectiveAsymmetryRatio: 0.88
    },
    estimatedStormSurgePeakFt: 13.8,
    rapidIntensificationProbability: 0.82,
    maximumPotentialIntensityKts: 165
  };
}

/**
 * Calculates Maximum Potential Intensity (MPI) based on SST and upper-level outflow temperature
 */
export function calculateMPI(sstC: number, tropopauseTempC: number = -75): number {
  // B Emanuel MPI thermodynamic scaling
  const sstK = sstC + 273.15;
  const tropK = tropopauseTempC + 273.15;
  const efficiency = (sstK - tropK) / sstK;
  
  // Empirical thermodynamic capacity
  const maxVelocityKts = Math.sqrt(efficiency * 1800 * (sstC - 26)) * 1.94384;
  return Math.min(185, Math.max(90, Math.round(maxVelocityKts + 75)));
}
