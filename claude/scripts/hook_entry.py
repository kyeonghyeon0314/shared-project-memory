import argparse
import json
import sys

sys.dont_write_bytecode = True
from preferences import read_settings, settings_path
from session_start import build_context, MAX_INPUT_CHARS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings')
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(MAX_INPUT_CHARS + 1)
        if len(raw) > MAX_INPUT_CHARS:
            raise ValueError('Hook input exceeds the allowed size')
        state = read_settings(settings_path(args.settings))
        policy = (
            'SHARED_PROJECT_MEMORY_USER_POLICY\n'
            'Initialization/loading use local code, without model calls. Do not change the main conversation model. '
            'Optional helpers: summarization -> shared-project-memory:memory-summarizer; '
            'simple extraction -> shared-project-memory:simple-extractor. '
            'Call them by these full names, omit the model argument so the agent file selects the model, '
            'and pass an isolated bounded evidence packet. Do not use same-named user agents for these tasks. '
            'Never silently substitute an unavailable model. Verify the first real invocation from execution metadata.\n'
        )
        # Policy and memory share one budget; build_context truncates once.
        result = build_context(json.loads(raw), 'claude', state['auto_init'], state['approve_main'], preamble=policy)
    except (OSError, ValueError, UnicodeError, RuntimeError) as error:
        message = f'SHARED_PROJECT_MEMORY_LOAD_FAILED: {type(error).__name__}: {error}'
        result = {'systemMessage': message, 'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': message + '\nMemory was not loaded; report the failure. Do not change sandbox settings.'}}
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    main()
