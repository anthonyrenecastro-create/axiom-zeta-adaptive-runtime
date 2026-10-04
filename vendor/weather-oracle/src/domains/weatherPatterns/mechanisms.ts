/**
 * Synoptic Weather Patterns Mechanisms
 * Independent physics and empirical mechanisms acting on regional weather systems.
 */

import { WeatherPatternState, SynopticFeature } from './types';

export function createInitialWeatherPatternState(): WeatherPatternState {
  const bermudaHigh: SynopticFeature = {
    id: 'synoptic_bermuda_high',
    name: 'Subtropical Ridge (Bermuda High)',
    type: 'subtropical_high',
    centerLat: 31.5,
    centerLon: -68.0,
    pressureMb: 1024,
    steeringVectorKts: { u: -12, v: 8 },
    steeringAngleDeg: 300,
    influenceRadiusNm: 850
  };

  const midTrough: SynopticFeature = {
    id: 'synoptic_trough_east_coast',
    name: 'Mid-Latitude Shortwave Trough',
    type: 'upper_trough',
    centerLat: 34.0,
    centerLon: -88.5,
    pressureMb: 1004,
    steeringVectorKts: { u: 18, v: 22 },
    steeringAngleDeg: 40,
    influenceRadiusNm: 500
  };

  return {
    timestamp: new Date().toISOString(),
    jetStreamLatitude: 38.2,
    mjoPhase: 3,
    teleconnectionIndices: {
      naoIndex: +0.85,
      amoIndex: +0.42,
      pnaIndex: -0.31
    },
    synopticFeatures: [bermudaHigh, midTrough],
    ambientEnvironmentalShearKts: 16.5,
    meanSteeringFlowKts: 14.0,
    meanSteeringDirectionDeg: 315,
    seaSurfaceTempGridC: 30.1
  };
}

export function evaluateSynopticSteering(state: WeatherPatternState, stormLat: number, stormLon: number) {
  // Compute vector influence of Subtropical High vs Mid-Latitude Trough
  let netU = 0;
  let netV = 0;
  let totalWeight = 0;

  for (const feat of state.synopticFeatures) {
    const dLat = stormLat - feat.centerLat;
    const dLon = stormLon - feat.centerLon;
    const distNm = Math.sqrt(dLat * dLat + dLon * dLon) * 60;
    
    // Weight decays quadratically with distance
    const weight = Math.max(0, 1 - distNm / feat.influenceRadiusNm);
    if (weight > 0) {
      netU += feat.steeringVectorKts.u * weight;
      netV += feat.steeringVectorKts.v * weight;
      totalWeight += weight;
    }
  }

  if (totalWeight > 0) {
    netU /= totalWeight;
    netV /= totalWeight;
  } else {
    netU = -10;
    netV = 10;
  }

  const speedKts = Math.sqrt(netU * netU + netV * netV);
  let angleDeg = (Math.atan2(netV, netU) * 180) / Math.PI;
  if (angleDeg < 0) angleDeg += 360;

  return {
    steeringSpeedKts: Number(speedKts.toFixed(1)),
    steeringDirectionDeg: Math.round(angleDeg),
    vectorComponents: { u: Number(netU.toFixed(1)), v: Number(netV.toFixed(1)) },
    ambientShearKts: state.ambientEnvironmentalShearKts
  };
}
