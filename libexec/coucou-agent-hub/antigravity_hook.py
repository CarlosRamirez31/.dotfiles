"""Antigravity public-hook observer: preserve native permissions and exact IDs."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    event=sys.argv[1] if len(sys.argv)>1 else ''
    if event not in ('SessionStart','PreToolUse','PostToolUse','PreInvocation','PostInvocation','Stop'):
        print('{}');return
    try:
        item=json.load(sys.stdin)
        observation={key:item[key] for key in ('conversationId','workspacePaths','transcriptPath') if key in item}
        try:
            subprocess.run(['agent-hub','agy-run','--observe'],input=json.dumps(observation),text=True,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3,check=False)
        except (OSError,subprocess.TimeoutExpired):pass
        mapped={'PreInvocation':'UserPromptSubmit','PostInvocation':'PostToolUse'}.get(event,event)
        item['hook_event_name']=mapped
        relay=Path.home()/'.local/share/coucou/bin/coucou-hook'
        reply=subprocess.run([str(relay),'--agent','antigravity',mapped],input=json.dumps(item),text=True,
            capture_output=True,timeout=3,check=False)
        # The installed relay returns ask for PreToolUse; never auto_approve.
        print(reply.stdout.strip() or ('{"decision":"ask"}' if event=='PreToolUse' else '{}'))
    except (OSError,ValueError,subprocess.TimeoutExpired):
        print('{"decision":"ask"}' if event=='PreToolUse' else '{}')

if __name__=='__main__':main()
