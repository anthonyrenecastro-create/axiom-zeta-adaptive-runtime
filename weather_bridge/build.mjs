import { stripTypeScriptTypes } from 'node:module';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));
for (const file of ['weatherPatterns/mechanisms','hurricaneTwin/mechanisms','domainCoupler']) {
 let source=readFileSync(resolve(here,'../vendor/weather-oracle/src/domains',file+'.ts'),'utf8');
 source=source.replace(/^import \{ (WeatherPatternState, SynopticFeature|HurricaneTwinState|WeatherPatternState) \} from .*;$/gm,'');
 source=source.replace(/from '(\.\/[^']+)'/g,"from '$1.js'");
 const target=resolve(here,'dist',file+'.js');mkdirSync(dirname(target),{recursive:true});
 writeFileSync(target,stripTypeScriptTypes(source));
}
