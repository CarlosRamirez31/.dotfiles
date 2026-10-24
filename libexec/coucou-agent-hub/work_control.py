"""Coucou control plane: public CLI only; persistent work state stays in Hub."""
import json
import re
import subprocess
from agent_hub_terminal import BridgeError


def control(bridge, request):
    operation=request.get('operation')
    if operation not in ('plan','show','execute','cancel','list','open-execution'):
        raise BridgeError('Operación de trabajo desconocida.')
    if operation=='open-execution':
        ident=request.get('id')
        if not isinstance(ident,str) or not re.fullmatch(r'EXEC-[0-9]{3,12}',ident):
            raise BridgeError('ID de ejecución inválido.')
        result=bridge.hub('work','execution','route',ident,'--json')
        route=result.get('route')
        bridge.associate({'agent':route['agente'],'sessionId':result['native_id'],'route':route})
        opened=bridge.open({'agent':route['agente'],'sessionId':result['native_id'],'route':route})
        if not opened.get('ok'):
            raise BridgeError('No se pudo abrir la conversación exacta de la ejecución.')
        return {'ok':True,'text':'Conversación de '+ident+' abierta mediante Agent Hub.','execution':result}
    command=['agent-hub','work','run',operation]
    if operation=='plan':
        query=request.get('query')
        if not isinstance(query,str) or not query.strip() or len(query)>200000:
            raise BridgeError('Describe la tarea que quieres preparar.')
        command+=['--intent',query]
        # The Hub command is named plan, not create. Fixed assignment is explicit;
        # absence of agent requests deterministic orchestrated routing.
        agent=request.get('agent')
        if agent is not None:
            if not isinstance(agent,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}',agent):
                raise BridgeError('Agente de la tarea inválido.')
            command+=['--agent',agent]
    elif operation!='list':
        ident=request.get('id')
        if not isinstance(ident,str) or not re.fullmatch(r'RUN-[0-9]{3,12}',ident):
            raise BridgeError('ID de run inválido.')
        command.append(ident)
    command+=['--json']
    if not bridge.which('agent-hub'):
        raise BridgeError('Agent Hub no está instalado.')
    try:
        # execute has its own persisted budgets and cancellation protocol; an
        # outer 20-second timeout could abandon managed workers midway through.
        result=bridge.run(command,capture_output=True,text=True,encoding='utf-8',
                          timeout=None if operation=='execute' else 20,check=False)
    except (OSError,subprocess.TimeoutExpired) as error:
        raise BridgeError('No se pudo consultar Agent Hub: '+str(error)) from error
    try:
        value=json.loads(result.stdout)
    except ValueError as error:
        raise BridgeError(result.stderr.strip()[:3000] or 'Agent Hub no devolvió un estado de trabajo válido.') from error
    if operation=='list':
        message='\n'.join(f"{run['id']} · {run['status']} · {run['title']}" for run in value) or 'Todavía no hay tareas preparadas.'
    else:
        message=f"{value['id']} · {value['title']}\nEstado: {value['status']}\n"
        message+='\n'.join(f"• {task['id']} · {task['status']} · {task['contract']['title']}" for task in value['tasks'])
        if operation=='plan':
            message+='\n\nPlan guardado en Agent Hub. Antes de ejecutar, configura su repositorio, checks y permisos. /estado '+value['id']+' consulta el avance.'
        if value['status']=='waiting_human':
            errors=[entry.get('error') for entry in value.get('results',[]) if entry.get('error')]
            message+='\n\n'+ ('\n'.join(errors) if errors else 'Se necesita revisar los controles o resultados en Agent Hub.')
    return {'ok':True,'text':message,'run':value}
