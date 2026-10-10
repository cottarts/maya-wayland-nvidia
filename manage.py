#!/usr/bin/env python3
"""Install/remove the Maya startup hook without replacing unrelated user settings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
FILES = ('arnold_qt_canvas_auto.py', 'arnold_qt_canvas_impl.py')
MANIFEST = '.arnold-qt-canvas-install.json'
HOOK = ('\n# BEGIN Arnold Qt canvas\n'
        'import maya.utils as _arnold_qt_maya_utils\n'
        '_arnold_qt_maya_utils.executeDeferred("import arnold_qt_canvas_auto; arnold_qt_canvas_auto.start()")\n'
        '# END Arnold Qt canvas\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def install(folder):
    manifest = folder / MANIFEST
    if manifest.exists():
        print('Already installed. Uninstall before updating.'); return
    setup = folder / 'userSetup.py'
    data = setup.read_bytes() if setup.exists() else b''
    if b'# BEGIN Arnold Qt canvas' in data:
        raise ValueError('An existing Arnold Qt hook is present. Remove the previous installation first.')
    # Preflight: validate all Python before touching the target directory.
    for name in FILES:
        compile((ROOT / 'maya' / name).read_bytes(), name, 'exec')
    compile(data + HOOK.encode(), str(setup), 'exec')
    folder.mkdir(parents=True, exist_ok=True)
    backup = folder / ('.arnold-qt-backup-' + uuid.uuid4().hex)
    backup.mkdir()
    state = {'version': 1, 'backup': backup.name, 'setup_existed': setup.exists(), 'files': {}}
    if setup.exists(): shutil.copy2(setup, backup / 'userSetup.py')
    for name in FILES:
        target = folder / name
        existed = target.exists()
        if existed: shutil.copy2(target, backup / name)
        shutil.copy2(ROOT / 'maya' / name, target)
        state['files'][name] = {'existed': existed, 'sha256': digest(target)}
    setup.write_bytes(data + HOOK.encode())
    manifest.write_text(json.dumps(state, indent=2) + '\n')
    print('Installed in', folder)
    print('Backup:', backup)
    print('Restart Maya, then open Arnold RenderView.')

def uninstall(folder):
    manifest = folder / MANIFEST
    if not manifest.exists(): raise ValueError('No installation manifest. No files were removed.')
    state = json.loads(manifest.read_text())
    backup = folder / state['backup']
    if backup.parent != folder or not backup.name.startswith('.arnold-qt-backup-'):
        raise ValueError('Invalid backup path.')
    # Refuse to discard edits made since installation.
    for name in FILES:
        target = folder / name
        if target.exists() and digest(target) != state['files'][name]['sha256']:
            raise ValueError('Modified module: ' + str(target) + '. Save/reconcile your edits first.')
        if state['files'][name]['existed'] and not (backup / name).exists():
            raise ValueError('Missing backup for ' + name)
    setup = folder / 'userSetup.py'
    data = setup.read_bytes() if setup.exists() else b''
    if b'# BEGIN Arnold Qt canvas' in data and HOOK.encode() not in data:
        raise ValueError('Startup hook was modified. No files were removed.')
    for name in FILES:
        target = folder / name
        if state['files'][name]['existed']: shutil.copy2(backup / name, target)
        elif target.exists(): target.unlink()
    cleaned = data.replace(HOOK.encode(), b'', 1)
    if cleaned or state['setup_existed']: setup.write_bytes(cleaned)
    elif setup.exists(): setup.unlink()
    manifest.unlink()
    print('Uninstalled. Other startup changes preserved. Backup retained:', backup)
    print('Restart Maya to restore its original canvas.')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('install', 'uninstall'))
    p.add_argument('--maya-version', default='2026')
    p.add_argument('--scripts-dir', type=Path, help='Override Maya user scripts directory')
    args = p.parse_args()
    if not re.fullmatch(r'\d{4}', args.maya_version): p.error('Expected a four-digit Maya year')
    folder = (args.scripts_dir or Path.home() / 'maya' / args.maya_version / 'scripts').expanduser().resolve()
    try: {'install': install, 'uninstall': uninstall}[args.action](folder)
    except (ValueError, OSError, SyntaxError) as exc:
        print('Error:', exc, file=sys.stderr); return 1
    return 0

if __name__ == '__main__': sys.exit(main())
