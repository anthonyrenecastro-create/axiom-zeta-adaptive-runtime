/**
 * Weather & Hurricane Substrate Cycle Evolution Manager
 */

import { HRMWorldState, Contribution } from '../types/hrm';
import { StormCategory } from '../types/weatherEcology';

export function applyWeatherCycle(nextState: HRMWorldState, acceptedContributions: Contribution[]): void {
  if (!nextState.weatherTwin) return;

  const step = nextState.metadata.step;
  const twin = nextState.weatherTwin;

  // Track progress along 24-step forecast track
  const trackIndex = Math.min(twin.trackForecast.length - 1, Math.floor(step / 5));
  const currentTrackPoint = twin.trackForecast[trackIndex] || twin.trackForecast[0];

  // Evaluate net pressure and wind deltas proposed by accepted weather mechanisms
  let netPressureDelta = 0;
  let netWindDelta = 0;

  for (const contrib of acceptedContributions) {
    if (contrib.fieldDeltas) {
      if (contrib.fieldDeltas['node_0'] !== undefined) {
        netPressureDelta += contrib.fieldDeltas['node_0'];
      }
      if (contrib.fieldDeltas['node_1'] !== undefined) {
        netWindDelta += contrib.fieldDeltas['node_1'];
      }
    }
  }

  // Update Storm Identity
  const prevPressure = twin.activeStorm.centralPressureMb;
  const newPressure = Math.max(910, Math.min(1010, Math.round(prevPressure + netPressureDelta)));
  
  const prevWind = twin.activeStorm.maxWindKts;
  const newWind = Math.max(25, Math.min(175, Math.round(prevWind + netWindDelta)));

  // Determine category
  let newCategory: StormCategory = 'TS';
  if (newWind >= 137) newCategory = 'Cat5';
  else if (newWind >= 113) newCategory = 'Cat4';
  else if (newWind >= 96) newCategory = 'Cat3';
  else if (newWind >= 83) newCategory = 'Cat2';
  else if (newWind >= 64) newCategory = 'Cat1';
  else if (newWind >= 34) newCategory = 'TS';
  else newCategory = 'TD';

  // Smooth position interpolation along track forecast
  const targetLat = currentTrackPoint.lat;
  const targetLon = currentTrackPoint.lon;
  const newLat = Number((twin.activeStorm.lat + (targetLat - twin.activeStorm.lat) * 0.25).toFixed(2));
  const newLon = Number((twin.activeStorm.lon + (targetLon - twin.activeStorm.lon) * 0.25).toFixed(2));

  twin.activeStorm = {
    ...twin.activeStorm,
    lat: newLat,
    lon: newLon,
    centralPressureMb: newPressure,
    maxWindKts: newWind,
    maxWindMph: Math.round(newWind * 1.15078),
    status: newCategory,
    lastUpdated: new Date().toISOString()
  };

  // Update Open-Meteo Grid Points
  twin.gridPoints = twin.gridPoints.map((gp, idx) => {
    if (idx === 0) { // Eye
      return {
        ...gp,
        surfacePressureMb: newPressure,
        windSpeed10mKts: Math.round(newWind * 0.15)
      };
    } else if (idx === 1) { // Eyewall North
      return {
        ...gp,
        surfacePressureMb: newPressure + 15,
        windSpeed10mKts: newWind
      };
    } else if (idx === 2) { // Eyewall South
      return {
        ...gp,
        surfacePressureMb: newPressure + 20,
        windSpeed10mKts: Math.round(newWind * 0.88)
      };
    }
    return gp;
  });

  // Calculate updated storm surge and consequences
  const pressureDeficit = Math.max(0, 1013 - newPressure);
  const surgeFeet = Number((pressureDeficit * 0.12 + (newWind / 110) ** 2 * 6.5).toFixed(1));

  twin.consequences = {
    ...twin.consequences,
    peakSurgeFeet: surgeFeet,
    coastalInundationRisk: surgeFeet > 12 ? 'Catastrophic' : surgeFeet > 8 ? 'High' : 'Moderate',
    powerGridFailureProbability: Math.min(0.99, Number((0.4 + (newWind / 140) * 0.55).toFixed(2))),
    populationAffected: Math.min(5000000, 2000000 + step * 80000)
  };

  // Update Model Disagreement metrics
  twin.modelDisagreement = {
    ...twin.modelDisagreement,
    trackSpreadKm: Math.max(15, Math.round(32 + Math.sin(step * 0.8) * 12)),
    intensitySpreadKts: Math.max(8, Math.round(18 + Math.cos(step * 0.5) * 6)),
    consensusIndex: Number((0.85 + Math.sin(step * 0.3) * 0.08).toFixed(2))
  };

  twin.lastAssimilatedStep = step;
}
