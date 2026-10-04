/**
 * HRM Ecology: Weather Patterns & Hurricane Twin Framework
 * Main Application Workbench
 */

import React, { useState, useEffect, useMemo } from 'react';
import { HRMEcologyRuntime } from './engine/runtime';
import { TopologyCanvas } from './components/TopologyCanvas';
import { CommitInspector } from './components/CommitInspector';
import { LedgerView } from './components/LedgerView';
import { ReplayControls } from './components/ReplayControls';
import { ResourceMonitor } from './components/ResourceMonitor';
import { PerturbationPanel } from './components/PerturbationPanel';
import { PythonCodeExporter } from './components/PythonCodeExporter';
import { SubstrateHealthAndReputation } from './components/SubstrateHealthAndReputation';
import { CognitiveMemoryConsole } from './components/CognitiveMemoryConsole';
import { WeatherMultiFeedMatrix } from './components/WeatherMultiFeedMatrix';
import { WeatherMechanismConsole } from './components/WeatherMechanismConsole';
import { WeatherConsequenceView } from './components/WeatherConsequenceView';
import { GeminiWeatherConsole } from './components/GeminiWeatherConsole';
import { SimulationScenario } from './engine/environment';
import { createInitialWeatherTwinState } from './engine/weatherState';
import {
  CloudRain,
  Activity,
  FileText,
  Terminal,
  ShieldAlert,
  Zap,
  Sparkles,
  Layers,
  Brain,
  Award,
  Database,
  Radio,
  Scale,
  Compass,
  AlertTriangle
} from 'lucide-react';

