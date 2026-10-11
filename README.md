# ai-agents-and-workflows-crash-course
Work based on the ai agents and workflows crash course by Greg Lim

## Setup

From the repo root:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The agents read the OpenAI API key from the macOS Keychain. Store it once
(you'll be prompted for the key):

```
keyring set openai api_key
```

## API key in the Keychain

The key is stored under service `openai`, account `api_key`, and each agent
reads it with:

```python
keyring.get_password("openai", "api_key")
```

Notes:

- Run `keyring set` in a normal terminal. It needs to prompt for input, so it
  fails inside tools that can't take typed input (such as a `!` command in
  Claude Code).
- The first time a script reads the key, macOS may ask whether Python can
  access it. Choose "Always Allow".
- To replace the key, run `keyring set openai api_key` again.
- To remove it, run `keyring del openai api_key`.
- To check it's there without printing it:
  ```
  python -c "import keyring; print(keyring.get_password('openai', 'api_key') is not None)"
  ```
  Avoid `keyring get`, which prints the full key to the terminal.
- You can also see the item in the Keychain Access app (search for `openai`).
- `keyring` uses the system's own store on other platforms too (Windows
  Credential Manager, Secret Service on Linux), so the same commands work
  there.
