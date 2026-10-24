"""Install only Coucou's named Antigravity hooks; do not touch authentication."""
import argparse
import copy
import json
from pathlib import Path
import shlex
import uuid
from agent_hub_terminal import atomic_json, private_dir
EVENTS=('SessionStart','PreToolUse','PostToolUse','PreInvocation','PostInvocation','Stop')
TOOL_EVENTS=('PreToolUse','PostToolUse')


def configure(path, observer):
    path,observer=Path(path),Path(observer).resolve()
    if not observer.is_file():raise ValueError('Falta el observer de Antigravity.')
    original=json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(original,dict):raise ValueError('hooks.json debe ser un objeto.')
    updated=copy.deepcopy(original)
    observer_hooks={}
    for event in EVENTS:
        cmd=shlex.join(['python3','-B',str(observer),event])
        handler={'type':'command','command':cmd,'timeout':8}
        if event in TOOL_EVENTS:
            observer_hooks[event]=[{'matcher':'*','hooks':[handler]}]
        else:
            observer_hooks[event]=[handler]
    updated['coucou-cli-observer']=observer_hooks
    if updated==original:return False
    private_dir(path.parent)
    if path.exists():atomic_json(private_dir(path.parent/'coucou-backups')/('hooks-'+uuid.uuid4().hex+'.json'),original)
    atomic_json(path,updated);return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hooks',type=Path,required=True);parser.add_argument('--observer',type=Path,required=True)
    args=parser.parse_args();configure(args.hooks,args.observer)
    print('Six Antigravity CLI observers ready; authentication and native permissions unchanged.')

if __name__=='__main__':main()
