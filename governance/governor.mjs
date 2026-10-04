/** Domain-neutral governance using the oracle's actual cognitive substrate modules. */
import {createHash} from 'node:crypto';
import {createInitialWorldState,freezeState} from './dist/core/state.js';
import {getDefaultMechanisms} from './dist/core/mechanisms.js';
import {commitNextState} from './dist/core/arbitrator.js';
import {ReputationManager} from './dist/core/reputation.js';
import {DynamicCognitiveRouter} from './dist/core/routing.js';
import {CognitiveMemoryEngine} from './dist/core/memory.js';
import {evaluateConsequences} from './dist/core/consequence.js';
import {computeRuntimeHealth} from './dist/core/health.js';
import {retrieveContextForLLM} from './dist/core/retrieval.js';
import {ScientificValidationTracker} from './dist/core/benchmarks.js';

const clone=x=>JSON.parse(JSON.stringify(x));
const bounded=x=>Math.max(0,Math.min(1,x));
const validId=x=>typeof x==='string'&&/^[A-Za-z][A-Za-z0-9_.-]{0,63}$/.test(x)&&!['constructor','prototype','__proto__'].includes(x);
const hash=s=>createHash('sha256').update(JSON.stringify({...s,metadata:{...s.metadata,stateHash:undefined}})).digest('hex');
function check(request){
 if(!request||!Array.isArray(request.domains)||!request.domains.length||request.domains.length>16)throw Error('domains must contain 1..16 modeled domains');
 if(request.allow_actions!==undefined&&typeof request.allow_actions!=='boolean')throw Error('allow_actions must be boolean');
 const seen=new Set();const nodes=new Set();let nodeCount=0;
 for(const d of request.domains){
  if(!validId(d.id)||seen.has(d.id))throw Error('invalid/duplicate domain id');seen.add(d.id);
  if(!d.observations||!d.bounds||!d.objectives||!Array.isArray(d.candidates)||d.candidates.length>64)throw Error('domain needs observations, bounds, objectives and up to 64 candidates');
  for(const [key,val] of Object.entries(d.observations)){
   if(!validId(key)||!Number.isFinite(val)||val<0||val>1)throw Error('observations must be named normalized finite scalars');if(nodes.has(`${d.id}.${key}`))throw Error('ambiguous domain node identity');nodes.add(`${d.id}.${key}`);nodeCount++;
  }
  if(!Object.keys(d.observations).length||Object.keys(d.bounds).length>100||Object.keys(d.objectives).length>12)throw Error('invalid domain width');
  for(const [key,b] of Object.entries(d.bounds))if(!validId(key)||!Number.isFinite(b.min)||!Number.isFinite(b.max)||b.min>b.max)throw Error('invalid actuator bounds');
  for(const [key,w] of Object.entries(d.objectives))if(!validId(key)||!Number.isFinite(w)||w<0)throw Error('invalid objective weight');
  if(!Object.values(d.objectives).some(w=>w>0))throw Error('domain needs a positive objective weight');
  const candidateIds=new Set();
  for(const c of d.candidates){
   if(candidateIds.has(c.id))throw Error('duplicate candidate id');candidateIds.add(c.id);
   if(!validId(c.id)||typeof c.feasible!=='boolean'||!c.targets||!c.metrics)throw Error('invalid candidate');
   for(const [key,value] of Object.entries(c.predicted_observations||{}))if(!Object.hasOwn(d.observations,key)||!Number.isFinite(value)||value<0||value>1)throw Error('invalid predicted observation');
   for(const key of Object.keys(d.objectives))if(!Number.isFinite(c.metrics[key])||c.metrics[key]<0)throw Error('invalid predicted metric');
   if(Object.keys(c.targets).length!==Object.keys(d.bounds).length)throw Error('incomplete action');
   for(const [key,b] of Object.entries(d.bounds))if(!Number.isFinite(c.targets[key])||c.targets[key]<b.min||c.targets[key]>b.max)throw Error('action outside declared bounds');
  }
 }
 if(nodeCount>100)throw Error('governance node limit reached');
 if(request.budget!==undefined&&(!Number.isFinite(request.budget)||request.budget<0||request.budget>1024))throw Error('invalid compute budget');
}

