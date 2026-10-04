import {readFileSync} from 'node:fs';
import {WorldGovernor} from './governor.mjs';
try{
 const input=JSON.parse(readFileSync(0,'utf8'));const governor=new WorldGovernor(input.session);
 const result=input.operation==='observe'?governor.observe(input.payload):governor.plan(input.payload);
 console.log(JSON.stringify({result,session:governor.export()}));
}catch(error){console.error(error.message);process.exit(1);}
