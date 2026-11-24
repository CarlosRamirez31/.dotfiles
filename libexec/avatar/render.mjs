import {Style, Avatar, OptionsDescriptor} from '../../share/avatar/vendor/core/lib/index.js';
import {readFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const directory=fileURLToPath(new URL('../../share/avatar/vendor/styles/dist/',import.meta.url));
const request=JSON.parse(readFileSync(0,'utf8'));
const names=readdirSync(directory).filter(n=>n.endsWith('.min.json')).map(n=>n.slice(0,-9)).sort();
function style(name){if(!names.includes(name))throw Error('Unknown style');return new Style(JSON.parse(readFileSync(`${directory}/${name}.min.json`,'utf8')));}
if(request.action==='catalog'){
 console.log(JSON.stringify(names.map(name=>{const s=style(name);const def=JSON.parse(readFileSync(`${directory}/${name}.min.json`,'utf8'));return {name,meta:def.meta,svg:new Avatar(s,{seed:'beambollow',size:96}).toString()};})));
}else{
 const s=style(request.style);
 if(request.action==='variants'){
  const field=new OptionsDescriptor(s).toJSON()[request.field];
  if(!field || field.type!=='enum')throw Error('Unknown visual option');
  const probability=request.field.replace(/Variant$/, 'Probability');
  const visible=new OptionsDescriptor(s).toJSON()[probability]?{[probability]:100}:{};
  console.log(JSON.stringify(field.values.map(value=>({value,svg:new Avatar(s,{...request.options,...visible,[request.field]:field.list?[value]:value,size:80}).toString()}))));
 } else {
 const avatar=new Avatar(s,{...request.options,size:512});
 console.log(JSON.stringify({svg:avatar.toString(),resolved:avatar.toJSON().options,fields:new OptionsDescriptor(s).toJSON()}));
 }
}