export default function App() {
  const [seed, setSeed] = useState(42);
  const scenario: SimulationScenario = 'ai_ecosystem';

  // Initialize HRM Engine Runtime Singleton
  const runtime = useMemo(() => new HRMEcologyRuntime(seed, 12, 'ai_ecosystem'), [seed]);

  const [worldState, setWorldState] = useState(runtime.getState());
  const [history, setHistory] = useState(runtime.getHistory());
  const [ledger, setLedger] = useState(runtime.getLedger());
  const [isRunning, setIsRunning] = useState(runtime.getIsRunning());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'gemini' | 'feeds' | 'canvas' | 'mechanisms' | 'consequences' | 'health' | 'memory' | 'python'>('gemini');
  const [selectedStepForLedger, setSelectedStepForLedger] = useState(0);

  useEffect(() => {
    const unsubscribe = runtime.subscribe(() => {
      const state = runtime.getState();
      setWorldState(state);
      setHistory([...runtime.getHistory()]);
      setLedger([...runtime.getLedger()]);
      setIsRunning(runtime.getIsRunning());
      setSelectedStepForLedger(state.metadata.step);
    });
    return () => unsubscribe();
  }, [runtime]);

  const currentStep = worldState.metadata.step;
  const maxStep = history.length - 1;

  const currentLedgerEntry = useMemo(() => {
    return ledger.find(e => e.step === currentStep) || (ledger.length > 0 ? ledger[ledger.length - 1] : null);
  }, [ledger, currentStep]);

  const weatherTwin = worldState.weatherTwin || createInitialWeatherTwinState();

  const handlePlayPause = () => {
    if (isRunning) {
      runtime.stop();
    } else {
      runtime.start(750);
    }
  };

  const handleStepForward = () => {
    runtime.step();
  };

  const handleStepBackward = () => {
    if (currentStep > 0) {
      runtime.replayToStep(currentStep - 1);
    }
  };

  const handleSeek = (step: number) => {
    runtime.replayToStep(step);
  };

  const handleReset = (newSeed = 42) => {
    setSeed(newSeed);
    runtime.reset(newSeed, 12, 'ai_ecosystem');
    setSelectedNodeId(null);
  };

  const handleSplitNodeRequest = (nodeId: string) => {
    runtime.injectSplitNode(nodeId);
  };

  const handleHypothesisApplied = (prompt: string) => {
    runtime.processUserPrompt(prompt);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased flex flex-col">
      {/* Navbar Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sky-500/20 border border-sky-500/40 rounded-xl text-sky-400">
            <CloudRain className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              HRM Weather Patterns & Hurricane Twin
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400 font-semibold">
                Weather Ecosystem
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Multi-Feed Weather Intelligence Substrate (NHC Feeds • NWS API • Open-Meteo • HRM Ecology • Gemini)
            </p>
          </div>
        </div>

        {/* Active Storm Quick Summary Badge */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse"></span>
            <span className="text-slate-400 font-semibold">{weatherTwin.activeStorm.name}:</span>
            <span className="text-red-400 font-bold">{weatherTwin.activeStorm.status}</span>
            <span className="text-slate-500">({weatherTwin.activeStorm.centralPressureMb} mb, {weatherTwin.activeStorm.maxWindKts} kts)</span>
          </div>

          <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="text-slate-500">Step:</span>
            <span className="text-emerald-400 font-bold">{currentStep}</span>
          </div>
        </div>
      </header>

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-5">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2 text-xs font-medium">
          <button
            onClick={() => setActiveTab('gemini')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'gemini'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Brain className="w-4 h-4 text-purple-300" /> Gemini Weather AI
          </button>

          <button
            onClick={() => setActiveTab('feeds')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'feeds'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Radio className="w-4 h-4 text-sky-300" /> Multi-Feed Matrix
          </button>

          <button
            onClick={() => setActiveTab('canvas')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'canvas'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Activity className="w-4 h-4 text-cyan-300" /> Hurricane Twin Canvas
          </button>

          <button
            onClick={() => setActiveTab('mechanisms')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'mechanisms'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Scale className="w-4 h-4 text-amber-300" /> Mechanism Forecasts & Disagreement
          </button>

          <button
            onClick={() => setActiveTab('consequences')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'consequences'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-red-400" /> Consequence & Impact Ledger
          </button>

          <button
            onClick={() => setActiveTab('health')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'health'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Award className="w-4 h-4 text-emerald-400" /> Substrate Health
          </button>

          <button
            onClick={() => setActiveTab('memory')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'memory'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Database className="w-4 h-4 text-purple-400" /> Cognitive Memory
          </button>

          <button
            onClick={() => setActiveTab('python')}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'python'
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Terminal className="w-4 h-4" /> Python Source Code
          </button>
        </div>

        {/* Tab 1: Gemini Weather AI */}
        {activeTab === 'gemini' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />

            <GeminiWeatherConsole
              weatherTwin={weatherTwin}
              onHypothesisApplied={handleHypothesisApplied}
            />

            <WeatherMultiFeedMatrix weatherTwin={weatherTwin} />
          </div>
        )}

        {/* Tab 2: Multi-Feed Matrix */}
        {activeTab === 'feeds' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />
            <WeatherMultiFeedMatrix weatherTwin={weatherTwin} />
          </div>
        )}

        {/* Tab 3: Hurricane Twin Substrate Canvas */}
        {activeTab === 'canvas' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />

            <TopologyCanvas
              state={worldState}
              environment={runtime.getEnvironment()}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
              onSplitNodeRequest={handleSplitNodeRequest}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ResourceMonitor state={worldState} />
              <PerturbationPanel runtime={runtime} />
            </div>
          </div>
        )}

        {/* Tab 4: Mechanism Forecasts & Model Disagreement */}
        {activeTab === 'mechanisms' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />
            <WeatherMechanismConsole weatherTwin={weatherTwin} />
          </div>
        )}

        {/* Tab 5: Consequence Analysis & Impact Ledger */}
        {activeTab === 'consequences' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />
            <WeatherConsequenceView
              weatherTwin={weatherTwin}
              ledger={ledger}
              currentStep={currentStep}
            />
          </div>
        )}

        {/* Tab 6: Substrate Health */}
        {activeTab === 'health' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />
            <SubstrateHealthAndReputation
              runtime={runtime}
              state={worldState}
            />
          </div>
        )}

        {/* Tab 7: Cognitive Memory */}
        {activeTab === 'memory' && (
          <div className="space-y-4">
            <ReplayControls
              currentStep={currentStep}
              maxStep={maxStep}
              isRunning={isRunning}
              stateHash={worldState.metadata.stateHash}
              seed={seed}
              scenario={scenario}
              onPlayPause={handlePlayPause}
              onStepForward={handleStepForward}
              onStepBackward={handleStepBackward}
              onSeek={handleSeek}
              onReset={handleReset}
            />
            <CognitiveMemoryConsole state={worldState} />
          </div>
        )}

        {/* Tab 8: Python Code Exporter */}
        {activeTab === 'python' && (
          <div className="space-y-4">
            <PythonCodeExporter />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/50 py-4 text-center text-xs text-slate-500">
        HRM Weather Patterns • Evolving Hurricane Twin Substrate • NHC, NWS API, Open-Meteo & Gemini Integration
      </footer>
    </div>
  );
}
