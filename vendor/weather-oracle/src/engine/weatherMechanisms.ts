/**
 * Weather & Hurricane Twin Physics Mechanisms
 * Core HRM Mechanisms for Tropical Cyclone Dynamics
 */

import { Mechanism } from './mechanisms';
import { HRMWorldState, Contribution, PerceptualObservation } from '../types/hrm';

export class NHCTrackAssimilatorMechanism implements Mechanism {
  id = 'mech_nhc_assimilator';
  name = 'NHC Track Observation Assimilator';
  description = 'Assimilates National Hurricane Center storm center observations and track cone coordinates into substrate attractor fields.';

  propose(state: Readonly<HRMWorldState>, _observation?: PerceptualObservation): Contribution {
    const storm = state.weatherTwin?.activeStorm;
    if (!storm) {
      return {
        mechanismId: this.id,
        mechanismName: this.name,
        confidence: 0.8,
        activationStrength: 0.8,
        estimatedCost: 10,
        uncertainty: 0.2,
        rationale: 'Assimilating baseline tropical observation vector.',
        fieldDeltas: {},
        diagnostics: { mode: 'fallback' }
      };
    }

    return {
      mechanismId: this.id,
      mechanismName: this.name,
      confidence: 0.95,
      activationStrength: 0.95,
      estimatedCost: 15,
      uncertainty: 0.05,
      rationale: `NHC Feed Assimilation: ${storm.name} at ${storm.centralPressureMb} mb, ${storm.maxWindKts} kts wind. Track vector aligned.`,
      fieldDeltas: {
        node_0: -0.5, // Central pressure delta
        node_1: +1.2  // Max wind speed delta
      },
      diagnostics: { centralPressureMb: storm.centralPressureMb, maxWindKts: storm.maxWindKts }
    };
  }
}

export class LatentHeatConvectionMechanism implements Mechanism {
  id = 'mech_latent_heat_convection';
  name = 'Thermodynamic Latent Heat Convection';
  description = 'Models core convective enthalpy flux from sea surface temperature (SST > 26.5°C) driving rapid eyewall pressure drop.';

  propose(state: Readonly<HRMWorldState>, _observation?: PerceptualObservation): Contribution {
    const gridPoints = state.weatherTwin?.gridPoints || [];
    const eyeGrid = gridPoints.find(g => g.sectorName.includes('Eye')) || gridPoints[0];
    const sst = eyeGrid?.seaSurfaceTempC ?? 29.5;
    const cape = eyeGrid?.capeJkg ?? 2800;
    const shear = eyeGrid?.verticalShearKts ?? 12;

    const thermodynamicFuel = Math.max(0, (sst - 26.0) * 0.2) + (cape / 4000) * 0.3;

    let deltaPressure = 0;
    let deltaWind = 0;
    let rationale = '';

    if (thermodynamicFuel > 0.6 && shear < 18) {
      deltaPressure = -2.5; // Rapid pressure drop
      deltaWind = +4.0;     // Wind increase
      rationale = `High SST (${sst.toFixed(1)}°C) and low shear (${shear} kts) fueling rapid convective intensification (+4 kts wind).`;
    } else if (shear >= 22) {
      deltaPressure = +1.5;
      deltaWind = -3.0;
      rationale = `Strong vertical shear (${shear} kts) disrupting convective core; storm weakening (-3 kts wind).`;
    } else {
      deltaPressure = -0.5;
      deltaWind = +1.0;
      rationale = `Steady thermodynamic equilibrium over warm water (${sst.toFixed(1)}°C).`;
    }

    return {
      mechanismId: this.id,
      mechanismName: this.name,
      confidence: 0.90,
      activationStrength: 0.90,
      estimatedCost: 12,
      uncertainty: 0.10,
      rationale,
      fieldDeltas: {
        node_0: deltaPressure,
        node_1: deltaWind
      },
      diagnostics: { sst, cape, shear }
    };
  }
}

