#!/usr/bin/env python3
"""Render portable payloads; never copy browser state or provider credentials."""
import argparse,datetime,hashlib,json,os,shutil,subprocess
from pathlib import Path

def rendered(data,home):
    try:return data.decode().replace('@HOST_HOME@',str(home)).encode()
    except UnicodeDecodeError:return data

def copy_managed(source,dest,home,backup):
    data=rendered(source.read_bytes(),home)
    if dest.is_file() and dest.read_bytes()==data:return
    if dest.exists():
        saved=backup/dest.relative_to(dest.anchor);saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,saved)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);dest.chmod(source.stat().st_mode & 0o777)

def render_payload(component,target,home,backup):
    for source in (component/'payload').rglob('*'):
        if source.is_file():copy_managed(source,target/source.relative_to(component/'payload'),home,backup)

def merge_settings(data,home):
    data.setdefault('cli',{})['expose_on_path']=False
    data.setdefault('terminal',{})['cwd']=str(home/'Documents/Universidad')
    skills=data.setdefault('skills',{});auto=skills.setdefault('auto_load',[])
    if 'humanize-global' not in auto:auto.append('humanize-global')
    academic=skills.setdefault('config',{}).setdefault('academic_writer',{})
    academic.update(language='es',local_first=True,web_fallback=True,validate_sources=True,humanize=True,autonomous_mode=True,default_word_count=1500,default_export='docx+md',auto_style_samples=True,format_profile='unicaribe',sources_dir=str(home/'Documents/Universidad/entradas'),writing_samples_dir=str(home/'Documents/Universidad/muestras'),output_dir=str(home/'Documents/Universidad/salidas'))
    return data

def configure(args):
    component=args.component.resolve();home=args.home.resolve();target=args.output.resolve()
    backup=target/'backups'/('dotfiles-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    render_payload(component,target,home,backup)
    if args.render_only:return
    if os.environ.get('CONTAINER_ID')!='dev' or target!=Path('/opt/presentacion'):raise SystemExit('Solo se instala dentro de dev en /opt/presentacion.')
    import yaml
    os.umask(0o077)
    for rel in ['run','verification','xdg/config','xdg/data/applications','xdg/cache','xdg/state']:(target/rel).mkdir(parents=True,exist_ok=True)
    for name in ['run','verification']:(target/name).chmod(0o700)
    for sub in ['entradas','salidas/capturas','muestras']:(home/'Documents/Universidad'/sub).mkdir(parents=True,exist_ok=True)
    # Reuse visual assets without changing their originals.
    for source,dest in [(home/'.config/awesome/theme.lua',target/'config/theme.lua'),(home/'.config/polybar/colors.ini',target/'config/polybar/colors.ini'),(home/'.config/alacritty/alacritty.toml',target/'xdg/config/alacritty/alacritty.toml')]:
        if source.is_file():copy_managed(source,dest,home,backup)
    for directory,names in [('config',['zsh','starship.toml','rofi','fastfetch','bat']),('data',['oh-my-zsh','icons'])]:
        sourcebase=home/('.config' if directory=='config' else '.local/share')
        for name in names:
            dest=target/'xdg'/directory/name
            if not dest.exists() and not dest.is_symlink() and (sourcebase/name).exists():dest.symlink_to(sourcebase/name)
    wallpaper=target/'config/wallpaper-path'
    if not wallpaper.exists():
        saved=home/'.local/state/dotfiles/wallpaper'; candidates=[]
        if saved.is_file():candidates.append(Path(saved.read_text().strip()))
        candidates.append(home/'.config/wallpapers/mocha-aurora.png')
        candidates.extend(sorted((home/'Pictures/Wallpapers').rglob('*.png')))
        wallpaper.write_text(str(next((p for p in candidates if p.is_file()),''))+'\n')
    for p in (target/'bin').iterdir():
        if p.is_file():p.chmod(0o755)
    manifest=target/'installed-packages.json';owned=set(json.loads(manifest.read_text())) if manifest.exists() else set()
    if args.packages_before:
        before=set(args.packages_before.read_text().splitlines());after=set(subprocess.check_output(['pacman','-Qq'],text=True).splitlines());owned.update(after-before)
    manifest.write_text(json.dumps(sorted(owned),indent=2)+'\n')
    hermes=Path('/opt/hermes/.hermes');hermes.mkdir(parents=True,exist_ok=True)
    for source in (component/'skills').rglob('*'):
        if source.is_file():copy_managed(source,hermes/'skills'/source.relative_to(component/'skills'),home,backup)
    for rel in ['academic','skill-bundles']:(hermes/rel).mkdir(exist_ok=True)
    for name,sub in [('sources','entradas'),('output','salidas'),('writing_samples','muestras')]:
        p=hermes/'academic'/name
        if not p.exists() and not p.is_symlink():p.symlink_to(home/'Documents/Universidad'/sub)
    copy_managed(component/'academico.yaml',hermes/'skill-bundles/academico.yaml',home,backup)
    cfg=hermes/'config.yaml';data=yaml.safe_load(cfg.read_text()) if cfg.exists() else {}
    data=data or {}
    # Merge only the declared personal settings. Never read/copy .env/auth.json.
    data=merge_settings(data,home)
    encoded=yaml.safe_dump(data,allow_unicode=True,sort_keys=False)
    if not cfg.exists() or cfg.read_text()!=encoded:
        if cfg.exists():
            saved=backup/'hermes-config.yaml';saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(cfg,saved)
        cfg.write_text(encoded);cfg.chmod(0o600)
    (target/'dotfiles-component.json').write_text(json.dumps({'component':'hermes','layout':1},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--component',type=Path,default=Path(__file__).parent);p.add_argument('--output',type=Path,default=Path('/opt/presentacion'));p.add_argument('--home',type=Path,default=Path.home());p.add_argument('--packages-before',type=Path);p.add_argument('--render-only',action='store_true');args=p.parse_args()
    if not args.render_only and (os.environ.get('CONTAINER_ID')!='dev' or args.output.resolve()!=Path('/opt/presentacion')):p.error('La instalación real requiere dev y /opt/presentacion.')
    configure(args)
