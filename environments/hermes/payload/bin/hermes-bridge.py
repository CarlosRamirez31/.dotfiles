#!/usr/bin/env python3
"""An opt-in image inbox for one foreground Hermes CLI, without changing Hermes."""
import atexit,fcntl,json,os,signal,socket,sys,threading,time
from pathlib import Path
ROOT=Path('/opt/presentacion'); RUN=ROOT/'run'
SOCKET=RUN/'hermes.sock'; INFO=RUN/'hermes.json'
CAPTURES=Path('@HOST_HOME@/Documents/Universidad/salidas/capturas').resolve()
os.umask(0o077)
lock=(RUN/'hermes.lock').open('w')
try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError: raise SystemExit('Ya hay un Hermes conectado a las capturas.')
state=json.loads((RUN/'state.json').read_text()); session=state['session']
if os.environ.get('DISPLAY')==state['display']: raise SystemExit('Abre Hermes desde la terminal exterior, fuera del escritorio virtual.')
stop=threading.Event(); server=None

def cleanup():
    stop.set()
    if server:
        try: server.close()
        except OSError: pass
    try:
        from host_hotkeys import change
        change('restore',os.getpid(),session)
    except Exception: pass
    try:
        info=json.loads(INFO.read_text())
        if info['pid']==os.getpid(): INFO.unlink(missing_ok=True);SOCKET.unlink(missing_ok=True)
    except (OSError,ValueError,KeyError): pass
atexit.register(cleanup)

def receive(cli):
    global server
    # Register only once the actual interactive prompt can receive turns.
    while not stop.wait(.1):
        app=getattr(cli,'_app',None)
        if app and app.is_running: break
        if getattr(cli,'_should_exit',False): return
    else: return
    SOCKET.unlink(missing_ok=True)
    server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(str(SOCKET));SOCKET.chmod(0o600)
    server.listen(2);server.settimeout(1)
    INFO.write_text(json.dumps({'pid':os.getpid(),'session':session,'socket':str(SOCKET)}))
    try:
        from host_hotkeys import change
        change('install',os.getpid(),session)
    except Exception as exc:
        print('No se pudieron activar los atajos del host: '+str(exc),flush=True)
        cleanup();return
    try:
        while not stop.is_set() and not getattr(cli,'_should_exit',False):
            try:
                if json.loads((RUN/'state.json').read_text()).get('session')!=session: break
                connection,_=server.accept()
            except socket.timeout: continue
            except (OSError,ValueError): break
            terminate=False
            with connection:
                connection.settimeout(2)
                try:
                    payload=b''
                    while b'\n' not in payload:
                        part=connection.recv(4096)
                        if not part or len(payload)+len(part)>8192: raise ValueError('Petición no válida.')
                        payload+=part
                    request=json.loads(payload.split(b'\n')[0])
                    if request.get('session')!=session: raise ValueError('La sesión virtual cambió.')
                    action=request.get('action')
                    if action=='image':
                        if request.get('source')!='host' or request.get('display')!=state['host_display']: raise ValueError('Solo se reciben capturas del host.')
                        path=Path(request['path']).resolve()
                        if not path.is_relative_to(CAPTURES) or path.suffix.lower()!='.png' or not path.is_file(): raise ValueError('Solo se aceptan capturas PNG de Universidad/salidas/capturas.')
                        if path.stat().st_size>16_000_000: raise ValueError('Captura demasiado grande.')
                        if path.open('rb').read(8)!=b'\x89PNG\r\n\x1a\n': raise ValueError('PNG no válido.')
                        if cli._pending_input.qsize()>=1: raise ValueError('Hermes ya tiene una captura o mensaje en espera. Espera a que lo procese.')
                        prompt=(ROOT/'config/hermes-capture-prompt.txt').read_text().strip()
                        # Same tuple type Hermes uses for native attached images.
                        cli._pending_input.put((prompt,[path]))
                        response={'ok':True,'message':'Captura adjuntada a Hermes.'}
                    elif action=='status':response={'ok':True,'pid':os.getpid(),'session':session}
                    elif action=='stop':response={'ok':True,'message':'Cerrando Hermes y desactivando la interceptación.'};terminate=True
                    else: raise ValueError('Acción no válida.')
                except (OSError,ValueError,KeyError,TypeError) as exc: response={'ok':False,'message':str(exc)}
                try: connection.sendall(json.dumps(response).encode()+b'\n')
                except OSError: pass
            if terminate:
                os.kill(os.getpid(),signal.SIGTERM);return
    finally:
        cleanup()
    # A closed/replaced virtual desktop must not leave its inbox enabled.
    if not stop.is_set() or not getattr(cli,'_should_exit',False):
        os.kill(os.getpid(),signal.SIGTERM)

sys.path.insert(0,str(ROOT/'bin'))
import cli
original=cli.HermesCLI._tui_init_run_state

def initialize(self,*args,**kwargs):
    result=original(self,*args,**kwargs)
    threading.Thread(target=receive,args=(self,),daemon=True,name='virtual-image-inbox').start()
    return result
cli.HermesCLI._tui_init_run_state=initialize
print('Hermes conectado a las capturas del HOST. Print: pantalla física completa; Alt+Shift+S: área. Libera Xephyr con Ctrl+Shift para usar los atajos del host.\nAl salir de Hermes se desactiva la interceptación.\n',flush=True)
sys.argv=['hermes','chat','--cli','--in','@HOST_HOME@/Documents/Universidad']
try:
    from hermes_cli.main import main
    main()
finally: cleanup()