export class TroughSteeringMechanism implements Mechanism {
  id = 'mech_baroclinic_trough_steering';
  name = 'Synoptic Steering & Trough Coupling';
  description = 'Computes steering vector from upper-level trough pressure gradients and subtropical high-pressure ridge positioning.';

  propose(state: Readonly<HRMWorldState>, _observation?: PerceptualObservation): Contribution {
    const storm = state.weatherTwin?.activeStorm;
    const speed = storm?.movementSpeedKts ?? 14;

    return {
      mechanismId: this.id,
      mechanismName: this.name,
      confidence: 0.88,
      activationStrength: 0.88,
      estimatedCost: 10,
      uncertainty: 0.12,
      rationale: `Subtropical ridge steering storm north-eastward at ${speed} knots. Trough interaction imminent at Step +12.`,
      fieldDeltas: {
        node_5: 0.85
      },
      diagnostics: { movementSpeedKts: speed }
    };
  }
}

export class SurgeHydrodynamicsMechanism implements Mechanism {
  id = 'mech_surge_hydrodynamics';
  name = 'Coastal Storm Surge Hydrodynamics';
  description = 'Calculates ocean water buildup and storm surge height based on central pressure deficit, wind stress, and coastal shelf bathymetry.';

  propose(state: Readonly<HRMWorldState>, _observation?: PerceptualObservation): Contribution {
    const storm = state.weatherTwin?.activeStorm;
    const pressure = storm?.centralPressureMb ?? 940;
    const maxWind = storm?.maxWindKts ?? 120;

    const pressureDeficit = Math.max(0, 1013 - pressure);
    const estimatedSurgeFt = Number((pressureDeficit * 0.12 + (maxWind / 110) ** 2 * 6.5).toFixed(1));

    return {
      mechanismId: this.id,
      mechanismName: this.name,
      confidence: 0.92,
      activationStrength: 0.92,
      estimatedCost: 14,
      uncertainty: 0.08,
      rationale: `Extreme pressure deficit (${pressureDeficit} mb) & ${maxWind} kt winds projecting peak storm surge of ${estimatedSurgeFt} ft at landfall zone.`,
      fieldDeltas: {
        node_4: estimatedSurgeFt
      },
      diagnostics: { pressureDeficit, estimatedSurgeFt }
    };
  }
}

export class LandFrictionDecayMechanism implements Mechanism {
  id = 'mech_land_friction_decay';
  name = 'Landfall Surface Friction & Friction Decay';
  description = 'Evaluates kinetic energy dissipation and dry air entrainment as the hurricane center crosses coastline onto land.';

  propose(state: Readonly<HRMWorldState>, _observation?: PerceptualObservation): Contribution {
    const isLandfall = state.metadata.step > 15;

    if (!isLandfall) {
      return {
        mechanismId: this.id,
        mechanismName: this.name,
        confidence: 0.95,
        activationStrength: 0.10,
        estimatedCost: 5,
        uncertainty: 0.05,
        rationale: 'Storm remains over open warm ocean water; maritime thermodynamic energy supply fully intact.',
        fieldDeltas: {},
        diagnostics: { isLandfall: false }
      };
    }

    return {
      mechanismId: this.id,
      mechanismName: this.name,
      confidence: 0.94,
      activationStrength: 0.94,
      estimatedCost: 15,
      uncertainty: 0.06,
      rationale: 'Landfall friction active. Surface friction and lack of oceanic sensible heat causing rapid vortex spin-down.',
      fieldDeltas: {
        node_0: +12, // Pressure rising
        node_1: -25  // Wind dropping
      },
      diagnostics: { isLandfall: true }
    };
  }
}

export function getWeatherMechanisms(): Mechanism[] {
  return [
    new NHCTrackAssimilatorMechanism(),
    new LatentHeatConvectionMechanism(),
    new TroughSteeringMechanism(),
    new SurgeHydrodynamicsMechanism(),
    new LandFrictionDecayMechanism()
  ];
}
