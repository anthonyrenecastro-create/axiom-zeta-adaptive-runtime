import math
import time
import unittest
from unittest.mock import patch
from az_runtime.devices import Capabilities,Command,SimulatedDevice,DeviceRegistry
from az_runtime.safety import SafetyEnvelope
from az_runtime.stability import StabilityMonitor
from az_runtime.supervisor import PID,AdaptiveField
from az_runtime.runtime import Runtime
from az_runtime.server import ShadowRegistry
from az_runtime.weather import WeatherOracle

class ControlTests(unittest.TestCase):
    def test_command_expiry_replay_and_limits(self):
        d=SimulatedDevice(Capabilities('server','compute',1200,min_performance=.8))
        self.assertTrue(d.apply(Command('server',.8,0,900,1),0))
        self.assertFalse(d.apply(Command('server',.9,0,900,1),0))
        self.assertFalse(d.apply(Command('server',.7,0,900,2),0))
        self.assertFalse(d.apply(Command('server',.9,0,900,2),900))
        d.tick(1/60,30,900)
        self.assertEqual(d.read().performance,1)

    def test_raw_temperature_and_stale_telemetry_block(self):
        d=SimulatedDevice(Capabilities('hvac','cooling',4000))
        gate=SafetyEnvelope()
        d.telemetry.temperature_c=27
        self.assertFalse(gate.dispatch({'hvac':d},{'hvac':23},0,1)['committed'])
        d.telemetry.temperature_c=24
        self.assertIn('hvac: stale/future telemetry',gate.validate({'hvac':d},{'hvac':23},121))
        d.telemetry.power_w=float('nan')
        self.assertFalse(gate.dispatch({'hvac':d},{'hvac':23},0,2)['committed'])

    def test_site_reserves_full_cooling_authority(self):
        d=SimulatedDevice(Capabilities('hvac','cooling',4000))
        self.assertIn('site power reservation exceeds budget',SafetyEnvelope(3000).validate({'hvac':d},{'hvac':23},0))

    def test_antiwindup_and_no_setpoint_derivative_kick(self):
        p=PID(kp=.3,ki=.1,kd=1)
        for _ in range(100):self.assertEqual(p.compute(40,23,1/60),1)
        self.assertEqual(p.integral,0)
        p.compute(40,25,1/60)
        self.assertEqual(p.derivative,0)
        with self.assertRaises(ValueError):p.compute(24,23,0)

    def test_drift_breaker_latches_and_device_isolation(self):
        m=StabilityMonitor(baseline_windows=2)
        self.assertFalse(m.assess('a',[1]*24)['ready'])
        self.assertTrue(m.assess('a',[1]*24)['ready'])
        for _ in range(3):status=m.assess('a',[10]*24)
        self.assertTrue(status['breaker_open'])
        self.assertTrue(m.assess('a',[1]*24)['breaker_open'])
        self.assertFalse(m.assess('b',[1]*24)['breaker_open'])
        m.reset('a');self.assertFalse(m.assess('a',[1]*24)['ready'])

    def test_seeded_field_and_identity_registry(self):
        a,b=AdaptiveField(),AdaptiveField()
        self.assertEqual(a.update([.001]*3),b.update([.001]*3))
        r=DeviceRegistry();d=SimulatedDevice(Capabilities('a','cooling',4000));r.register(d)
        with self.assertRaises(ValueError):r.register(d)

    def test_shadow_validation(self):
        r=ShadowRegistry();row={'device_id':'plug','timestamp_s':time.time(),'power_w':200,'max_power_w':1000}
        self.assertEqual(r.ingest(row)['mode'],'shadow')
        with self.assertRaises(ValueError):r.ingest(row)
        with self.assertRaises(ValueError):r.ingest({**row,'timestamp_s':time.time()-1000})
        with self.assertRaises(ValueError):r.ingest({**row,'power_w':float('nan')})

    def test_weather_bridge_reuses_domain_functions(self):
        w=WeatherOracle().forecast(12)
        self.assertEqual(w['mode'],'synthetic')
        self.assertIn('thermodynamicMPIKts',w['coupling'])
        self.assertEqual(len(w['points']),8)

class IntegrationTests(unittest.TestCase):
    def test_full_day_comparison_and_constraints(self):
        a,b=Runtime(),Runtime(mode='baseline')
        sa,sb=a.run(),b.run()
        self.assertLess(sa['energy_kwh'],sb['energy_kwh'])
        self.assertEqual(sa['constraint_violations'],0)
        self.assertFalse(sa['deadline_missed'])
        self.assertAlmostEqual(sa['pump_completed_h'],2)
        self.assertEqual(sb['adaptive_steps'],0)
        self.assertGreater(sa['adaptive_steps'],0)
        self.assertTrue(any(e['alternatives'] for e in a.ledger))
        self.assertTrue(all(e['dispatch']['committed'] for e in a.ledger))

    def test_governs_without_weather_and_handles_compute_only(self):
        cfg={'max_site_power_w':2000,'pump_required_h':2,'pump_deadline_h':22,
             'devices':[{'device_id':'server','kind':'compute','max_power_w':1200,'min_performance':.8}]}
        r=Runtime(cfg)
        e=r.step()
        self.assertFalse(r.weather_enabled)
        self.assertEqual(e['forecast_mode'],'synthetic-environment')
        self.assertIsNotNone(e['governance'])
        self.assertEqual(e['governance']['context']['weather_enabled'],False)
        self.assertIsNone(e['temperature_range_c'])
        self.assertEqual(r.summary()['pump_completed_h'],0)

    def test_governor_budget_blocks_optimized_action(self):
        r=Runtime();r.run(28);r.config={**r.config,'governance_budget':0}
        e=r.step()
        self.assertEqual(e['governance']['plans'],{})
        self.assertEqual(e['targets']['hvac'],23)

    def test_fault_reverts_to_conservative_policy(self):
        r=Runtime();r.run(30)
        entry=r.step('drift')
        self.assertFalse(entry['adaptive'])
        self.assertEqual(entry['targets']['hvac'],23)
        self.assertTrue(entry['dispatch']['committed'])

    def test_stale_device_rejects_whole_batch(self):
        r=Runtime();r.run(30)
        r.registry.devices['server'].telemetry.timestamp_s=0
        r.registry.devices['server'].stale=True
        entry=r.step()
        self.assertFalse(entry['dispatch']['committed'])
        self.assertEqual(entry['dispatch']['acknowledgements'],{})

    def test_forecast_failure_uses_local_policy(self):
        r=Runtime()
        with patch.object(r.weather,'forecast',side_effect=TimeoutError):e=r.step()
        self.assertFalse(e['adaptive']);self.assertEqual(e['forecast_mode'],'unavailable')
        self.assertTrue(e['dispatch']['committed'])

if __name__=='__main__':unittest.main()
