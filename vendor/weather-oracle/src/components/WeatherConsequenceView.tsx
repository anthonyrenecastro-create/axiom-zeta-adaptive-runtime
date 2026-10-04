/**
 * Weather Consequence Analysis & Immutable Ledger Component
 */

import React from 'react';
import { WeatherTwinWorldState } from '../types/weatherEcology';
import { LedgerEntry } from '../types/hrm';
import { AlertTriangle, Waves, Wind, Users, DollarSign, ShieldAlert, FileText, Lock, ChevronRight } from 'lucide-react';

interface WeatherConsequenceViewProps {
  weatherTwin: WeatherTwinWorldState;
  ledger: LedgerEntry[];
  currentStep: number;
}

export const WeatherConsequenceView: React.FC<WeatherConsequenceViewProps> = ({ weatherTwin, ledger, currentStep }) => {
  const cons = weatherTwin.consequences;

  return (
    <div className="space-y-6">
      {/* Risk Metrics Highlight Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Peak Storm Surge */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Waves className="w-4 h-4 text-cyan-400" /> Peak Storm Surge
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
              cons.peakSurgeFeet > 10 ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
            }`}>
              {cons.coastalInundationRisk}
            </span>
          </div>
          <p className="text-3xl font-extrabold text-cyan-300 font-mono">{cons.peakSurgeFeet} <span className="text-sm font-normal text-slate-400">ft AGL</span></p>
          <p className="text-[11px] text-slate-400">Coastal water level above normal ground elevation</p>
        </div>

        {/* Power Grid Failure Prob */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Wind className="w-4 h-4 text-red-400" /> Power Grid Risk
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-400 font-bold">
              Critical
            </span>
          </div>
          <p className="text-3xl font-extrabold text-red-400 font-mono">{(cons.powerGridFailureProbability * 100).toFixed(0)}%</p>
          <p className="text-[11px] text-slate-400">Probability of transmission & grid blackout</p>
        </div>

        {/* Population Impact */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Users className="w-4 h-4 text-amber-400" /> Population Impact
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300 font-bold">
              Evac Zone
            </span>
          </div>
          <p className="text-3xl font-extrabold text-white font-mono">{(cons.populationAffected / 1000000).toFixed(2)}M</p>
          <p className="text-[11px] text-slate-400">Residents under hurricane & surge warnings</p>
        </div>

        {/* Economic Loss Estimate */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-emerald-400" /> Economic Exposure
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 font-bold">
              Insured Loss
            </span>
          </div>
          <p className="text-3xl font-extrabold text-emerald-400 font-mono">${(cons.economicImpactEstMillionUsd / 1000).toFixed(1)}B</p>
          <p className="text-[11px] text-slate-400">Estimated infrastructure & property exposure</p>
        </div>
      </div>

      {/* Evacuation Directive & Structural Damage Assessment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Evacuation Orders Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-red-400 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-400" /> Civil Protection Evacuation Status
            </span>
            <span className="text-xs font-mono font-bold text-red-300 bg-red-950 px-2.5 py-1 rounded border border-red-800">
              {cons.evacuationOrderLevel}
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Mandatory evacuation ordered for Zones A and B in Hillsborough, Pinellas, Pasco, Manatee, Sarasota, and Charlotte counties. Low-lying barrier islands and mobile home residents must relocate immediately.
          </p>
        </div>

        {/* Wind Damage Tier Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-amber-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" /> Structural Damage Hazard Profile
            </span>
            <span className="text-xs font-mono text-slate-400">Category 4 Impact</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {cons.windDamageTier}
          </p>
        </div>
      </div>

      {/* Immutable Ledger Records */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-sky-400" />
            Immutable Substrate State Transition Ledger
          </h3>
          <span className="text-xs font-mono text-slate-400">Total Steps Recorded: {ledger.length}</span>
        </div>

        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {ledger.slice().reverse().map((entry) => (
            <div
              key={entry.step}
              className={`p-3 rounded-lg border text-xs font-mono transition-all ${
                entry.step === currentStep
                  ? 'bg-sky-950/60 border-sky-600/50 text-white'
                  : 'bg-slate-950 border-slate-800/80 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-sky-400">Step #{entry.step}</span>
                  <span className="text-slate-500">Hash: <span className="text-slate-300">{entry.newStateHash}</span></span>
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-emerald-400">{entry.acceptedContributions.length} Accepted</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              {entry.acceptedContributions.length > 0 && (
                <div className="mt-2 text-[11px] font-sans text-slate-400 bg-slate-900/80 p-2 rounded border border-slate-800">
                  <span className="text-slate-500 font-mono text-[10px] block mb-0.5">Primary Physics Rationale:</span>
                  {entry.acceptedContributions[0].rationale}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
