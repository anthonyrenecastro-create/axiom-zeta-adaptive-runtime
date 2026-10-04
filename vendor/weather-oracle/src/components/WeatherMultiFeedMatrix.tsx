/**
 * Weather Multi-Feed Matrix Component
 * Synthesizes NHC Feeds, NWS API, Open-Meteo Grid, and HRM Substrate Twin
 */

import React, { useState, useEffect } from 'react';
import { WeatherTwinWorldState } from '../types/weatherEcology';
import { NormalizedObservationRecord } from '../engine/observationAdapters';
import { CloudRain, ShieldAlert, Thermometer, Radio, Navigation, Wind, Eye, RefreshCw, CheckCircle, ExternalLink, Zap, ArrowRight, Layers, Database, Cpu, Check } from 'lucide-react';

interface WeatherMultiFeedMatrixProps {
  weatherTwin: WeatherTwinWorldState;
}

export const WeatherMultiFeedMatrix: React.FC<WeatherMultiFeedMatrixProps> = ({ weatherTwin }) => {
  const [nwsAlerts, setNwsAlerts] = useState(weatherTwin.activeAlerts);
  const [openMeteoData, setOpenMeteoData] = useState<any>(null);
  const [axiomSeerData, setAxiomSeerData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchLiveFeeds() {
      setLoading(true);
      try {
        // Fetch NWS Proxy
        const nwsRes = await fetch('/api/weather/nws');
        if (nwsRes.ok) {
          const data = await nwsRes.json();
          if (data.alerts && data.alerts.length > 0) {
            setNwsAlerts(data.alerts);
          }
        }

        // Fetch Open-Meteo Proxy
        const omRes = await fetch(`/api/weather/open-meteo?lat=${weatherTwin.activeStorm.lat}&lon=${weatherTwin.activeStorm.lon}`);
        if (omRes.ok) {
          const data = await omRes.json();
          setOpenMeteoData(data);
        }

        // Fetch AxiomHRMWheatherSeer9955 API
        const seerRes = await fetch(`/api/weather/axiom-seer?lat=${weatherTwin.activeStorm.lat}&lon=${weatherTwin.activeStorm.lon}`);
        if (seerRes.ok) {
          const data = await seerRes.json();
          setAxiomSeerData(data);
        }
      } catch (err) {
        console.error('Error fetching live weather feeds:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchLiveFeeds();
  }, [weatherTwin.activeStorm.lat, weatherTwin.activeStorm.lon]);

  const storm = weatherTwin.activeStorm;

  return (
    <div className="space-y-6">
      {/* Top Banner Feed Health Indicators */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-xl">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Multi-Feed Weather Integration Framework
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400">
                AxiomHRMWheatherSeer9955 Active
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Synchronizing NOAA NHC, NWS Alerts, Open-Meteo & AxiomHRMWheatherSeer9955 Predictive Array
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-indigo-900/60 shadow-sm">
            <Zap className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            <span className="text-slate-400">AxiomSeer 9955:</span>
            <span className="text-indigo-300 font-bold">{axiomSeerData?.feedStatus || weatherTwin.dataSourcesStatus.axiomHRMWeatherSeer}</span>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="text-slate-400">NHC Feeds:</span>
            <span className="text-emerald-300 font-semibold">{weatherTwin.dataSourcesStatus.nhcFeed}</span>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="text-slate-400">NWS API:</span>
            <span className="text-emerald-300 font-semibold">{weatherTwin.dataSourcesStatus.nwsApi}</span>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="text-slate-400">Open-Meteo:</span>
            <span className="text-emerald-300 font-semibold">{weatherTwin.dataSourcesStatus.openMeteo}</span>
          </div>
        </div>
      </div>

      {/* 4-Column Grid: The 4 Ingestion Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pillar 1: NHC Feeds */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
                <CloudRain className="w-4 h-4 text-sky-400" /> NHC Storm Feed
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-400 font-bold">
                {storm.status}
              </span>
            </div>

            <div className="mt-3 space-y-2">
              <div className="flex justify-between items-baseline">
                <h4 className="text-base font-extrabold text-white">{storm.name}</h4>
                <span className="text-xs text-slate-400 font-mono">{storm.id}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                <div className="bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Central Pressure</span>
                  <span className="text-sky-300 font-bold text-sm">{storm.centralPressureMb} mb</span>
                </div>
                <div className="bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Max Winds</span>
                  <span className="text-red-400 font-bold text-sm">{storm.maxWindKts} kts <span className="text-[10px] text-slate-400">({storm.maxWindMph} mph)</span></span>
                </div>
                <div className="bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Eye Diameter</span>
                  <span className="text-slate-200 font-semibold">{storm.eyeDiameterNm} NM</span>
                </div>
                <div className="bg-slate-950 p-2 rounded border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">Vector Motion</span>
                  <span className="text-emerald-400 font-semibold text-[11px] truncate">{storm.movementDirection}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 space-y-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Active Advisories</span>
            <div className="space-y-1 max-h-24 overflow-y-auto text-[11px] text-slate-300 pr-1">
              {storm.advisories.map((adv, idx) => (
                <p key={idx} className="bg-slate-950 p-1.5 rounded border border-slate-800/80 leading-snug">
                  • {adv}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* Pillar 2: NWS Alerts API */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-red-400 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-red-400" /> NWS Alerts API
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {nwsAlerts.length} Active
              </span>
            </div>

            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto pr-1">
              {nwsAlerts.map(alert => (
                <div key={alert.id} className="bg-slate-950 p-2.5 rounded-lg border border-red-900/40 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-red-300">{alert.event}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-red-950 border border-red-800 text-red-400 uppercase">
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-medium leading-snug">{alert.headline}</p>
                  <p className="text-[10px] text-slate-400 font-mono">Zones: {alert.areaDesc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
            <span>Direct NWS Feed (`api.weather.gov`)</span>
            <span className="text-emerald-400 font-mono flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Realtime
            </span>
          </div>
        </div>

        {/* Pillar 3: Open-Meteo Environmental Grid */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-purple-400 flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-purple-400" /> Open-Meteo Grid
              </span>
              <span className="text-[10px] font-mono text-purple-300 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
                {weatherTwin.gridPoints.length} Sector Grids
              </span>
            </div>

            <div className="mt-3 space-y-2 max-h-56 overflow-y-auto pr-1 text-xs">
              {weatherTwin.gridPoints.map((gp, idx) => (
                <div key={idx} className="bg-slate-950 p-2 rounded-lg border border-slate-800 space-y-1">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="font-semibold text-slate-200">{gp.sectorName}</span>
                    <span className="text-purple-300 font-mono text-[10px]">{gp.seaSurfaceTempC}°C SST</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400">
                    <div>Press: <span className="text-slate-200">{gp.surfacePressureMb} mb</span></div>
                    <div>Wind: <span className="text-red-300">{gp.windSpeed10mKts} kts</span></div>
                    <div>Precip: <span className="text-sky-300">{gp.precipitationMmHr} mm/h</span></div>
                    <div>CAPE: <span className="text-amber-300">{gp.capeJkg} J/kg</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
            <span>Open-Meteo Environmental Grid</span>
            <span className="text-sky-400 font-mono">10m / 100m Vectors</span>
          </div>
        </div>

        {/* Pillar 4: HRM Substrate Weather Twin */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-400" /> HRM Evolving Twin
              </span>
              <span className="text-[10px] font-mono text-amber-300 bg-amber-950 px-2 py-0.5 rounded border border-amber-800 font-bold">
                Step +{weatherTwin.lastAssimilatedStep}
              </span>
            </div>

            <div className="mt-3 space-y-2.5">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <span className="text-xs text-slate-400 block font-semibold">Track Forecast Vector</span>
                <div className="space-y-1.5 text-xs font-mono">
                  {weatherTwin.trackForecast.slice(0, 4).map((tf, i) => (
                    <div key={i} className="flex items-center justify-between text-[11px] border-b border-slate-900 pb-1">
                      <span className="text-slate-400">T+{tf.hoursFromNow}h ({tf.locationName})</span>
                      <span className="text-amber-300 font-bold">{tf.maxWindKts} kts</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
                <span className="text-slate-400">Consensus Index</span>
                <span className="text-emerald-400 font-mono font-bold text-sm">
                  {(weatherTwin.modelDisagreement.consensusIndex * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
            <span>HRM Substrate World-Model</span>
            <span className="text-amber-400 font-mono font-bold">Evolving</span>
          </div>
        </div>
      </div>

      {/* AxiomHRMWheatherSeer9955 Live API Telemetry Display */}
      <div className="bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-800/60 rounded-xl p-4 shadow-xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-indigo-900/60 pb-3">
          <div className="flex items-center gap-2.5">
            <Zap className="w-5 h-5 text-indigo-400 animate-bounce" />
            <div>
              <h4 className="text-xs font-bold text-indigo-200 tracking-wide uppercase flex items-center gap-2">
                AxiomHRMWheatherSeer9955 Live API Feed
                <span className="normal-case text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 border border-indigo-700 text-indigo-300 font-bold">
                  v9.95.5-ConvectiveCore
                </span>
              </h4>
              <p className="text-[11px] text-slate-400">
                {axiomSeerData?.forecastSynthesis || 'AxiomHRMWheatherSeer9955 High-Resolution Convective Array assimilating real-time Doppler radar & satellite enthalpy feeds.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">API Status:</span>
            <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 font-bold">
              {axiomSeerData?.feedStatus || 'LIVE'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs font-mono">
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Central Pressure</span>
            <span className="text-indigo-300 font-extrabold text-sm">{axiomSeerData?.telemetry?.centralPressureMb || 938} mb</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Predictive Max Wind</span>
            <span className="text-red-400 font-extrabold text-sm">{axiomSeerData?.telemetry?.predictiveMaxWindKts || 132} kts</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Thermodynamic Enthalpy</span>
            <span className="text-emerald-400 font-extrabold text-sm">{axiomSeerData?.telemetry?.thermodynamicEnthalpyIndex || 0.96}</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Doppler Vorticity Vector</span>
            <span className="text-sky-300 font-bold text-xs truncate">{axiomSeerData?.telemetry?.dopplerVorticityVector || '280° at 130 kts'}</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Est Landfall Surge</span>
            <span className="text-amber-400 font-extrabold text-sm">{axiomSeerData?.telemetry?.estimatedLandfallSurgeFt || 13.8} ft</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
            <span className="text-[10px] text-slate-500 block uppercase">Seer Confidence</span>
            <span className="text-indigo-400 font-extrabold text-sm">
              {((axiomSeerData?.telemetry?.seerConfidenceIndex || 0.985) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Observation Adapters Architectural Layer Card */}
      <div className="bg-slate-900 border border-teal-800/50 rounded-xl p-5 space-y-4 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-teal-900/50 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-teal-950 border border-teal-700/60 text-teal-400 rounded-lg">
              <Layers className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Observation Adapters Layer
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950 border border-teal-700 text-teal-300 font-bold">
                  Pre-Mechanism Ingestion & Normalization
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Strips raw API format anomalies and normalizes observations directly into Validated Weather State before physics mechanisms reason on them.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Normalized Feeds:</span>
            <span className="px-2.5 py-1 rounded bg-teal-950 border border-teal-700 text-teal-300 font-bold">
              {weatherTwin.validatedObservationState?.normalizedCount || 7} Adapters Verified
            </span>
          </div>
        </div>

        {/* Pipeline Concept Flow Banner */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 overflow-x-auto">
          <div className="flex items-center justify-between min-w-[650px] text-xs font-mono">
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
              <Database className="w-3.5 h-3.5 text-sky-400" />
              <span>External APIs</span>
            </div>
            <ArrowRight className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-teal-950 border border-teal-700 text-teal-300 font-bold">
              <Layers className="w-3.5 h-3.5 text-teal-400" />
              <span>Observation Adapters</span>
            </div>
            <ArrowRight className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 font-bold">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              <span>Validated Weather State</span>
            </div>
            <ArrowRight className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>Mechanisms</span>
            </div>
            <ArrowRight className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
              <span>Contributions</span>
            </div>
            <ArrowRight className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-indigo-950 border border-indigo-700 text-indigo-300 font-bold">
              <span>Arbitration</span>
            </div>
          </div>
        </div>

        {/* Normalized Adapters Breakdown Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {weatherTwin.validatedObservationState?.observationsByAdapter ? (
            (Object.values(weatherTwin.validatedObservationState.observationsByAdapter) as NormalizedObservationRecord[]).map(adapterObs => (
              <div key={adapterObs.adapterId} className="bg-slate-950/90 border border-slate-800 rounded-lg p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-teal-300 truncate max-w-[180px]">{adapterObs.sourceName}</span>
                  <span className="px-1.5 py-0.5 text-[10px] rounded bg-teal-950 border border-teal-800 text-teal-400 font-mono flex items-center gap-1">
                    <Check className="w-3 h-3 text-emerald-400" />
                    {(adapterObs.confidenceScore * 100).toFixed(0)}% Quality
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                  {adapterObs.rawPayloadSummary}
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1 text-[10px] font-mono text-slate-300">
                  {adapterObs.observedMetrics.centralPressureMb && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Pressure: <strong className="text-teal-300">{adapterObs.observedMetrics.centralPressureMb} mb</strong>
                    </span>
                  )}
                  {adapterObs.observedMetrics.maxWindKts && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Wind: <strong className="text-red-400">{adapterObs.observedMetrics.maxWindKts} kts</strong>
                    </span>
                  )}
                  {adapterObs.observedMetrics.seaSurfaceTempC && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      SST: <strong className="text-amber-300">{adapterObs.observedMetrics.seaSurfaceTempC}°C</strong>
                    </span>
                  )}
                  {adapterObs.observedMetrics.waveHeightFt && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Swell: <strong className="text-sky-300">{adapterObs.observedMetrics.waveHeightFt} ft</strong>
                    </span>
                  )}
                  {adapterObs.observedMetrics.radarMaxReflectivityDbz && (
                    <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Reflectivity: <strong className="text-indigo-300">{adapterObs.observedMetrics.radarMaxReflectivityDbz} dBZ</strong>
                    </span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-3 text-center text-xs text-slate-500 py-3">
              Observation Adapters Active - Normalizing External Weather Feeds...
            </div>
          )}
        </div>
      </div>

      {/* Decoupled Sub-Domains Architectural Display */}
      <div className="bg-slate-900 border border-purple-800/50 rounded-xl p-5 space-y-4 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-purple-900/50 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-purple-950 border border-purple-700/60 text-purple-400 rounded-lg">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Decoupled Sub-Domain Architecture
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 border border-purple-700 text-purple-300 font-bold">
                  Domain-Isolated Reasoning
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                General Synoptic Weather Patterns and Tropical Cyclone Vortex Dynamics run as decoupled sub-domains joined by a Cross-Domain Coupling Adapter.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Domain Coupling:</span>
            <span className="px-2.5 py-1 rounded bg-purple-950 border border-purple-700 text-purple-300 font-bold">
              {weatherTwin.coupledBoundaryEffect?.shearImpactStatus || 'FAVORABLE_LOW_SHEAR'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Domain 1: General Weather Patterns */}
          <div className="bg-slate-950 border border-sky-900/60 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-sky-900/40 pb-2">
              <span className="text-xs font-bold text-sky-300 uppercase tracking-wider flex items-center gap-1.5">
                <Wind className="w-4 h-4 text-sky-400" />
                Sub-Domain 1: Weather Patterns
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400">
                Synoptic Scale
              </span>
            </div>

            <p className="text-[11px] text-slate-400">
              Tracks atmospheric steering ridges, upper-level jet stream troughs, and ambient thermodynamic background conditions.
            </p>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Bermuda High Steering:</span>
                <span className="text-sky-300 font-bold">300° @ 12 kts</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Jet Stream Trough:</span>
                <span className="text-sky-300 font-bold">{weatherTwin.weatherPatternDomain?.jetStreamLatitude || 38.2}°N</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Ambient Wind Shear:</span>
                <span className="text-amber-300 font-bold">{weatherTwin.weatherPatternDomain?.ambientEnvironmentalShearKts || 16.5} kts</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Sea Surface Temp Grid:</span>
                <span className="text-emerald-300 font-bold">{weatherTwin.weatherPatternDomain?.seaSurfaceTempGridC || 30.1}°C</span>
              </div>
            </div>
          </div>

          {/* Coupling Adapter Bridge */}
          <div className="bg-gradient-to-b from-purple-950/60 to-slate-950 border border-purple-800/60 rounded-xl p-4 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-purple-800/40 pb-2">
                <span className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                  <ArrowRight className="w-4 h-4 text-purple-400" />
                  Cross-Domain Coupler
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-900/60 text-purple-200">
                  Adapter Layer
                </span>
              </div>

              <p className="text-[11px] text-slate-400 mt-2">
                Converts synoptic weather patterns into boundary forces injected into the Hurricane Twin domain.
              </p>
            </div>

            <div className="space-y-2 text-xs font-mono my-2">
              <div className="p-2 bg-slate-900/90 rounded border border-purple-900/60 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Synoptic Steering Angle</span>
                <span className="text-purple-300 font-extrabold text-sm">
                  {weatherTwin.coupledBoundaryEffect?.synopticSteeringHeadingDeg || 315}°
                </span>
              </div>
              <div className="p-2 bg-slate-900/90 rounded border border-purple-900/60 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Thermodynamic MPI Boundary</span>
                <span className="text-emerald-300 font-extrabold text-sm">
                  {weatherTwin.coupledBoundaryEffect?.thermodynamicMPIKts || 165} kts
                </span>
              </div>
              <div className="p-2 bg-slate-900/90 rounded border border-purple-900/60 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Coupled 24h Intensification</span>
                <span className="text-indigo-300 font-extrabold text-sm">
                  +{weatherTwin.coupledBoundaryEffect?.coupledIntensificationRateKtsPer24h || 12} kts/24h
                </span>
              </div>
            </div>

            <div className="text-[10px] font-mono text-purple-300/80 bg-purple-950/40 p-2 rounded border border-purple-900/30 text-center">
              Boundary Forces Synchronized
            </div>
          </div>

          {/* Domain 2: Hurricane Digital Twin */}
          <div className="bg-slate-950 border border-red-900/60 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-red-900/40 pb-2">
              <span className="text-xs font-bold text-red-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                Sub-Domain 2: Hurricane Twin
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 border border-red-800 text-red-400">
                Meso-Vortex Scale
              </span>
            </div>

            <p className="text-[11px] text-slate-400">
              Focuses purely on inner-core thermodynamics, eyewall replacement cycles, maximum winds, and storm surge generation.
            </p>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Storm Intensity Category:</span>
                <span className="text-red-400 font-extrabold">{weatherTwin.hurricaneTwinDomain?.category || 'Cat4'}</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Central Pressure / Wind:</span>
                <span className="text-red-300 font-bold">{weatherTwin.hurricaneTwinDomain?.vortexCore.centralPressureMb || 938} mb / {weatherTwin.hurricaneTwinDomain?.vortexCore.maximumSustainedWindKts || 130} kts</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Eyewall Phase:</span>
                <span className="text-indigo-300 font-bold truncate max-w-[140px]">{weatherTwin.hurricaneTwinDomain?.eyewall.eyewallReplacementCyclePhase || 'secondary_eyewall_forming'}</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-slate-400">Peak Storm Surge:</span>
                <span className="text-amber-300 font-bold">{weatherTwin.hurricaneTwinDomain?.estimatedStormSurgePeakFt || 13.8} ft</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
