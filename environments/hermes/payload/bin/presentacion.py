#!/usr/bin/env python3
"""Escritorio X11 de presentación, instalado exclusivamente en dev."""
import argparse, base64, datetime, fcntl, http.server, json, os
from pathlib import Path
import re, secrets, shutil, signal, socket, subprocess, sys, threading, time

ROOT = Path('/opt/presentacion')
RUN = ROOT / 'run'
STATE = RUN / 'state.json'
CAPTURES = Path('@HOST_HOME@/Documents/Universidad/salidas/capturas')


def require_dev():
    if os.environ.get('CONTAINER_ID') != 'dev':
        raise RuntimeError('Ejecuta este comando dentro de Distrobox dev.')


def alive(pid):
    try:
        cmd = Path(f'/proc/{int(pid)}/cmdline').read_bytes()
        return b'presentacion.py' in cmd and b'_sesion' in cmd
    except (OSError, ValueError, TypeError):
        return False


def state(required=True):
    try:
        s = json.loads(STATE.read_text())
        if alive(s['pid']): return s
    except (OSError, ValueError, KeyError):
        pass
    if required: raise RuntimeError('No hay escritorio activo. Usa: presentacion iniciar')
    return None


def nested_env(s):
    env = dict(os.environ)
    for name in ('WAYLAND_DISPLAY','MOZ_ENABLE_WAYLAND','DBUS_SESSION_BUS_ADDRESS','SESSION_MANAGER','LIBGL_ALWAYS_SOFTWARE'):
        env.pop(name, None)
    env.update(DISPLAY=s['display'], XAUTHORITY=str(RUN/'Xauthority'),
               GDK_BACKEND='x11', MOZ_ENABLE_WAYLAND='0', GTK_USE_PORTAL='0',
               XDG_SESSION_TYPE='x11', XDG_CURRENT_DESKTOP='awesome',
               XDG_SESSION_DESKTOP='awesome', FONTCONFIG_FILE=str(ROOT/'config/fonts.conf'), PRESENTACION_SESSION=s.get('session',''),
               XDG_CONFIG_HOME=str(ROOT/'xdg/config'), XDG_CACHE_HOME=str(ROOT/'xdg/cache'),
               XDG_DATA_HOME=str(ROOT/'xdg/data'), XDG_STATE_HOME=str(ROOT/'xdg/state'))
    if (RUN/'bus-address').exists():
        env['DBUS_SESSION_BUS_ADDRESS']=(RUN/'bus-address').read_text().strip()
    return env


def spawn(command, env, logfile):
    with open(logfile, 'ab', buffering=0) as log:
        return subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,
                                stdout=log,stderr=log,start_new_session=True)


def firefox(s, url=None):
    # Only one private profile may own the Firefox lock at a time.
    pidfile=RUN/'firefox.pid'
    if pidfile.exists():
        pid=int(pidfile.read_text())
        try:
            if b'/opt/presentacion/firefox-profile' in Path(f'/proc/{pid}/cmdline').read_bytes():
                senv=nested_env(s)
                found=subprocess.run(['xdotool','search','--onlyvisible','--class','^firefox$'],env=senv,capture_output=True,text=True)
                if found.returncode==0 and found.stdout.strip():
                    window=found.stdout.splitlines()[0]
                    subprocess.run(['xdotool','windowactivate','--sync',window],env=senv,check=True,timeout=5)
                    if url:
                        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+l','type','--clearmodifiers',url],env=senv,check=True,timeout=5)
                        subprocess.run(['xdotool','key','--clearmodifiers','Return'],env=senv,check=True,timeout=5)
                    return None
                raise RuntimeError('Firefox ya está abierto en la pantalla virtual.')
        except OSError: pass
    p=spawn(['firefox','--no-remote','--new-instance','--profile',str(ROOT/'firefox-profile'),
             url or f"http://127.0.0.1:{s['port']}/"],nested_env(s),RUN/'firefox.log')
    pidfile.write_text(str(p.pid))
    return p


