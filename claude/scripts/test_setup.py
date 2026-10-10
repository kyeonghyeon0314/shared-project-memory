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
(root/'.claude/settings.local.json').write_text(json.dumps({'permissions':{'allow':['Read']},'custom_flag':True,'env':{'SPM_TEST_TOKEN':'local-secret-marker'}}),encoding='utf-8')
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
memory_files=[path for path in (root/'project-memory').rglob('*') if path.is_file()]
assert not any(b'local-secret-marker' in path.read_bytes() for path in memory_files),'Local settings were copied into shared memory'
local_backups=list((fixtures/'isolated-user-config/shared-project-memory/backups').rglob('settings.local.json'))
assert local_backups and b'local-secret-marker' in local_backups[0].read_bytes(),'Local settings backup missing from user config'
if os.name!='nt':
    assert local_backups[0].stat().st_mode&0o777==0o600,'Local settings backup is readable by other users'
    assert local_backups[0].parent.parent.stat().st_mode&0o777==0o700,'Local backup folder is accessible to other users'
ignored=(root/'project-memory/.gitignore').read_text(encoding='utf-8').splitlines()
assert 'archive/' in ignored and '.setup-complete.json' in ignored,'Local-only memory files are not git-ignored'
for shared in ('CLAUDE.md','AGENTS.md','project-memory/MEMORY.md','project-memory/current.md'):
    assert root.as_posix() not in (root/shared).read_text(encoding='utf-8') and str(root) not in (root/shared).read_text(encoding='utf-8'),f'Absolute machine path written to shared file {shared}'
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
user_config.mkdir(exist_ok=True)
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
def git(repo,*arguments):
    return subprocess.run(['git','-C',str(repo),'-c','user.name=spm-test','-c','user.email=spm-test@example.invalid',*arguments],check=True,capture_output=True,text=True)
os.environ['CLAUDE_CONFIG_DIR']=str(fixtures/'gitignore-user-config')
existing=fixtures/'existing-gitignore'
(existing/'project-memory').mkdir(parents=True)
git(fixtures,'init','-q','-b','work',str(existing))
(existing/'project-memory/.gitignore').write_text('notes.tmp',encoding='utf-8')
result=module.initialize(existing,apply=True)
lines=(existing/'project-memory/.gitignore').read_text(encoding='utf-8').splitlines()
assert lines[0]=='notes.tmp' and 'archive/' in lines and '.setup-complete.json' in lines,'Existing .gitignore was replaced or not completed'
assert result['git_exposure']=={'git':True,'local_copies_verified_ignored':True,'tracked_local_files':[]},result['git_exposure']
git(existing,'check-ignore','-q','project-memory/archive/setup-backup-x/AGENTS.md')
git(existing,'check-ignore','-q','project-memory/.setup-complete.json')
git(existing,'add','-A')
assert not [name for name in git(existing,'ls-files').stdout.splitlines() if name.startswith('project-memory/archive/') or name.endswith('.setup-complete.json')],'Local-only files were staged'
assert module.initialize(existing,apply=True)['changed']==[],'Completed .gitignore changed on re-run'
tracked=fixtures/'tracked-archive'
(tracked/'project-memory/archive').mkdir(parents=True)
git(fixtures,'init','-q','-b','work',str(tracked))
(tracked/'project-memory/archive/old-backup.json').write_text('{}',encoding='utf-8')
git(tracked,'add','-A')
git(tracked,'commit','-q','-m','pre-existing tracked backup')
exposure=module.initialize(tracked,apply=True)['git_exposure']
assert exposure['local_copies_verified_ignored'] is True and exposure['tracked_local_files']==['project-memory/archive/old-backup.json'],exposure
negations={
    'whole-folder':'archive/\n!archive/\n.setup-complete.json\n',
    'single-backup-file':'archive/\n!archive/\narchive/*\n!archive/setup-backup-*/\narchive/setup-backup-*/*\n!archive/setup-backup-*/AGENTS.md\n.setup-complete.json\n',
}
for label,rules in negations.items():
    negated=fixtures/('negation-'+label)
    (negated/'project-memory').mkdir(parents=True)
    git(fixtures,'init','-q','-b','work',str(negated))
    (negated/'AGENTS.md').write_text('Existing rule\n',encoding='utf-8')
    (negated/'project-memory/.gitignore').write_text(rules,encoding='utf-8')
    if label=='single-backup-file':
        git(negated,'check-ignore','-q','project-memory/archive/.probe')
        assert subprocess.run(['git','-C',str(negated),'check-ignore','-q','project-memory/archive/setup-backup-x/AGENTS.md']).returncode==1,'Fixture does not re-include the backup file'
    result=module.initialize(negated,apply=True)
    assert result['git_exposure']['local_copies_verified_ignored'] is True,result
    assert (negated/'project-memory/.gitignore').read_text(encoding='utf-8').startswith(rules),f'{label}: existing rules not preserved'
    backups=[path.relative_to(negated).as_posix() for path in (negated/'project-memory/archive').rglob('*') if path.is_file()]
    assert any(name.endswith('/AGENTS.md') for name in backups),backups
    for name in backups:
        git(negated,'check-ignore','-q',name)
    git(negated,'add','-A')
    staged=git(negated,'ls-files').stdout.splitlines()
    assert not [name for name in staged if '/archive/' in name or name.endswith('.setup-complete.json')],f'{label}: local-only copy staged {staged}'
    assert module.initialize(negated,apply=True)['changed']==[],f'{label}: repaired .gitignore changed on re-run'
