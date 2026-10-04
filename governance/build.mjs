import {stripTypeScriptTypes} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=dirname(fileURLToPath(import.meta.url));
for(const file of ['state','mechanisms','arbitrator','memory','reputation','routing','safety','consequence','transport','health','retrieval','benchmarks']){
 let s=readFileSync(resolve(root,'../vendor/weather-oracle/src/engine',file+'.ts'),'utf8');
 s=s.replace(/import\s*\{[\s\S]*?\}\s*from\s*'([^']+)';/g,(all,path)=>{
  if(path.includes('/types/')||path==='./llmMechanisms'||(file==='state'&&['./aiEcosystem','./weatherState'].includes(path))||path==='./mechanisms')return '';
  return all.replace(path,path+'.js');
 });
 if(file==='state'){
  s=s.replace('createInitialAIEcosystemState(0)','undefined').replace('weatherTwin: createInitialWeatherTwinState(),','').replace('timestamp: Date.now(),','timestamp: 1700000000000,');
  s=s.replace('Forecast Hurricane Track, Intensity & Mitigate Surge Hazards','Govern connected domains within their operating constraints');
  s=s.replace('return Object.freeze(JSON.parse(JSON.stringify(state)));',`const copy=JSON.parse(JSON.stringify(state));\n  const deepFreeze=(o:any):any=>{if(o && typeof o==='object'){Object.values(o).forEach(deepFreeze);Object.freeze(o);}return o;};\n  return deepFreeze(copy);`);
 }
 if(file==='mechanisms')s=s.replace(/^\s*new (LLMAReasoningMechanism|LLMBCritiqueMechanism|ToolsActionMechanism)\(\),?$/gm,'').replaceAll('Date.now()','state.metadata.timestamp');
 if(file==='memory'){
  s=s.replace('Math.floor(Math.random() * 1000)','Object.keys(memory.nodes).length');
  s=s.replace('const toRemove = sorted.find', 'const toRemove = sorted.find');
  s=s.replace('if (nodeCount > memory.capacity) {','while (Object.keys(memory.nodes).length > memory.capacity) {').replace('const toRemove = sorted.find(n => n.type !== \'procedural\');',"const toRemove = sorted.find(n => n.type !== 'procedural') || sorted[0];");
 }
 if(file==='transport'){
  s=s.replace('for (const nodeId in previousState.field.values)', 'for (const nodeId in nextStateDraft.field.values)').replace('const val = previousState.field.values[nodeId];','const val = nextStateDraft.field.values[nodeId];');
  s=s.replaceAll('Date.now()',"nextStateDraft.metadata.timestamp + Object.keys(nextStateDraft.topology.edges).length");
 }
 if(file==='arbitrator'){
  s=s.replace('  }\n): CommitResult {','  },\n  deferCredit = false\n): CommitResult {');
  s=s.replace('if (reputationManager) {\n    const acceptedIds','if (reputationManager && !deferCredit) {\n    const acceptedIds');
 }
 if(file==='routing')s=s.replace("if (mech.id.startsWith('mech_llm_')", "if (mech.id.startsWith('domain_') || mech.id.startsWith('mech_llm_')");
 const src=resolve(root,'src/core',file+'.ts');writeFileSync(src,s);
 writeFileSync(resolve(root,'dist/core',file+'.js'),stripTypeScriptTypes(s));
}