class DomainObjectiveMechanism{
 constructor(domain,objective){this.domain=domain;this.objective=objective;this.id=`domain_${domain.id}_${objective}`;this.name=`${domain.id}: ${objective}`;}
 propose(snapshot){
  const d=snapshot.domains[this.domain.id];
  const eligible=d.candidates.filter(c=>c.feasible);
  const ranked=eligible.toSorted((a,b)=>a.metrics[this.objective]-b.metrics[this.objective]);
  const prediction=ranked[0]?.predicted_observations||{};
  const predictedFieldValues=Object.fromEntries(Object.entries(prediction).filter(([k,v])=>Number.isFinite(v)&&v>=0&&v<=1).map(([k,v])=>[`${d.id}.${k}`,v]));
  return {mechanismId:this.id,mechanismName:this.name,confidence:0.9/(1+2*(d.experience?.prediction_error_ema||0)),activationStrength:0.95,
   estimatedCost:2,uncertainty:bounded(0.1+(d.experience?.prediction_error_ema||0)),rationale:`Evaluate ${eligible.length} feasible ${d.id} alternatives for ${this.objective}; no direct actuator authority`,
   fieldDeltas:{},predictedFieldValues,diagnostics:{domain:d.id,objective:this.objective,
    weight:d.objectives[this.objective],preferredCandidate:ranked[0]?.id,
    candidateCosts:Object.fromEntries(eligible.map(c=>[c.id,c.metrics[this.objective]]))}};
 }
}

