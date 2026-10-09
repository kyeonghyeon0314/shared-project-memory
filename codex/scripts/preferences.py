import json
import os
import re
from pathlib import Path

DEFAULTS = {
    'version': 1,
    'auto_init': False,
    'approve_main': False,
    'models': {
        'summarization': {'model': None, 'effort': None},
        'extraction': {'model': None, 'effort': None},
    },
}
EFFORTS = {'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'}
MODEL_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}')


def settings_path(value=None):
    if value:
        return Path(value).expanduser().resolve()
    config = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    return (config / 'shared-project-memory/settings.json').resolve()


def read_settings(path):
    state = json.loads(json.dumps(DEFAULTS))
    if path.exists():
        saved = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(saved, dict):
            raise ValueError('Settings must be a JSON object')
        state.update(saved)
    if type(state.get('version')) is not int or state['version'] != 1:
        raise ValueError('Unsupported preferences version')
    for name in ('auto_init', 'approve_main'):
        if type(state.get(name)) is not bool:
            raise ValueError(f'{name} must be a boolean')
    models = state.get('models')
    if not isinstance(models, dict):
        raise ValueError('models must be an object')
    for task in ('summarization', 'extraction'):
        mapping = models.get(task)
        if not isinstance(mapping, dict):
            raise ValueError(f'Missing model mapping for {task}')
        model, effort = mapping.get('model'), mapping.get('effort')
        if model is None and effort is None:
            continue
        if not isinstance(model, str) or not MODEL_ID.fullmatch(model) or not isinstance(effort, str) or effort not in EFFORTS:
            raise ValueError(f'{task} requires an explicit valid model and effort pair')
    return state
