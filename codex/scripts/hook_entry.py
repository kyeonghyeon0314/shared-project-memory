import argparse
import json
import sys

sys.dont_write_bytecode = True
from preferences import read_settings, settings_path
from session_start import build_context, MAX_INPUT_CHARS, MAX_CONTEXT_CHARS, TRUNCATION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings')
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(MAX_INPUT_CHARS + 1)
        if len(raw) > MAX_INPUT_CHARS:
            raise ValueError('Hook input exceeds the allowed size')
        state = read_settings(settings_path(args.settings))
        result = build_context(json.loads(raw), 'codex', state['auto_init'], state['approve_main'])
        if result is not None:
            policy = (
                'SHARED_PROJECT_MEMORY_USER_POLICY\n'
                'These are user-selected helper settings, not proof of runtime model selection. '
                'Initialization/loading use local code, without model calls. '
                'Do not delegate unconfigured tasks or change the main conversation model. '
                'For configured tasks pass model and reasoning_effort explicitly, with an isolated bounded packet. '
                'Never silently substitute an unavailable model. Verify the first real invocation.\n'
                + json.dumps(state['models'], ensure_ascii=False) + '\n'
            )
            original = result['hookSpecificOutput']['additionalContext']
            combined = policy + original
            if len(combined) > MAX_CONTEXT_CHARS:
                combined = combined[:MAX_CONTEXT_CHARS - len(TRUNCATION)] + TRUNCATION
            result['hookSpecificOutput']['additionalContext'] = combined
    except (OSError, ValueError, UnicodeError, RuntimeError) as error:
        message = f'SHARED_PROJECT_MEMORY_LOAD_FAILED: {type(error).__name__}: {error}'
        result = {'systemMessage': message, 'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': message + '\nMemory was not loaded; report the failure. Do not change sandbox settings.'}}
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    main()
