"""Optional context providers, separate from the domain-neutral governor."""
import math
class EnvironmentContext:
    def forecast(self,hour,horizon=8):
        return {'mode':'synthetic-environment','confidence':.65,'weather_enabled':False,
                'points':[{'hour':hour+(i+1)*.25,
                           'ambient_c':30+5*math.sin(2*math.pi*(hour+(i+1)*.25-8)/24),
                           'uncertainty_c':.6+.15*i,
                           'price_per_kwh':.32 if 15<=(hour+(i+1)*.25)%24<19 else .12}
                          for i in range(horizon)]}