export class WorldGovernor{
 constructor(session){
  this.state=session?.state||null;this.pending=session?.pending||null;
  this.reputation=new ReputationManager();if(session?.reputations)this.reputation.reputations=clone(session.reputations);
  this.router=new DynamicCognitiveRouter();this.memory=new CognitiveMemoryEngine();this.tracker=new ScientificValidationTracker();
 }
 export(){return clone({state:this.state,pending:this.pending,reputations:this.reputation.getAllReputations()});}
 plan(request){
  check(request);if(this.pending)throw Error('report the previous observed outcome before planning again');
  const domains=Object.fromEntries(request.domains.map(d=>[d.id,clone(d)]));
  const observed=Object.fromEntries(request.domains.flatMap(d=>Object.entries(d.observations).map(([k,v])=>[`${d.id}.${k}`,v])));
  if(!this.state){
   this.state=createInitialWorldState(42,Object.keys(observed).length,false);
   this.state.topology={nodes:{},edges:{},adjacency:{}};
   this.state.field={values:{},gradients:{},densities:{},velocities:{}};
   this.state.stress.nodeStress={};this.state.uncertainty.nodeUncertainties={};
   this.state.registeredNodeIds=Object.keys(observed).sort();
   this.state.memory.nodes={};this.state.memory.workingMemory.activeObservations=[];
   let i=0,previous=null;
   for(const [id,value] of Object.entries(observed)){
    this.state.topology.nodes[id]={id,position:{x:100+i*80,y:100},regionId:id.split('.')[0],manifoldId:'manifold_primary'};
    this.state.topology.adjacency[id]=[];this.state.field.values[id]=value;
    this.state.field.gradients[id]={x:0,y:0};this.state.field.densities[id]=1;this.state.field.velocities[id]={x:0,y:0};
    this.state.stress.nodeStress[id]=0;this.state.uncertainty.nodeUncertainties[id]=.1;
    if(previous){const eid=`edge_${i}`;this.state.topology.edges[eid]={id:eid,source:previous,target:id,weight:.8,conductance:.7,active:true};this.state.topology.adjacency[id].push(previous);this.state.topology.adjacency[previous].push(id);}
    previous=id;i++;
   }
   this.state.cognition.attentionFocusNodeId=Object.keys(observed)[0];
   this.state.guidance.attractorNodes=Object.keys(observed).slice(0,3);
   this.state.hierarchy.manifolds.manifold_root.nodeIds=Object.keys(observed);
   this.state.hierarchy.manifolds.manifold_primary.nodeIds=Object.keys(observed);
   this.state.hierarchy.manifolds.manifold_secondary.nodeIds=[];
  }
  const priorHash=this.state.metadata.stateHash||hash(this.state);
  const frame=clone(this.state);
  if(JSON.stringify(Object.keys(observed).sort())!==JSON.stringify(frame.registeredNodeIds))throw Error('domain topology changed; start a new governor session');
  // Domain registration/retirement must be explicit rather than mutating topology mid-session.
  for(const key of Object.keys(observed))if(!frame.topology.nodes[key])throw Error('domain topology changed; start a new governor session');
  frame.domains=domains;
  for(const d of Object.values(domains))d.experience=clone(frame.domainExperience?.[d.id]||{});
  frame.context=clone(request.context||{});
  frame.guidance.activeGoal=request.goal||'Optimize connected domains under hard constraints';
  frame.goals.primaryGoal=frame.guidance.activeGoal;
  frame.resources.totalComputeBudget=request.budget??256;frame.resources.usedComputeEnergy=0;
  frame.resources.structuralEventBudget=2;
  for(const key of Object.keys(frame.topology.nodes))frame.stress.nodeStress[key]=bounded(request.stress?.[key]??0.05);
  frame.stress.globalStress=Object.values(frame.stress.nodeStress).reduce((a,b)=>a+b,0)/Object.keys(frame.topology.nodes).length;
  frame.stress.safeModeActive=frame.stress.globalStress>.85;
  frame.metadata.stateHash=hash(frame);
  const snapshot=freezeState(frame);
  const observation={step:snapshot.metadata.step,sensedNodes:Object.fromEntries(Object.entries(observed).map(([k,value])=>[k,{value,noise:.05}])),sensorLoss:false};
  const domainMechanisms=request.domains.flatMap(d=>Object.entries(d.objectives).filter(([,w])=>w>0).map(([key])=>new DomainObjectiveMechanism(d,key)));
  const all=[...domainMechanisms,...getDefaultMechanisms()];
  const routed=this.router.selectActiveMechanisms(snapshot,all,this.reputation,observation);
  const proposals=[];const budgetRejected=[];let used=0;
  for(const mech of routed){const c=mech.propose(snapshot,observation);if(used+c.estimatedCost>snapshot.resources.totalComputeBudget){budgetRejected.push(mech.id);continue;}used+=c.estimatedCost;proposals.push(c);}
  const veto=request.allow_actions===false?domainMechanisms.map(m=>m.id):[];
  const critique={overallConsistencyScore:1,hallucinationRisk:0,vetoedMechanisms:veto,safetyWarnings:request.allow_actions===false?['Actions disabled by supervisory policy']:[]};
  const result=commitNextState(snapshot,proposals,this.reputation,critique,true);
  result.ledgerEntry.previousStateHash=priorHash;
  result.ledgerEntry.observationFrameHash=snapshot.metadata.stateHash;
  const accepted=new Map(result.ledgerEntry.acceptedContributions.map(c=>[c.mechanismId,c]));
  const plans={};
  if(result.ledgerEntry.accepted&&!result.nextState.stress.safeModeActive){
   for(const d of request.domains){
    const actionContributions=proposals.filter(c=>accepted.has(c.mechanismId)&&c.diagnostics?.domain===d.id);
    const eligible=d.candidates.filter(c=>c.feasible);
    if(!actionContributions.length||!eligible.length)continue;
    const ranked=eligible.map(c=>({candidate:c,score:actionContributions.reduce((sum,p)=>sum+p.diagnostics.weight*accepted.get(p.mechanismId).weight*c.metrics[p.diagnostics.objective],0)})).toSorted((a,b)=>a.score-b.score||a.candidate.id.localeCompare(b.candidate.id));
    plans[d.id]={...ranked[0].candidate,arbitrationScore:ranked[0].score,votes:actionContributions.map(c=>({mechanism:c.mechanismId,preferred:c.diagnostics.preferredCandidate,weight:accepted.get(c.mechanismId).weight})),ranking:ranked.map(x=>({id:x.candidate.id,score:x.score}))};
   }
  }
  this.state=result.nextState;this.state.resources.usedComputeEnergy=used;
  this.state.memory=this.memory.consolidateMemory(this.state,observation,result.consequence,request.goal);
  this.state.metadata.stateHash=hash(this.state);
  result.ledgerEntry.newStateHash=this.state.metadata.stateHash;
  result.ledgerEntry.rejectedContributions.push(...budgetRejected.map(mechanismId=>({mechanismId,reason:'compute budget exhausted'})));
  this.pending={previous:clone(snapshot),proposals:proposals.filter(c=>accepted.has(c.mechanismId)),accepted:[...accepted.keys()],rejected:result.ledgerEntry.rejectedContributions.map(c=>c.mechanismId),plans,ledger:result.ledgerEntry};
  this.tracker.recordStep(result.ledgerEntry,result.consequence);
  return {plans,ledger:result.ledgerEntry,health:computeRuntimeHealth(this.state,this.reputation,result.consequence),
    retrieved_context:retrieveContextForLLM(this.state,request.goal),mechanism_count:all.length,routed_count:routed.length,used_budget:used,budget:snapshot.resources.totalComputeBudget,
    memory_layers:this.memoryLayers(),reputations:this.reputation.getAllReputations(),state_hash:this.state.metadata.stateHash,context:this.state.context};
 }
 observe(outcome){
  if(!this.pending)throw Error('no pending governance decision');
  if(!outcome||!outcome.observations||typeof outcome.committed!=='boolean')throw Error('outcome requires observations and committed boolean');
  for(const key of this.state.registeredNodeIds)if(!Object.hasOwn(outcome.observations,key))throw Error('incomplete observed outcome');
  const priorHash=this.state.metadata.stateHash;
  const actual=clone(this.state);
  for(const [key,value] of Object.entries(outcome.observations)){
   if(!Object.hasOwn(actual.field.values,key)||!Number.isFinite(value)||value<0||value>1)throw Error('invalid outcome observation');
   actual.field.values[key]=value;
  }
  if(outcome.progress!==undefined&&!Number.isFinite(outcome.progress))throw Error('invalid progress');
  actual.goals.progressRatio=bounded(outcome.progress??actual.goals.progressRatio);
  actual.stress.consecutiveAlerts=outcome.committed?0:actual.stress.consecutiveAlerts+1;
  const consequence=evaluateConsequences(this.pending.previous,actual,this.pending.proposals);
  if(!outcome.committed){for(const credit of consequence.creditAssignments){credit.reward=0;credit.blame=1;}consequence.causalConfidence=.1;}
  this.reputation.updateReputations(this.pending.accepted,this.pending.rejected,consequence);
  actual.domainExperience=actual.domainExperience||{};
  for(const [id,plan] of Object.entries(this.pending.plans)){
   const pairs=Object.entries(plan.predicted_observations||{}).filter(([key])=>Object.hasOwn(outcome.observations,`${id}.${key}`));
   if(pairs.length&&outcome.committed){
    const error=pairs.reduce((sum,[key,v])=>sum+Math.abs(v-outcome.observations[`${id}.${key}`]),0)/pairs.length;
    const old=actual.domainExperience[id]||{samples:0,prediction_error_ema:0};
    actual.domainExperience[id]={samples:old.samples+1,prediction_error_ema:old.samples?.8*old.prediction_error_ema+.2*error:error,last_candidate:plan.id};
    const memoryId=`mem_domain_${id}_${actual.metadata.step}`;
    actual.memory.nodes[memoryId]={id:memoryId,type:'episodic',content:`${id} observed ${plan.id}; normalized prediction error ${error.toFixed(3)}`,vector:[error],salience:.8,lastAccessedStep:actual.metadata.step,associatedNodeIds:Object.keys(outcome.observations).filter(k=>k.startsWith(id+'.'))};
   }
  }
  this.state=actual;this.state.memory=this.memory.consolidateMemory(this.state,undefined,consequence);
  this.state.metadata.stateHash=hash(this.state);
  const feedback={previous_state_hash:priorHash,consequence,health:computeRuntimeHealth(this.state,this.reputation,consequence),memory_layers:this.memoryLayers(),domain_experience:this.state.domainExperience||{},reputations:this.reputation.getAllReputations(),state_hash:this.state.metadata.stateHash};
  this.pending=null;return feedback;
 }
 memoryLayers(){const nodes=Object.values(this.state?.memory.nodes||{});return {working:this.state?.memory.workingMemory.activeObservations.length||0,episodic:nodes.filter(n=>n.type==='episodic').length,semantic:nodes.filter(n=>n.type==='semantic').length,procedural:nodes.filter(n=>n.type==='procedural').length};}
}