class TestServer(http.server.ThreadingHTTPServer):
    daemon_threads=True


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT/'www'),**kw)
    def log_message(self,*a): pass
    def do_POST(self):
        origin=f'http://127.0.0.1:{self.server.server_port}'
        if self.headers.get('Origin')!=origin:
            self.send_error(403); return
        size=int(self.headers.get('Content-Length','0'))
        if not 0<size<=12_000_000:
            self.send_error(413); return
        try:
            data=json.loads(self.rfile.read(size))
            verification=ROOT/'verification'; verification.mkdir(exist_ok=True,mode=0o700)
            if self.path=='/screen-proof':
                image=data.pop('image')
                if not image.startswith('data:image/png;base64,'): raise ValueError()
                (verification/'firefox-screen.png').write_bytes(base64.b64decode(image.split(',',1)[1],validate=True))
                (verification/'firefox-screen.json').write_text(json.dumps(data,indent=2))
            elif self.path=='/device-proof':
                (verification/'devices.json').write_text(json.dumps(data,indent=2))
            else:
                self.send_error(404); return
            self.send_response(200); self.end_headers(); self.wfile.write(b'OK')
        except (ValueError,KeyError,TypeError): self.send_error(400)


def supervisor(args):
    os.umask(0o077)
    RUN.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=open(RUN/'session.lock','w')
    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('Ya hay una sesión en ejecución.')
    display=next((f':{n}' for n in range(100,200)
                  if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
    if not display: raise RuntimeError('No hay un número de display disponible.')
    for name in ('xephyr.log','desktop.log','resize.log','polybar.log','picom.log'):
        (RUN/name).write_text('')
    host_env=dict(os.environ)
    authority=RUN/'Xauthority'; authority.touch(mode=0o600)
    subprocess.run(['xauth','-f',str(authority),'add',display,'MIT-MAGIC-COOKIE-1',secrets.token_hex(16)],check=True)
    s={}; children=[]; stopped=threading.Event(); server=None
    for sig in (signal.SIGTERM,signal.SIGINT): signal.signal(sig,lambda *_:stopped.set())
    (RUN/'bus-address').unlink(missing_ok=True)
    try:
        xephyr=['Xephyr',display,'-glamor','-auth',str(authority),'-nolisten','tcp','-screen',args.resolucion,
                '-resizeable','-noreset','-title','Presentación · dev']
        if args.pantalla_completa: xephyr.append('-fullscreen')
        x=spawn(xephyr,host_env,RUN/'xephyr.log'); children.append(x)
        s={'pid':os.getpid(),'display':display,'host_display':host_env.get('DISPLAY',':0'),
           'host_xauthority':host_env.get('XAUTHORITY',''),'host_bus':host_env.get('DBUS_SESSION_BUS_ADDRESS','unix:path=/run/user/'+str(os.getuid())+'/bus'),'resolution':args.resolucion,'session':secrets.token_hex(16)}
        for _ in range(100):
            if x.poll() is not None: raise RuntimeError('Xephyr terminó. Revisa presentacion registro.')
            ready=subprocess.run(['xdpyinfo'],env=nested_env(s),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
            if ready: break
            time.sleep(.1)
        else: raise RuntimeError('Xephyr no respondió a tiempo.')
        env=nested_env(s)
        desktop=spawn(['dbus-run-session','--',str(ROOT/'bin/desktop-session')],env,RUN/'desktop.log')
        children.append(desktop)
        for _ in range(100):
            if (RUN/'bus-address').exists(): break
            if desktop.poll() is not None: raise RuntimeError('Awesome terminó. Revisa el registro.')
            time.sleep(.05)
        server=TestServer(('127.0.0.1',0),Handler); s['port']=server.server_port
        threading.Thread(target=server.serve_forever,daemon=True).start()
        temp=RUN/'state.tmp'; temp.write_text(json.dumps(s)); temp.replace(STATE)
        if not args.sin_firefox:
            browser=firefox(s)
            if browser: children.append(browser)
        while not stopped.wait(.3):
            if x.poll() is not None or desktop.poll() is not None: break
    finally:
        if server: server.shutdown(); server.server_close()
        # Stop only process groups started for this session.
        apps=RUN/'applications.jsonl'
        if apps.exists():
            for line in apps.read_text().splitlines():
                try:
                    entry=json.loads(line); pid=entry['pid']
                    marker=('PRESENTACION_SESSION='+entry['session']).encode()
                    if entry['session']==s.get('session') and marker in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'):
                        os.killpg(pid,signal.SIGTERM)
                except (OSError,ValueError,KeyError): pass
            apps.unlink(missing_ok=True)
        p=RUN/'firefox.pid'
        if p.exists():
            try:
                pid=int(p.read_text())
                if b'/opt/presentacion/firefox-profile' in Path(f'/proc/{pid}/cmdline').read_bytes():
                    os.killpg(pid,signal.SIGTERM)
            except (OSError,ValueError): pass
        for child in reversed(children):
            try: os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError: pass
        for child in children:
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
        STATE.unlink(missing_ok=True)
        for name in ('Xauthority','firefox.pid','bus-address'): (RUN/name).unlink(missing_ok=True)


def stop():
    s=state(False)
    if not s: print('El escritorio ya está cerrado.'); return
    os.kill(s['pid'],signal.SIGTERM)
    for _ in range(100):
        if not state(False): print('Escritorio cerrado.'); return
        time.sleep(.1)
    raise RuntimeError('El cierre sigue en curso. Revisa presentacion estado.')


def resize(s, resolution):
    if not re.fullmatch(r'[1-9]\d{2,3}x[1-9]\d{2,3}',resolution):
        raise RuntimeError('Usa un tamaño como 1280x720.')
    w,h=map(int,resolution.split('x'))
    host=dict(os.environ,DISPLAY=s['host_display'],DBUS_SESSION_BUS_ADDRESS=s.get('host_bus','unix:path=/run/user/'+str(os.getuid())+'/bus'))
    if s['host_xauthority']: host['XAUTHORITY']=s['host_xauthority']
    found=subprocess.run(['xdotool','search','--class','^Xephyr$'],env=host,capture_output=True,text=True,check=True)
    windows=[]
    for wid in found.stdout.split():
        title=subprocess.run(['xdotool','getwindowname',wid],env=host,capture_output=True,text=True).stdout.strip()
        if title=='Presentación · dev': windows.append(int(wid))
    if len(windows)!=1: raise RuntimeError('No se pudo identificar una única ventana de presentación.')
    lua='for _,c in ipairs(client.get()) do if c.window=='+str(windows[0])+""" then if not c.presentacion_resizebutton then local gears=require('gears'); local awful=require('awful'); c:buttons(gears.table.join(c:buttons(),awful.button({'Mod1'},3,function() awful.mouse.client.resize(c) end))); c.presentacion_resizebutton=true end; c.fullscreen=false; c.maximized=false; c.floating=true; local a=c.screen.workarea; local w=math.min("""+str(w)+',a.width-20); local h=math.min('+str(h)+',a.height-20); c:geometry({x=a.x+math.floor((a.width-w)/2),y=a.y+math.floor((a.height-h)/2),width=w,height=h}); return true end end; return false'
    result=subprocess.run(['awesome-client',lua],env=host,capture_output=True,text=True,check=True)
    if 'true' not in result.stdout: raise RuntimeError('Awesome no encontró la ventana de presentación.')
    print('Tamaño actualizado; se adapta al espacio disponible del monitor.')


def cpu_report(s, seconds):
    if not 1<=seconds<=30: raise RuntimeError('Usa entre 1 y 30 segundos.')
    hz=os.sysconf('SC_CLK_TCK')
    def snapshot():
        rows={}
        for d in Path('/proc').glob('[0-9]*'):
            try:
                value=(d/'stat').read_text(); fields=value[value.rindex(')')+2:].split()
                rows[int(d.name)]={'ticks':int(fields[11])+int(fields[12]),'ppid':int(fields[1]),'name':(d/'comm').read_text().strip()}
            except (OSError,ValueError): pass
        return rows
    before=snapshot(); start=time.monotonic(); time.sleep(seconds); after=snapshot(); elapsed=time.monotonic()-start
    own={s['pid']}
    candidates=[]
    try: candidates.append(int((RUN/'firefox.pid').read_text()))
    except (OSError,ValueError): pass
    try:
        for line in (RUN/'applications.jsonl').read_text().splitlines():
            entry=json.loads(line)
            if entry.get('session')==s['session']: candidates.append(entry['pid'])
    except (OSError,ValueError,KeyError): pass
    marker=('PRESENTACION_SESSION='+s['session']).encode()
    for pid in candidates:
        try:
            if marker in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'): own.add(pid)
        except OSError: pass
    while True:
        new={pid for pid,r in after.items() if r['ppid'] in own}-own
        if not new: break
        own.update(new)
    rows=sorted([{'pid':pid,'name':r['name'],'cpu':round(100*(r['ticks']-before[pid]['ticks'])/hz/elapsed,1)} for pid,r in after.items() if pid in own and pid in before],key=lambda r:r['cpu'],reverse=True)
    report={'time':datetime.datetime.now().astimezone().isoformat(),'seconds':round(elapsed,2),'logical_cpus':os.cpu_count(),'processes':rows}
    (RUN/'cpu-last.json').write_text(json.dumps(report,indent=2))
    print('CPU por proceso: 100% equivale a un núcleo lógico. Núcleos:',os.cpu_count())
    for r in rows[:15]: print(f"{r['pid']:>8} {r['cpu']:>6.1f}%  {r['name']}")
    total=sum(r['cpu'] for r in rows)
    print(f'Sesión: {total:.1f}% de un núcleo; {total/(os.cpu_count() or 1):.1f}% de la capacidad total.')


def hermes_control(action):
    try:
        current=json.loads(STATE.read_text())
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
            sock.settimeout(2);sock.connect(str(RUN/'hermes.sock'))
            sock.sendall(json.dumps({'action':action,'session':current['session']}).encode()+b'\n')
            data=b''
            while b'\n' not in data:
                part=sock.recv(4096)
                if not part or len(data)+len(part)>8192: raise RuntimeError('Respuesta no válida de Hermes.')
                data+=part
            response=json.loads(data.split(b'\n')[0])
            if not response.get('ok'):raise RuntimeError(response.get('message','Hermes no respondió.'))
            print(response.get('message','Hermes activo; interceptación de capturas habilitada.'))
    except (OSError,ValueError):print('No hay Hermes conectado a las capturas.')


def start_hermes(s):
    if not sys.stdin.isatty() or not sys.stdout.isatty():raise RuntimeError('Ejecuta presentacion hermes en una terminal interactiva.')
    if os.environ.get('DISPLAY')==s['display']:raise RuntimeError('Ejecuta el comando en la terminal exterior desde la que abriste el escritorio virtual.')
    command=json.loads(subprocess.check_output(['hermes','--print-runtime-command'],text=True))
    index=command.index('-c')+1
    marker="runpy.run_module('hermes_cli.main', run_name='__main__', alter_sys=True)"
    if marker not in command[index]:raise RuntimeError('Cambió el lanzador de Hermes; revisa la integración antes de usarla.')
    command[index]=command[index].replace(marker,"runpy.run_path('/opt/presentacion/bin/hermes-bridge.py', run_name='__main__')")
    env=dict(os.environ,HERMES_HOME='/opt/hermes/.hermes')
    os.execvpe(command[0],command,env)


def main():
    require_dev()
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    for cmd in ('iniciar','_sesion'):
        p=sub.add_parser(cmd)
        p.add_argument('--resolucion',default='1280x720')
        p.add_argument('--pantalla-completa',action='store_true')
        p.add_argument('--sin-firefox',action='store_true')
        p.add_argument('--con-firefox',dest='sin_firefox',action='store_false')
        p.set_defaults(sin_firefox=True)
    for cmd in ('estado','cerrar','probar','terminal-privada','registro','hermes','hermes-detener','hermes-estado'): sub.add_parser(cmd)
    p=sub.add_parser('cpu'); p.add_argument('--segundos',type=int,default=5)
    p=sub.add_parser('tamaño',aliases=['tamano']); p.add_argument('resolucion')
    p=sub.add_parser('firefox'); p.add_argument('url',nargs='?')
    p=sub.add_parser('abrir'); p.add_argument('command',nargs=argparse.REMAINDER)
    p=sub.add_parser('captura'); p.add_argument('archivo',nargs='?')
    p=sub.add_parser('captura-host'); p.add_argument('modo',choices=['full','area'],default='full',nargs='?')
    p=sub.add_parser('desinstalar'); p.add_argument('--confirmar',action='store_true'); p.add_argument('--paquetes',action='store_true')
    args=parser.parse_args()
    if args.action in ('iniciar','_sesion'):
        if not re.fullmatch(r'[1-9]\d{2,3}x[1-9]\d{2,3}',args.resolucion): raise RuntimeError('Resolución no válida; ejemplo: 1280x720.')
        if args.action=='_sesion': supervisor(args); return
        if state(False): print('Ya está activo:',state()['display']); return
        RUN.mkdir(parents=True,exist_ok=True,mode=0o700)
        cmd=[sys.executable,str(Path(__file__).resolve()),'_sesion','--resolucion',args.resolucion]
        if args.pantalla_completa: cmd.append('--pantalla-completa')
        if args.sin_firefox: cmd.append('--sin-firefox')
        else: cmd.append('--con-firefox')
        p=spawn(cmd,dict(os.environ),RUN/'session.log')
        for _ in range(150):
            if state(False):
                if not args.pantalla_completa:
                    try: resize(state(),args.resolucion)
                    except (RuntimeError,subprocess.CalledProcessError): pass
                print('Escritorio Awesome listo en la pantalla virtual',state()['display']); return
            if p.poll() is not None: raise RuntimeError('No se pudo iniciar. Usa: presentacion registro')
            time.sleep(.1)
        raise RuntimeError('El inicio sigue en curso. Usa: presentacion estado')
    if args.action=='estado':
        s=state(False); print(json.dumps(s,ensure_ascii=False,indent=2) if s else 'Cerrado.'); return
    if args.action=='cerrar': stop(); return
    if args.action=='registro':
        for f in sorted(RUN.glob('*.log')):
            print('\n'+f.name+'\n'+'\n'.join(f.read_text(errors='replace').splitlines()[-12:]))
        return
    if args.action=='desinstalar':
        if not args.confirmar: raise RuntimeError('Esto elimina el perfil de Firefox de presentación. Usa --confirmar; añade --paquetes para retirar también los paquetes nuevos. Conserva Hermes y Universidad.')
        stop()
        if args.paquetes:
            packages=json.loads((ROOT/'installed-packages.json').read_text())
            remaining=[p for p in packages if subprocess.run(['pacman','-Qq',p],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0]
            if remaining: subprocess.run(['sudo','pacman','-R','--noconfirm',*remaining],check=True)
        subprocess.run(['sudo','rm','--','/usr/local/bin/presentacion'],check=True)
        shutil.rmtree(ROOT)
        print('Presentación eliminada. Hermes y Universidad se conservan.'); return
    if args.action in ('hermes-detener','hermes-estado'):
        hermes_control('stop' if args.action=='hermes-detener' else 'status'); return
    s=state(); env=nested_env(s)
    if args.action=='hermes': start_hermes(s); return
    if args.action=='cpu':
        cpu_report(s,args.segundos); return
    if args.action in ('tamaño','tamano'):
        resize(s,args.resolucion); return
    if args.action=='probar':
        firefox(s,f"http://127.0.0.1:{s['port']}/")
        print('Prueba local abierta en',s['display']); return
    if args.action=='firefox':
        firefox(s,args.url); print('Firefox abierto en',s['display']); return
    if args.action=='abrir':
        command=args.command
        if command and command[0]=='--': command=command[1:]
        if not command: raise RuntimeError('Uso: presentacion abrir COMANDO [argumentos]')
        p=spawn(command,env,RUN/'applications.log')
        with open(RUN/'applications.jsonl','a') as f: f.write(json.dumps({'pid':p.pid,'session':s['session']})+'\n')
        print('Aplicación enviada a',s['display'],'PID',p.pid); return
    if args.action=='captura-host':
        subprocess.run([str(ROOT/'bin/screenshot'),'--host',args.modo],env=dict(os.environ),check=True); return
    if args.action=='captura':
        subprocess.run([str(ROOT/'bin/screenshot'),'full',*([args.archivo] if args.archivo else [])],env=env,check=True); return
    if args.action=='terminal-privada':
        host=dict(os.environ); host['DISPLAY']=s['host_display']
        if s['host_xauthority']: host['XAUTHORITY']=s['host_xauthority']
        subprocess.Popen(['distrobox-host-exec','alacritty','--title','HERMES_PRIVADO','-e','distrobox','enter','dev'],env=host,start_new_session=True)
        print('Terminal privada abierta en el escritorio principal. Ejecuta hermes allí.'); return


if __name__=='__main__':
    try: main()
    except (RuntimeError,OSError,subprocess.CalledProcessError,ValueError) as exc:
        print('Error:',exc,file=sys.stderr); sys.exit(1)
