"""Coucou control plane: public CLI only; persistent work state stays in Hub."""
import json
import re
import subprocess
from agent_hub_terminal import BridgeError


def control(bridge, request):
    operation=request.get('operation')
    if operation not in ('plan','refine','show','execute','cancel','list','open-execution'):
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
    command=['agent-hub','work','run','request' if operation in ('plan','refine') else operation]
    if operation in ('plan','refine'):
        query=request.get('query')
        if not isinstance(query,str) or not query.strip() or len(query)>200000:
            raise BridgeError('Describe la tarea que quieres preparar.')
        command+=['--intent',query]
        if operation=='refine':
            ident=request.get('id')
            if not isinstance(ident,str) or not re.fullmatch(r'RUN-[0-9]{3,12}',ident):raise BridgeError('ID de plan inválido.')
            command+=['--continue-run',ident]
        if request.get('automatic') is True or request.get('agent') is None:command+=['--auto']
        if request.get('directory'):
            if not isinstance(request['directory'],str):raise BridgeError('Carpeta de proyecto inválida.')
            command+=['--repo',request['directory']]
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
                          timeout=None if operation in ('plan','refine','execute') else 20,check=False)
    except (OSError,subprocess.TimeoutExpired) as error:
        raise BridgeError('No se pudo consultar Agent Hub: '+str(error)) from error
    try:
        value=json.loads(result.stdout)
    except ValueError as error:
        raise BridgeError(result.stderr.strip()[:3000] or 'Agent Hub no devolvió un estado de trabajo válido.') from error
    if isinstance(value,dict) and 'run' in value:
        report=value
        lines=[report.get('summary') or 'Tarea del proyecto', 'Estado: '+str(report.get('status'))]
        memory=report.get('architecture') or {}
        if memory.get('path'):lines.append('Arquitectura externa: '+memory['path'])
        run=report.get('run')
        if run:
            lines.append(run['id']+' · '+run['status'])
            planned=run['configuration']['request']['plan']
            lines+=['Alcance: '+', '.join(planned['files']), 'Validación: '+ '; '.join(' '.join(argv) for argv in planned['checks'])]
            if report.get('status')=='ready':lines.append('/ejecutar '+run['id']+' inicia esta tarea preparada.')
            if run.get('status')=='waiting_human':
                for entry in run.get('results',[]):
                    error=entry.get('error') or (entry.get('result') or {}).get('error')
                    if error:lines.append(error)
        lines+=['Pendiente: '+question for question in report.get('questions',[])]
        if run and report.get('status')=='needs_input':lines.append('Para definirlo: /definir '+run['id']+' tus respuestas y decisiones')
        for item in report.get('applied',[]):lines.append('Cambios aplicados: '+', '.join(item['files']))
        return {'ok':True,'text':'\n'.join(lines),'run':run,'request':report}
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
