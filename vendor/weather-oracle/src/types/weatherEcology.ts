/**
 * Weather Patterns & Hurricane Twin Substrate
 * Multi-Feed Framework Type Definitions
 */

import { ValidatedWeatherState } from '../engine/observationAdapters';

export type StormCategory = 'TD' | 'TS' | 'Cat1' | 'Cat2' | 'Cat3' | 'Cat4' | 'Cat5' | 'Extratropical';

export interface StormIdentity {
  id: string; // e.g. "AL092026"
  name: string; // e.g. "Hurricane Milton"
  basin: 'Atlantic' | 'Eastern Pacific' | 'Central Pacific' | 'Gulf of Mexico';
  status: StormCategory;
  lat: number;
  lon: number;
  centralPressureMb: number;
  maxWindKts: number;
  maxWindMph: number;
  movementDirection: string; // e.g. "ENE at 14 mph"
  movementSpeedKts: number;
  eyeDiameterNm: number;
  advisories: string[];
  lastUpdated: string;
}

export interface TrackForecastPoint {
  step: number;
  hoursFromNow: number;
  lat: number;
  lon: number;
  maxWindKts: number;
  pressureMb: number;
  category: StormCategory;
  coneRadiusKm: number;
  locationName: string;
}

export interface NWSAlert {
  id: string;
  event: string; // e.g. "Hurricane Warning", "Storm Surge Watch", "Flash Flood Emergency"
  severity: 'Extreme' | 'Severe' | 'Moderate' | 'Minor';
  urgency: 'Immediate' | 'Expected' | 'Future';
  headline: string;
  areaDesc: string;
  effective: string;
  expires: string;
  description: string;
  instruction: string;
}

export interface OpenMeteoGridPoint {
  sectorName: string;
  lat: number;
  lon: number;
  temperature2mC: number;
  relativeHumidityPercent: number;
  surfacePressureMb: number;
  windSpeed10mKts: number;
  windDirectionDeg: number;
  precipitationMmHr: number;
  seaSurfaceTempC: number;
  capeJkg: number; // Convective Available Potential Energy
  verticalShearKts: number;
}

export interface ModelEnsembleVote {
  modelName: string; // e.g., "NHC Official", "HRM Physics Substrate", "GFS Model", "ECMWF European", "HWRF Hurricane Model"
  intensityKts: number;
  landfallHour: number;
  trackErrorKm: number;
  confidence: number;
  rationale: string;
}

export interface MechanismDisagreementMetrics {
  trackSpreadKm: number; // Disagreement in storm center path
  intensitySpreadKts: number; // Disagreement in wind speed peak
  landfallTimingSpreadHours: number;
  consensusIndex: number; // [0, 1] - 1.0 means full model agreement
  primaryUncertaintyFactor: string; // e.g. "Trough steering timing vs. Ridge collapse"
  modelVotes: ModelEnsembleVote[];
}

export interface HurricaneConsequenceAnalysis {
  peakSurgeFeet: number;
  coastalInundationRisk: 'Low' | 'Moderate' | 'High' | 'Catastrophic';
  windDamageTier: string;
  inlandRainfallInches: number;
  powerGridFailureProbability: number; // [0, 1]
  populationAffected: number;
  economicImpactEstMillionUsd: number;
  evacuationOrderLevel: 'None' | 'Voluntary' | 'Mandatory Coastal' | 'Mandatory Region-Wide';
}
import { WeatherPatternState } from '../domains/weatherPatterns/types';
import { HurricaneTwinState } from '../domains/hurricaneTwin/types';
import { CoupledBoundaryEffect } from '../domains/domainCoupler';

export interface WeatherTwinWorldState {
  activeStorm: StormIdentity;
  trackForecast: TrackForecastPoint[];
  activeAlerts: NWSAlert[];
  gridPoints: OpenMeteoGridPoint[];
  modelDisagreement: MechanismDisagreementMetrics;
  consequences: HurricaneConsequenceAnalysis;
  validatedObservationState?: ValidatedWeatherState;
  weatherPatternDomain?: WeatherPatternState;
  hurricaneTwinDomain?: HurricaneTwinState;
  coupledBoundaryEffect?: CoupledBoundaryEffect;
  lastAssimilatedStep: number;
  dataSourcesStatus: {
    nhcFeed: 'LIVE' | 'SIMULATED' | 'OFFLINE';
    nwsApi: 'LIVE' | 'SIMULATED' | 'OFFLINE';
    openMeteo: 'LIVE' | 'SIMULATED' | 'OFFLINE';
    axiomHRMWeatherSeer: 'LIVE' | 'SIMULATED' | 'OFFLINE' | 'ACTIVE';
    hrmEcology: 'ACTIVE';
    geminiReasoning: 'ONLINE' | 'FALLBACK';
  };
}
