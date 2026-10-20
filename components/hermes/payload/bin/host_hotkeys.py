#!/usr/bin/env python3
"""Temporary host Awesome bindings; all files and execution stay in dev."""
import json,os,subprocess,sys
from pathlib import Path
RUN=Path('/opt/presentacion/run')
def host_env(s):
    env=dict(os.environ,DISPLAY=s['host_display'],DBUS_SESSION_BUS_ADDRESS=s['host_bus'])
    if s.get('host_xauthority'):env['XAUTHORITY']=s['host_xauthority']
    return env

def change(action,pid,session):
    s=json.loads((RUN/'state.json').read_text())
    identity=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
    token=str(pid)+':'+identity+':'+session
    prefix='local token='+json.dumps(token)+'; '
    restore='''local rec=_G._presentacion_hermes_host_keys;
if rec and rec.token==token then rec.restore(); return true end; return true'''
    install='''
local gears=require('gears');local awful=require('awful');
local prev=_G._presentacion_hermes_host_keys;
if prev then if prev.token==token then return true end; return 'Ya hay otro Hermes conectado a los atajos del host' end;
local function target(k)
 local m={};for _,v in ipairs(k.modifiers) do if v~='Lock' and v~='Mod2' then table.insert(m,v) end end;table.sort(m);
 local mods=table.concat(m,',');return (k.key=='Print' and (mods=='' or mods=='Mod1')) or (k.key=='s' and mods=='Mod1,Shift')
end;
local old={};local keep={};for _,k in ipairs(root.keys()) do if target(k) then table.insert(old,k) else table.insert(keep,k) end end;
local generated=gears.table.join(
 awful.key({},'Print',function() awful.spawn({'distrobox','enter','dev','--','/opt/presentacion/bin/screenshot','--host','full'},false) end),
 awful.key({'Mod1'},'Print',function() awful.spawn({'distrobox','enter','dev','--','/opt/presentacion/bin/screenshot','--host','area'},false) end),
 awful.key({'Mod1','Shift'},'s',function() awful.spawn({'distrobox','enter','dev','--','/opt/presentacion/bin/screenshot','--host','area'},false) end));
local ours={};for _,k in ipairs(generated) do ours[k]=true;table.insert(keep,k) end;
local rec={token=token};_G._presentacion_hermes_host_keys=rec;
rec.restore=function()
 if _G._presentacion_hermes_host_keys~=rec then return end;
 if rec.timer then rec.timer:stop() end;
 local keys={};for _,k in ipairs(root.keys()) do if not ours[k] then table.insert(keys,k) end end;
 for _,k in ipairs(old) do table.insert(keys,k) end;root.keys(keys);_G._presentacion_hermes_host_keys=nil;
end;
root.keys(keep);
local function alive()
 local f=io.open('/proc/PID/stat','r');if not f then return false end;
 local v=f:read('*a');f:close();local tail=v:match('^%d+ %b() (.*)$');if not tail then return false end;
 local fields={};for w in tail:gmatch('%S+') do table.insert(fields,w) end;
 return fields[20]=='START' and fields[1]~='Z'
end;
rec.timer=gears.timer({timeout=1,autostart=true,callback=function() if not alive() then rec.restore() end end});
return true
'''.replace('PID',str(int(pid))).replace('START',identity)
    result=subprocess.run(['awesome-client',prefix+(install if action=='install' else restore)],env=host_env(s),capture_output=True,text=True,timeout=5,check=True)
    if 'boolean true' not in result.stdout:raise RuntimeError(result.stdout.strip() or result.stderr.strip() or 'Awesome del host rechazó los atajos.')
    return token
if __name__=='__main__':
    try:
        info=json.loads((RUN/'hermes.json').read_text());change(sys.argv[1],info['pid'],info['session']);print('Atajos del host actualizados.')
    except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as exc:print('Error:',exc,file=sys.stderr);sys.exit(1)