refused=fixtures/'ignore-verification-fails'
(refused/'project-memory').mkdir(parents=True)
git(fixtures,'init','-q','-b','work',str(refused))
(refused/'AGENTS.md').write_text('Existing rule\n',encoding='utf-8')
(refused/'project-memory/.gitignore').write_text('notes.tmp\n',encoding='utf-8')
snapshot={str(path.relative_to(refused)):path.read_bytes() for path in refused.rglob('*') if path.is_file() and '.git' not in path.relative_to(refused).parts}
real_git_ignored=module.git_ignored
module.git_ignored=lambda root,paths:set()
try:
    module.initialize(refused,apply=True)
except RuntimeError as error:
    assert 'nothing was written' in str(error),error
    assert snapshot=={str(path.relative_to(refused)):path.read_bytes() for path in refused.rglob('*') if path.is_file() and '.git' not in path.relative_to(refused).parts},'Files changed although ignore verification failed'
    assert not (refused/'project-memory/archive').exists()
else:
    raise AssertionError('Setup wrote local-only copies Git would not ignore')
fresh=fixtures/'ignore-verification-fails-fresh'
git(fixtures,'init','-q','-b','work',str(fresh))
(fresh/'AGENTS.md').write_text('Existing rule\n',encoding='utf-8')
try:
    module.initialize(fresh,apply=True)
except RuntimeError:
    assert not (fresh/'project-memory').exists() and (fresh/'AGENTS.md').read_text(encoding='utf-8')=='Existing rule\n','Refused setup left project-memory behind'
else:
    raise AssertionError('Fresh project setup ignored failed verification')
finally:
    module.git_ignored=real_git_ignored
inside=fixtures/'config-inside-project'
(inside/'.claude').mkdir(parents=True)
(inside/'.claude/settings.local.json').write_text('{"env":{"SPM_TEST_TOKEN":"x"}}',encoding='utf-8')
for label,config in (('direct',inside/'.claude-config'),('linked',fixtures/'linked-config')):
    if label=='linked':
        if sys.platform=='win32':
            subprocess.run(['cmd','/c','mklink','/J',str(config),str(inside/'linked-target')],check=True,capture_output=True)
        else:
            (inside/'linked-target').mkdir()
            config.symlink_to(inside/'linked-target',target_is_directory=True)
    os.environ['CLAUDE_CONFIG_DIR']=str(config)
    snapshot={str(path.relative_to(inside)):path.read_bytes() for path in inside.rglob('*') if path.is_file()}
    try:
        module.initialize(inside,apply=True)
    except RuntimeError as error:
        assert 'inside the project' in str(error),error
        assert snapshot=={str(path.relative_to(inside)):path.read_bytes() for path in inside.rglob('*') if path.is_file()},f'{label}: files changed before refusal'
    else:
        raise AssertionError(f'{label}: local settings backup was allowed inside the project')
print(json.dumps({'status':'passed','checks':['dry-run','preserve-instructions-and-permissions','idempotent','conflicting-path-no-mutation','invalid-json-no-mutation','main-approval-gate','outside-link-no-mutation','agents-rule-loading','project-scope-conflict','incidental-mention-adapter','user-scope-conflict','prohibited-guidance','local-backup-outside-project','local-only-gitignore','no-absolute-shared-paths','private-local-backup','existing-gitignore-completed','git-check-ignore-verified','tracked-local-file-reported','config-dir-inside-project-refused','linked-config-dir-refused','negated-folder-repaired','negated-backup-file-repaired','unverified-ignore-aborts-before-copies'],'fixtures':str(fixtures)},ensure_ascii=False))
