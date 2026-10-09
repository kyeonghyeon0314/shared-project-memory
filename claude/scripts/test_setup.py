import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

spec=importlib.util.spec_from_file_location('setup_memory',Path(__file__).with_name('setup_memory.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

parser=argparse.ArgumentParser()
parser.add_argument('--fixtures',required=True)
args=parser.parse_args()
fixtures=Path(args.fixtures).resolve()/('shared-memory-check-'+uuid4().hex[:8])
fixtures.mkdir(parents=True)
os.environ['CLAUDE_CONFIG_DIR']=str(fixtures/'isolated-user-config')
root=fixtures/'new project 한글'
root.mkdir()
(root/'AGENTS.md').write_text('Existing agent rule\n',encoding='utf-8')
(root/'CLAUDE.md').write_text('Existing Claude rule\n',encoding='utf-8')
(root/'.claude').mkdir()
(root/'.claude/settings.local.json').write_text(json.dumps({'permissions':{'allow':['Read']},'custom_flag':True}),encoding='utf-8')
before={str(path.relative_to(root)):path.read_bytes() for path in root.rglob('*') if path.is_file()}
module.initialize(root,apply=False)
assert before=={str(path.relative_to(root)):path.read_bytes() for path in root.rglob('*') if path.is_file()},'Dry run changed files'
module.initialize(root,apply=True,approve_main=True)
assert (root/'project-memory/MEMORY.md').is_file(),'Shared index was not created'
assert (root/'AGENTS.md').read_text(encoding='utf-8').startswith('Existing agent rule\n')
assert (root/'CLAUDE.md').read_text(encoding='utf-8').startswith('Existing Claude rule\n')
settings=json.loads((root/'.claude/settings.local.json').read_text(encoding='utf-8'))
assert settings['permissions']=={'allow':['Read']} and settings['custom_flag'] is True
assert Path(settings['autoMemoryDirectory']).resolve()==root/'project-memory'
after={str(path.relative_to(root)):path.read_bytes() for path in root.rglob('*') if path.is_file()}
assert module.initialize(root,apply=True,approve_main=True)['changed']==[]
assert after=={str(path.relative_to(root)):path.read_bytes() for path in root.rglob('*') if path.is_file()},'Re-run altered existing files'
conflict=fixtures/'conflict'
(conflict/'.claude').mkdir(parents=True)
conflict_cfg=conflict/'.claude/settings.local.json'
conflict_cfg.write_text(json.dumps({'autoMemoryDirectory':str(fixtures/'other-memory')}),encoding='utf-8')
original=conflict_cfg.read_bytes()
try:
    module.initialize(conflict,apply=True,approve_main=True)
except RuntimeError:
    assert conflict_cfg.read_bytes()==original and not (conflict/'project-memory').exists()
else:
    raise AssertionError('Conflicting memory directory was overwritten')
bad=fixtures/'malformed'
(bad/'.claude').mkdir(parents=True)
(bad/'.claude/settings.local.json').write_text('{broken',encoding='utf-8')
try:
    module.initialize(bad,apply=True,approve_main=True)
except json.JSONDecodeError:
    assert not (bad/'project-memory').exists()
else:
    raise AssertionError('Invalid config was silently replaced')
repo=fixtures/'main-repo'
repo.mkdir()
subprocess.run(['git','init','-b','main',str(repo)],check=True,capture_output=True)
try:
    module.initialize(repo,apply=True)
except RuntimeError:
    assert not (repo/'project-memory').exists()
else:
    raise AssertionError('Main branch setup lacked the explicit approval flag')
module.initialize(repo,apply=True,approve_main=True)
escaped=fixtures/'outside-link-project'
(escaped/'project-memory').mkdir(parents=True)
outside=fixtures/'outside-destination'
outside.mkdir()
if sys.platform=='win32':
    subprocess.run(['cmd','/c','mklink','/J',str(escaped/'project-memory/archive'),str(outside)],check=True,capture_output=True)
else:
    (escaped/'project-memory/archive').symlink_to(outside,target_is_directory=True)
try:
    module.initialize(escaped,apply=True,approve_main=True)
except RuntimeError:
    assert not (escaped/'AGENTS.md').exists() and list(outside.iterdir())==[]
else:
    raise AssertionError('Outside-root archive link allowed a partial setup')
agents_only=fixtures/'agents-only'
agents_only.mkdir()
(agents_only/'AGENTS.md').write_text('Never run deployment commands.\n',encoding='utf-8')
module.initialize(agents_only,apply=True,approve_main=True)
assert '@AGENTS.md' in (agents_only/'CLAUDE.md').read_text(encoding='utf-8'),'New CLAUDE.md stops loading existing AGENTS rules'
scoped=fixtures/'project-scope-conflict'
(scoped/'.claude').mkdir(parents=True)
(scoped/'.claude/settings.json').write_text(json.dumps({'autoMemoryDirectory':str(fixtures/'project-other')}),encoding='utf-8')
try:
    module.initialize(scoped,apply=True,approve_main=True)
except RuntimeError:
    assert not (scoped/'project-memory').exists() and not (scoped/'.claude/settings.local.json').exists()
else:
    raise AssertionError('Project-scope memory setting silently overridden')
mention=fixtures/'incidental-mention'
mention.mkdir()
(mention/'AGENTS.md').write_text('Example documentation path: project-memory/MEMORY.md\n',encoding='utf-8')
module.initialize(mention,apply=True,approve_main=True)
assert module.MARKER in (mention/'AGENTS.md').read_text(encoding='utf-8'),'Incidental mention suppressed managed adapter'
user_conflict=fixtures/'user-conflict-project'
user_conflict.mkdir()
user_config=fixtures/'isolated-user-config'
user_config.mkdir()
(user_config/'settings.json').write_text(json.dumps({'autoMemoryDirectory':str(fixtures/'user-other-memory')}),encoding='utf-8')
try:
    module.initialize(user_conflict,apply=True,approve_main=True)
except RuntimeError:
    assert not (user_conflict/'project-memory').exists()
else:
    raise AssertionError('User-scope memory setting silently overridden')
os.environ['CLAUDE_CONFIG_DIR']=str(fixtures/'another-empty-user-config')
prohibited=fixtures/'prohibited-guidance'
prohibited.mkdir()
(prohibited/'AGENTS.md').write_text('Do not create project-memory/MEMORY.md automatically.\n',encoding='utf-8')
try:
    module.initialize(prohibited,apply=True,approve_main=True)
except RuntimeError:
    assert not (prohibited/'project-memory').exists()
else:
    raise AssertionError('Contradictory memory rule was ignored')
print(json.dumps({'status':'passed','checks':['dry-run','preserve-instructions-and-permissions','idempotent','conflicting-path-no-mutation','invalid-json-no-mutation','main-approval-gate','outside-link-no-mutation','agents-rule-loading','project-scope-conflict','incidental-mention-adapter','user-scope-conflict','prohibited-guidance'],'fixtures':str(fixtures)},ensure_ascii=False))
