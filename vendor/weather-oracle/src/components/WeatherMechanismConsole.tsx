/**
 * Weather Mechanism Forecasts & Model Disagreement Console Component
 */

import React from 'react';
import { WeatherTwinWorldState } from '../types/weatherEcology';
import { Mechanism } from '../engine/mechanisms';
import { getWeatherMechanisms } from '../engine/weatherMechanisms';
import { Scale, Target, Wind, Compass, AlertCircle, ShieldCheck, Activity, BarChart2 } from 'lucide-react';

interface WeatherMechanismConsoleProps {
  weatherTwin: WeatherTwinWorldState;
}

export const WeatherMechanismConsole: React.FC<WeatherMechanismConsoleProps> = ({ weatherTwin }) => {
  const disagreement = weatherTwin.modelDisagreement;
  const mechanisms: Mechanism[] = getWeatherMechanisms();

  return (
    <div className="space-y-6">
      {/* Top Section: Model Disagreement & Spread Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Metric 1: Track Spread */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><Compass className="w-4 h-4 text-sky-400" /> Track Spread</span>
            <span className="text-[10px] font-mono text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
              High Confidence
            </span>
          </div>
          <p className="text-2xl font-extrabold text-white font-mono">{disagreement.trackSpreadKm} <span className="text-sm font-normal text-slate-400">km</span></p>
          <p className="text-[11px] text-slate-400">Ensemble track variance across model guidance</p>
        </div>

        {/* Metric 2: Intensity Spread */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><Wind className="w-4 h-4 text-amber-400" /> Intensity Spread</span>
            <span className="text-[10px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800">
              Shear Uncertainty
            </span>
          </div>
          <p className="text-2xl font-extrabold text-white font-mono">{disagreement.intensitySpreadKts} <span className="text-sm font-normal text-slate-400">kts</span></p>
          <p className="text-[11px] text-slate-400">Peak wind speed disagreement at landfall</p>
        </div>

        {/* Metric 3: Landfall Timing Spread */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><Target className="w-4 h-4 text-purple-400" /> Timing Window</span>
            <span className="text-[10px] font-mono text-purple-400 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
              Steering Speed
            </span>
          </div>
          <p className="text-2xl font-extrabold text-white font-mono">±{disagreement.landfallTimingSpreadHours} <span className="text-sm font-normal text-slate-400">hours</span></p>
          <p className="text-[11px] text-slate-400">Estimated landfall window variance</p>
        </div>

        {/* Metric 4: Model Consensus Index */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-emerald-400" /> Consensus Index</span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
              HRM Substrate
            </span>
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 font-mono">{(disagreement.consensusIndex * 100).toFixed(0)}%</p>
          <p className="text-[11px] text-slate-400">Overall ensemble convergence score</p>
        </div>
      </div>

      {/* Uncertainty Factor Highlight */}
      <div className="bg-slate-900 border border-amber-900/40 rounded-xl p-4 flex items-center gap-3">
        <div className="p-2.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-xl shrink-0">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div>
          <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block">Primary Meteorological Uncertainty Driver</span>
          <p className="text-xs text-slate-200 mt-0.5 font-medium">{disagreement.primaryUncertaintyFactor}</p>
        </div>
      </div>

      {/* Ensemble Model Guidance Votes Comparison */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-sky-400" />
            Ensemble Guidance Model Votes & Intensity Predictions
          </h3>
          <span className="text-xs font-mono text-slate-400">5 Active Numerical & Physics Models</span>
        </div>

        <div className="space-y-3">
          {disagreement.modelVotes.map((vote, i) => (
            <div key={i} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono ${
                    vote.modelName.includes('HRM')
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-slate-800 text-slate-200'
                  }`}>
                    {vote.modelName}
                  </span>
                  <span className="text-xs text-slate-400">Track Error: <span className="text-slate-200 font-mono">{vote.trackErrorKm} km</span></span>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="text-slate-400">Landfall Intensity:</span>
                  <span className="text-red-400 font-extrabold text-sm">{vote.intensityKts} kts</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-sky-300 font-semibold">T+{vote.landfallHour}h</span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">{vote.rationale}</p>
            </div>
          ))}
        </div>
      </div>

      {/* HRM Physics Mechanisms Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-amber-400" />
            Active HRM Weather Physics Substrate Mechanisms
          </h3>
          <span className="text-xs font-mono text-slate-400">{mechanisms.length} Mechanisms Registered</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mechanisms.map(mech => (
            <div key={mech.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-100">{mech.name}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-300 uppercase">
                  Physics Substrate
                </span>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed">{mech.description}</p>

              <div className="pt-2 border-t border-slate-900 flex justify-between items-center text-xs font-mono">
                <span className="text-slate-500">Status:</span>
                <span className="text-emerald-400 font-bold">Active Substrate</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
