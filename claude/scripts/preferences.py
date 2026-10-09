import json
import os
from pathlib import Path

DEFAULTS = {
    'version': 1,
    'auto_init': False,
    'approve_main': False,
}


def settings_path(value=None):
    if value:
        return Path(value).expanduser().resolve()
    # Fixed path so the hook and a manually run configure.py share one file (CLAUDE_PLUGIN_DATA exists only inside hooks).
    config = Path(os.environ.get('CLAUDE_CONFIG_DIR', str(Path.home() / '.claude')))
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
    return state
