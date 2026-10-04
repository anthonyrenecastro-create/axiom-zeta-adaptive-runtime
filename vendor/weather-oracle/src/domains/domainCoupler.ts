/**
 * Cross-Domain Coupling Adapter Layer
 * 
 * Flow Architecture:
 * General Weather Patterns Domain (Background Forces, Steering, Shear, SST)
 *    │
 *    ▼ (Coupling Adapter Interface)
 * Injected Boundary Conditions
 *    │
 *    ▼
 * Hurricane Digital Twin Domain (Vortex Intensity, Track Delta, Eyewall Dynamics)
 */

import { WeatherPatternState } from './weatherPatterns/types';
import { evaluateSynopticSteering } from './weatherPatterns/mechanisms';
import { HurricaneTwinState } from './hurricaneTwin/types';
import { calculateMPI } from './hurricaneTwin/mechanisms';

export interface CoupledBoundaryEffect {
  steeringVectorKts: { u: number; v: number };
  synopticSteeringHeadingDeg: number;
  synopticSteeringSpeedKts: number;
  shearImpactStatus: 'FAVORABLE_LOW_SHEAR' | 'MODERATE_RESTRICTIVE' | 'HIGH_DISRUPTIVE_SHEAR';
  thermodynamicMPIKts: number;
  coupledIntensificationRateKtsPer24h: number;
}

export class DomainCoupler {
  /**
   * Evaluates how the synoptic General Weather Patterns domain conditions
   * couple with and drive the internal state of the Hurricane Digital Twin domain.
   */
  public coupleDomains(
    weatherPatterns: WeatherPatternState,
    hurricaneTwin: HurricaneTwinState
  ): { updatedTwin: HurricaneTwinState; couplingEffect: CoupledBoundaryEffect } {
    // 1. Calculate steering vector influence from synoptic weather patterns
    const steering = evaluateSynopticSteering(
      weatherPatterns,
      hurricaneTwin.lat,
      hurricaneTwin.lon
    );

    // 2. Assess environmental shear impact on vortex stability
    const shear = weatherPatterns.ambientEnvironmentalShearKts;
    let shearImpactStatus: 'FAVORABLE_LOW_SHEAR' | 'MODERATE_RESTRICTIVE' | 'HIGH_DISRUPTIVE_SHEAR' = 'FAVORABLE_LOW_SHEAR';
    let shearPenaltyKts = 0;

    if (shear < 12) {
      shearImpactStatus = 'FAVORABLE_LOW_SHEAR';
      shearPenaltyKts = +15; // Low shear allows rapid intensification
    } else if (shear <= 22) {
      shearImpactStatus = 'MODERATE_RESTRICTIVE';
      shearPenaltyKts = -5;
    } else {
      shearImpactStatus = 'HIGH_DISRUPTIVE_SHEAR';
      shearPenaltyKts = -25; // High shear tilts vortex and inhibits core
    }

    // 3. Compute thermodynamic Maximum Potential Intensity (MPI) from SST grid
    const sst = weatherPatterns.seaSurfaceTempGridC;
    const thermodynamicMPI = calculateMPI(sst);

    // 4. Determine coupled 24h intensification trajectory
    const currentWind = hurricaneTwin.vortexCore.maximumSustainedWindKts;
    const mpiHeadroom = thermodynamicMPI - currentWind;
    const coupledRate = Math.round((mpiHeadroom * 0.25) + shearPenaltyKts);

    const couplingEffect: CoupledBoundaryEffect = {
      steeringVectorKts: steering.vectorComponents,
      synopticSteeringHeadingDeg: steering.steeringDirectionDeg,
      synopticSteeringSpeedKts: steering.steeringSpeedKts,
      shearImpactStatus,
      thermodynamicMPIKts: thermodynamicMPI,
      coupledIntensificationRateKtsPer24h: coupledRate
    };

    // Construct coupled Hurricane Twin update with boundary steering and MPI applied
    const updatedTwin: HurricaneTwinState = {
      ...hurricaneTwin,
      headingDeg: steering.steeringDirectionDeg,
      speedKts: steering.steeringSpeedKts,
      maximumPotentialIntensityKts: thermodynamicMPI
    };

    return { updatedTwin, couplingEffect };
  }
}
