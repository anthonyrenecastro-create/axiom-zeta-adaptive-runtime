/**
 * Gemini Weather Intelligence Console Component
 * Provides Explanation, Feed Comparison, and Interactive Hypothesis Generation
 */

import React, { useState } from 'react';
import { WeatherTwinWorldState } from '../types/weatherEcology';
import { Brain, Sparkles, Send, RefreshCw, Layers, Compass, HelpCircle, CheckCircle, AlertTriangle } from 'lucide-react';

interface GeminiWeatherConsoleProps {
  weatherTwin: WeatherTwinWorldState;
  onHypothesisApplied?: (prompt: string) => void;
}

export const GeminiWeatherConsole: React.FC<GeminiWeatherConsoleProps> = ({ weatherTwin, onHypothesisApplied }) => {
  const [activeSubTab, setActiveSubTab] = useState<'explanation' | 'comparison' | 'hypothesis'>('explanation');
  const [hypothesisPrompt, setHypothesisPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const handleRunAnalysis = async (customHypothesis?: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/gemini/weather-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          weatherState: weatherTwin,
          mode: activeSubTab,
          userHypothesis: customHypothesis || hypothesisPrompt
        })
      });

      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
        if (customHypothesis && onHypothesisApplied) {
          onHypothesisApplied(customHypothesis);
        }
      }
    } catch (err) {
      console.error('Weather analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const presetHypotheses = [
    'What if Gulf Sea Surface Temperatures increase by +1.5°C?',
    'What if upper-level vertical wind shear surges to 35 knots?',
    'What if an eyewall replacement cycle commences in 6 hours?',
    'What if a high-pressure ridge blocks north-eastward movement?'
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
      {/* Console Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-xl">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              Gemini AI Weather Intelligence Engine
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-purple-300">
                gemini-3.6-flash
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Explanation, Multi-Feed Model Comparison & Interactive What-If Hypothesis Testing
            </p>
          </div>
        </div>

        <button
          onClick={() => handleRunAnalysis()}
          disabled={loading}
          className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs flex items-center gap-2 transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Run Full Synthesis
        </button>
      </div>

      {/* Sub Tab Switcher */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-medium">
        <button
          onClick={() => setActiveSubTab('explanation')}
          className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
            activeSubTab === 'explanation'
              ? 'bg-purple-600 text-white font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950'
          }`}
        >
          <Brain className="w-4 h-4" /> Meteorological Explanation
        </button>

        <button
          onClick={() => setActiveSubTab('comparison')}
          className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
            activeSubTab === 'comparison'
              ? 'bg-purple-600 text-white font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950'
          }`}
        >
          <Layers className="w-4 h-4 text-cyan-300" /> Multi-Feed Comparison
        </button>

        <button
          onClick={() => setActiveSubTab('hypothesis')}
          className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
            activeSubTab === 'hypothesis'
              ? 'bg-purple-600 text-white font-semibold'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950'
          }`}
        >
          <Sparkles className="w-4 h-4 text-amber-300" /> Hypothesis Generator
        </button>
      </div>

      {/* Content Area Based On Selected SubTab */}
      {activeSubTab === 'explanation' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
          <span className="text-xs font-bold text-purple-300 uppercase tracking-wider block flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" /> Executive Meteorological Synthesis
          </span>
          <p className="text-xs text-slate-200 leading-relaxed font-sans">
            {analysisResult?.explanation ||
              `Major Hurricane Milton (${weatherTwin.activeStorm.centralPressureMb} mb, ${weatherTwin.activeStorm.maxWindKts} kts) continues rapid eastward translation across the central Gulf of Mexico. Thermodynamic enthalpy extraction over high Sea Surface Temperatures (30.1°C) sustains a tight inner core convective structure with minimal vertical shear disruption (8 kts). Synoptic trough interaction is inducing north-eastward acceleration toward the Tampa Bay landfall corridor.`}
          </p>
        </div>
      )}

      {activeSubTab === 'comparison' && (
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
          <span className="text-xs font-bold text-cyan-300 uppercase tracking-wider block flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-cyan-400" /> Multi-Feed Guidance Comparison
          </span>
          <p className="text-xs text-slate-200 leading-relaxed font-sans">
            {analysisResult?.comparison ||
              `NHC Official Advisory predicts Category 4 landfall near Tampa Bay with 125 kt max winds. HRM Substrate Physics Twin aligns closely at 128 kts due to low environmental shear and strong baroclinic energy coupling. GFS guidance serves as a low-end outlier (115 kts) due to higher shear entrainment, while ECMWF maintains Category 4 intensity (132 kts). NWS local alerts reflect peak surge heights of 10 to 15 feet.`}
          </p>
        </div>
      )}

      {activeSubTab === 'hypothesis' && (
        <div className="space-y-4">
          <div className="space-y-2">
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wider block">
              Preset "What-If" Sensitivity Scenarios
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {presetHypotheses.map((ph, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setHypothesisPrompt(ph);
                    handleRunAnalysis(ph);
                  }}
                  className="p-2.5 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-left text-xs text-slate-300 hover:text-white transition-all flex items-center justify-between gap-2"
                >
                  <span className="line-clamp-2">{ph}</span>
                  <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs text-slate-400 font-medium">Or type a custom environmental perturbation:</span>
            <div className="flex gap-2">
              <input
                type="text"
                value={hypothesisPrompt}
                onChange={(e) => setHypothesisPrompt(e.target.value)}
                placeholder="e.g. What if a dry air mass entrains into the western quadrant?"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 font-mono"
              />
              <button
                onClick={() => handleRunAnalysis()}
                disabled={loading || !hypothesisPrompt.trim()}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs flex items-center gap-2 transition-all disabled:opacity-50 shrink-0"
              >
                <Send className="w-3.5 h-3.5" /> Test
              </button>
            </div>
          </div>

          {analysisResult?.hypothesisAnalysis && (
            <div className="bg-slate-950 p-4 rounded-xl border border-amber-900/50 space-y-2 mt-3">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-400" /> Sensitivity Simulation Analysis Output
              </span>
              <p className="text-xs text-slate-200 leading-relaxed font-sans">
                {analysisResult.hypothesisAnalysis}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
