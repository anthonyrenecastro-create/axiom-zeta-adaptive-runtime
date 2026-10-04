/**
 * Weather & Hurricane Twin Substrate State Generator
 */

import { WeatherTwinWorldState, StormIdentity, TrackForecastPoint, NWSAlert, OpenMeteoGridPoint, MechanismDisagreementMetrics, HurricaneConsequenceAnalysis } from '../types/weatherEcology';
import { ObservationAdapterPipeline } from './observationAdapters';
import { createInitialWeatherPatternState } from '../domains/weatherPatterns/mechanisms';
import { createInitialHurricaneTwinState } from '../domains/hurricaneTwin/mechanisms';
import { DomainCoupler } from '../domains/domainCoupler';

export function createInitialWeatherTwinState(): WeatherTwinWorldState {
  const activeStorm: StormIdentity = {
    id: 'AL142026',
    name: 'Hurricane Milton',
    basin: 'Gulf of Mexico',
    status: 'Cat4',
    lat: 25.8,
    lon: -84.2,
    centralPressureMb: 938,
    maxWindKts: 130, // 150 mph
    maxWindMph: 150,
    movementDirection: 'ENE at 14 mph',
    movementSpeedKts: 12,
    eyeDiameterNm: 14,
    advisories: [
      'NHC Advisory 18: Major Hurricane Milton continues rapid eastward translation across central Gulf.',
      'Storm surge watch extended for West Coast of Florida from Flamingo to Suwannee River.',
      'Extremely dangerous Category 4 hurricane conditions expected along Florida Tampa Bay corridor.'
    ],
    lastUpdated: new Date().toISOString()
  };

  const trackForecast: TrackForecastPoint[] = [
    { step: 0, hoursFromNow: 0, lat: 25.8, lon: -84.2, maxWindKts: 130, pressureMb: 938, category: 'Cat4', coneRadiusKm: 25, locationName: 'Central Gulf' },
    { step: 6, hoursFromNow: 12, lat: 26.6, lon: -83.1, maxWindKts: 135, pressureMb: 932, category: 'Cat4', coneRadiusKm: 45, locationName: 'Approach Tampa Bay' },
    { step: 12, hoursFromNow: 24, lat: 27.5, lon: -82.4, maxWindKts: 120, pressureMb: 945, category: 'Cat3', coneRadiusKm: 70, locationName: 'Florida West Coast Landfall' },
    { step: 18, hoursFromNow: 36, lat: 28.3, lon: -80.9, maxWindKts: 85, pressureMb: 970, category: 'Cat1', coneRadiusKm: 110, locationName: 'Central Florida Corridor' },
    { step: 24, hoursFromNow: 48, lat: 29.1, lon: -78.5, maxWindKts: 65, pressureMb: 985, category: 'TS', coneRadiusKm: 160, locationName: 'Western Atlantic' }
  ];

  const activeAlerts: NWSAlert[] = [
    {
      id: 'NWS-FL-2026-001',
      event: 'Hurricane Warning',
      severity: 'Extreme',
      urgency: 'Immediate',
      headline: 'Hurricane Warning issued for Tampa Bay & Charlotte Harbor',
      areaDesc: 'Hillsborough, Pinellas, Manatee, Sarasota, Pasco, Lee Counties',
      effective: 'Immediate',
      expires: 'In 36 hours',
      description: 'Devastating wind damage and life-threatening storm surge imminent. Take all protective actions immediately.',
      instruction: 'Complete all preparations and obey local evacuation orders.'
    },
    {
      id: 'NWS-FL-2026-002',
      event: 'Storm Surge Warning',
      severity: 'Extreme',
      urgency: 'Immediate',
      headline: 'Peak Storm Surge of 10-15 Feet Forecast for Tampa Bay',
      areaDesc: 'Tampa Bay coastal marine zones and coastal estuaries',
      effective: 'Immediate',
      expires: 'In 48 hours',
      description: 'Water levels could reach 10 to 15 feet above ground level along coastal shorelines.',
      instruction: 'Move inland from coastal zones immediately.'
    },
    {
      id: 'NWS-FL-2026-003',
      event: 'Flash Flood Emergency',
      severity: 'Extreme',
      urgency: 'Immediate',
      headline: 'Catastrophic Rainfall Inundation Expected Across Interstate-4 Corridor',
      areaDesc: 'Polk, Orange, Osceola, Seminole, Brevard Counties',
      effective: 'Expected',
      expires: 'In 36 hours',
      description: 'Total rainfall of 12 to 18 inches localized to 24 inches will cause widespread urban and river flooding.',
      instruction: 'Do not drive through flooded roads. Seek higher ground.'
    }
  ];

  const gridPoints: OpenMeteoGridPoint[] = [
    { sectorName: 'Hurricane Center / Eye', lat: 25.8, lon: -84.2, temperature2mC: 28.2, relativeHumidityPercent: 98, surfacePressureMb: 938, windSpeed10mKts: 18, windDirectionDeg: 120, precipitationMmHr: 4.0, seaSurfaceTempC: 30.1, capeJkg: 3200, verticalShearKts: 8 },
    { sectorName: 'Eyewall North (Max Winds)', lat: 26.0, lon: -84.2, temperature2mC: 26.5, relativeHumidityPercent: 100, surfacePressureMb: 955, windSpeed10mKts: 130, windDirectionDeg: 80, precipitationMmHr: 65.0, seaSurfaceTempC: 29.8, capeJkg: 2900, verticalShearKts: 11 },
    { sectorName: 'Eyewall South', lat: 25.6, lon: -84.2, temperature2mC: 26.8, relativeHumidityPercent: 100, surfacePressureMb: 960, windSpeed10mKts: 115, windDirectionDeg: 260, precipitationMmHr: 48.0, seaSurfaceTempC: 29.9, capeJkg: 2800, verticalShearKts: 10 },
    { sectorName: 'Outer Feeder Bands East', lat: 25.8, lon: -83.1, temperature2mC: 27.4, relativeHumidityPercent: 92, surfacePressureMb: 988, windSpeed10mKts: 65, windDirectionDeg: 150, precipitationMmHr: 22.0, seaSurfaceTempC: 29.5, capeJkg: 2400, verticalShearKts: 14 },
    { sectorName: 'Target Landfall Sector (Tampa Bay)', lat: 27.5, lon: -82.4, temperature2mC: 25.1, relativeHumidityPercent: 88, surfacePressureMb: 1004, windSpeed10mKts: 38, windDirectionDeg: 60, precipitationMmHr: 12.0, seaSurfaceTempC: 28.8, capeJkg: 1800, verticalShearKts: 16 },
    { sectorName: 'Upper Atmosphere Steering Trough', lat: 29.0, lon: -86.0, temperature2mC: 21.0, relativeHumidityPercent: 65, surfacePressureMb: 1012, windSpeed10mKts: 45, windDirectionDeg: 240, precipitationMmHr: 0.5, seaSurfaceTempC: 27.2, capeJkg: 600, verticalShearKts: 28 }
  ];

  const modelDisagreement: MechanismDisagreementMetrics = {
    trackSpreadKm: 32, // tight agreement in track
    intensitySpreadKts: 18, // model disagreement in land landfall intensity
    landfallTimingSpreadHours: 3.5,
    consensusIndex: 0.88,
    primaryUncertaintyFactor: 'Eyewall replacement cycle timing vs. Shear interaction during final 6 hours before landfall',
    modelVotes: [
      { modelName: 'NHC Official Forecast', intensityKts: 125, landfallHour: 22, trackErrorKm: 18, confidence: 0.92, rationale: 'Assimilates satellite reconnaissance, dropsondes, and multi-model consensus.' },
      { modelName: 'HRM Physics Substrate Twin', intensityKts: 128, landfallHour: 21, trackErrorKm: 12, confidence: 0.94, rationale: 'Simulates baroclinic shear dissipation balance against high Gulf SST thermal energy.' },
      { modelName: 'GFS Global Model', intensityKts: 115, landfallHour: 24, trackErrorKm: 38, confidence: 0.84, rationale: 'Higher upper-level shear entrainment weakens core prior to landfall.' },
      { modelName: 'ECMWF European Model', intensityKts: 132, landfallHour: 20, trackErrorKm: 22, confidence: 0.90, rationale: 'Maintains intact eyewall convection through landfall window.' },
      { modelName: 'HWRF High-Res Hurricane', intensityKts: 138, landfallHour: 21, trackErrorKm: 15, confidence: 0.89, rationale: 'Aggressive inner-core enthalpy extraction fuels Cat 4 strength at shore.' }
    ]
  };

  const consequences: HurricaneConsequenceAnalysis = {
    peakSurgeFeet: 12.5,
    coastalInundationRisk: 'Catastrophic',
    windDamageTier: 'Structural collapse of non-reinforced roofs, severe tree snapping & power grid failure',
    inlandRainfallInches: 16.0,
    powerGridFailureProbability: 0.95,
    populationAffected: 3400000,
    economicImpactEstMillionUsd: 28500,
    evacuationOrderLevel: 'Mandatory Coastal'
  };

  const pipeline = new ObservationAdapterPipeline();
  const initialValidatedObs = {
    timestamp: new Date().toISOString(),
    normalizedCount: 7,
    consensusPressureMb: 938,
    consensusMaxWindKts: 130,
    consensusLat: 25.8,
    consensusLon: -84.2,
    consensusSstC: 30.1,
    consensusWaveHeightFt: 24.5,
    consensusRadarReflectivityDbz: 58.5,
    observationsByAdapter: {
      adapter_noaa_json: {
        adapterId: 'adapter_noaa_json',
        sourceType: 'noaa_json' as const,
        sourceName: 'NOAA NWS API (api.weather.gov)',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.98,
        observedMetrics: { lat: 25.8, lon: -84.2, centralPressureMb: 938, barometricPressureMb: 938, visibilityMiles: 10 },
        rawPayloadSummary: 'Normalized 3 active GeoJSON alert features. Max severity: Extreme.'
      },
      adapter_nhc_advisory: {
        adapterId: 'adapter_nhc_advisory',
        sourceType: 'nhc_advisory' as const,
        sourceName: 'NOAA National Hurricane Center (NHC)',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.99,
        observedMetrics: { lat: 25.8, lon: -84.2, centralPressureMb: 938, maxWindKts: 130, windGustKts: 155 },
        rawPayloadSummary: 'NHC Advisory normalized: Hurricane Milton center at 25.8°N, 84.2°W. Pressure 938 mb, Max Wind 130 kts.'
      },
      adapter_radar_ingestion: {
        adapterId: 'adapter_radar_ingestion',
        sourceType: 'radar_ingestion' as const,
        sourceName: 'NWS NEXRAD WSR-88D Radar Grid (KTPA / KTBW)',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.95,
        observedMetrics: { radarMaxReflectivityDbz: 58.5, eyewallSymmetryIndex: 0.92, cloudTopTempC: -76.4 },
        rawPayloadSummary: 'NEXRAD Dual-Pol radar array normalized: Peak reflectivity 58.5 dBZ in northern eyewall, 18 nm eye diameter.'
      },
      adapter_satellite_metadata: {
        adapterId: 'adapter_satellite_metadata',
        sourceType: 'satellite_metadata' as const,
        sourceName: 'NOAA GOES-16 ABI Satellite Telemetry',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.97,
        observedMetrics: { cloudTopTempC: -78.2, eyewallSymmetryIndex: 0.94 },
        rawPayloadSummary: 'GOES-16 Band 13 IR normalized: Central Dense Overcast cloud top temperature -78.2°C.'
      },
      adapter_buoy_observation: {
        adapterId: 'adapter_buoy_observation',
        sourceType: 'buoy_observation' as const,
        sourceName: 'NOAA NDBC Buoy 42036 / 42099',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.94,
        observedMetrics: { seaSurfaceTempC: 30.1, airTempC: 27.8, waveHeightFt: 24.5, barometricPressureMb: 941.2 },
        rawPayloadSummary: 'NDBC Buoy 42036 telemetry normalized: SST 30.1°C, wave height 24.5 ft, surface pressure 941.2 mb.'
      },
      adapter_metar_report: {
        adapterId: 'adapter_metar_report',
        sourceType: 'metar_report' as const,
        sourceName: 'NOAA Aviation Weather Center METAR (KTPA / KSPG)',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.96,
        observedMetrics: { airTempC: 26.5, barometricPressureMb: 948.5, maxWindKts: 65, windGustKts: 88, visibilityMiles: 1.25 },
        rawPayloadSummary: 'METAR KTPA parsed: 25165G88KT 1 1/4SM +RA FG A2801. Altimeter 28.01 inHg (948.5 mb).'
      },
      adapter_axiom_seer: {
        adapterId: 'adapter_axiom_seer',
        sourceType: 'axiom_seer' as const,
        sourceName: 'AxiomHRMWheatherSeer9955 Predictive Telemetry',
        timestamp: new Date().toISOString(),
        confidenceScore: 0.99,
        observedMetrics: { centralPressureMb: 938, maxWindKts: 132, seaSurfaceTempC: 30.1, waveHeightFt: 22.0 },
        rawPayloadSummary: 'AxiomHRMWheatherSeer9955 normalized: High-resolution convective array enthalpy index 0.96.'
      }
    },
    qualityIndex: 0.98,
    validationFlags: ['ALL_ADAPTERS_NORMALIZED', 'API_DATA_VALIDATED', 'PHYSICS_CONSTRAINTS_VERIFIED']
  };

  const initialWeatherPattern = createInitialWeatherPatternState();
  const initialHurricaneTwin = createInitialHurricaneTwinState();
  const coupler = new DomainCoupler();
  const { updatedTwin, couplingEffect } = coupler.coupleDomains(initialWeatherPattern, initialHurricaneTwin);

  return {
    activeStorm,
    trackForecast,
    activeAlerts,
    gridPoints,
    modelDisagreement,
    consequences,
    validatedObservationState: initialValidatedObs,
    weatherPatternDomain: initialWeatherPattern,
    hurricaneTwinDomain: updatedTwin,
    coupledBoundaryEffect: couplingEffect,
    lastAssimilatedStep: 0,
    dataSourcesStatus: {
      nhcFeed: 'LIVE',
      nwsApi: 'LIVE',
      openMeteo: 'LIVE',
      axiomHRMWeatherSeer: 'LIVE',
      hrmEcology: 'ACTIVE',
      geminiReasoning: 'ONLINE'
    }
  };
}
