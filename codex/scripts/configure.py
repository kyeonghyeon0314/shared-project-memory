import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from uuid import uuid4

sys.dont_write_bytecode = True
from preferences import read_settings, settings_path


def main():
    parser = argparse.ArgumentParser(description='Preview or apply one user preference file. No project writes, installs, API calls, or hook trust changes.')
    parser.add_argument('--settings')
    parser.add_argument('--apply', action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--enable-auto-init', action='store_true')
    group.add_argument('--disable-auto-init', action='store_true')
    parser.add_argument('--approve-main', action='store_true')
    parser.add_argument('--summary-model')
    parser.add_argument('--summary-effort')
    parser.add_argument('--extract-model')
    parser.add_argument('--extract-effort')
    args = parser.parse_args()
    target = settings_path(args.settings)
    before = target.read_bytes() if target.exists() else None
    state = read_settings(target)
    if args.enable_auto_init:
        state['auto_init'] = True
    if args.disable_auto_init:
        state['auto_init'] = False
    if args.approve_main:
        state['approve_main'] = True
    for task, model, effort in (
        ('summarization', args.summary_model, args.summary_effort),
        ('extraction', args.extract_model, args.extract_effort),
    ):
        if model is not None or effort is not None:
            if model is None or effort is None:
                parser.error(f'{task}: provide both model and effort')
            state['models'][task] = {'model': model, 'effort': effort}
    # Validate the proposed state without writing it.
    from preferences import MODEL_ID, EFFORTS
    for task, mapping in state['models'].items():
        model, effort = mapping.get('model'), mapping.get('effort')
        if model is not None and (not isinstance(model, str) or not MODEL_ID.fullmatch(model) or not isinstance(effort, str) or effort not in EFFORTS):
            parser.error(f'Invalid model/effort pair for {task}')
    desired = (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    changed = before != desired
    if args.apply and changed:
        target.parent.mkdir(parents=True, exist_ok=True)
        current = target.read_bytes() if target.exists() else None
        if current != before:
            raise RuntimeError('Preferences changed during preview; refusing overwrite')
        if before is not None:
            backup = target.with_name(target.name + '.backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:8])
            backup.write_bytes(before)
        with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent, prefix=target.name + '.', delete=False) as temp:
            temp.write(desired)
            temporary = temp.name
        os.replace(temporary, target)
    print(json.dumps({'settings': str(target), 'applied': args.apply, 'changed': changed, 'preferences': state}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
