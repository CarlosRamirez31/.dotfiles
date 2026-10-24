"""Restore Gemini's local Coucou observers; never install auth or permissions."""
import argparse
import copy
import json
import os
from pathlib import Path
import shlex
import uuid
from agent_hub_terminal import atomic_json, private_dir

EVENTS = {'SessionStart':'SessionStart', 'SessionEnd':'SessionEnd',
          'BeforeTool':'PreToolUse', 'AfterTool':'PostToolUse',
          'BeforeAgent':'UserPromptSubmit', 'AfterAgent':'Stop'}


def configure(settings, relay):
    settings, relay = Path(settings), Path(relay).resolve()
    if not relay.is_file() or not os.access(relay, os.X_OK):
        raise ValueError('Falta el relay instalado de Coucou: '+str(relay))
    original = json.loads(settings.read_text()) if settings.exists() else {}
    if not isinstance(original,dict):
        raise ValueError('Gemini settings.json debe ser un objeto.')
    updated = copy.deepcopy(original)
    for field in ('hooks','privacy','telemetry'):
        if not isinstance(updated.setdefault(field,{}),dict):
            raise ValueError('Configuración no válida de Gemini: '+field)
    for event, mapped in EVENTS.items():
        groups = updated['hooks'].setdefault(event,[])
        if not isinstance(groups,list):raise ValueError('Hooks de Gemini no válidos: '+event)
        name = 'coucou-gemini-'+event.lower()
        for group in groups:
            if not isinstance(group,dict) or not isinstance(group.get('hooks',[]),list):
                raise ValueError('Grupo de hooks de Gemini no válido.')
        # Replace only this installer's named observer; preserve foreign hooks.
        for group in groups:
            group['hooks'] = [hook for hook in group.get('hooks',[]) if hook.get('name')!=name]
        groups[:] = [group for group in groups if group.get('hooks')]
        groups.append({'matcher':'*','hooks':[{'name':name,'type':'command',
            'command':shlex.join([str(relay),'--agent','gemini',mapped]),'timeout':5000}]})
    updated['privacy']['usageStatisticsEnabled'] = False
    updated['telemetry'].update(enabled=False,logPrompts=False)
    if updated == original:return False
    private_dir(settings.parent)
    if settings.exists():
        backup = private_dir(settings.parent/'coucou-backups')/(settings.name+'-'+uuid.uuid4().hex)
        atomic_json(backup,original)
    atomic_json(settings,updated)
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--relay',type=Path,required=True)
    args=parser.parse_args()
    configure(args.settings,args.relay)
    print('Gemini: six local observers ready; telemetry/statistics disabled; authentication unchanged.')

if __name__=='__main__':main()
