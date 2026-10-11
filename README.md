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
- The key lives in your login keychain, not in this repo, so any project on
  your Mac can use it (see below).
- `keyring` uses the system's own store on other platforms too (Windows
  Credential Manager, Secret Service on Linux), so the same commands work
  there.

### Using the key in other projects

In another Python project, add `keyring` to its requirements and read the key
the same way:

```python
keyring.get_password("openai", "api_key")
```

From a shell or a non-Python tool, use the macOS `security` command:

```
security find-generic-password -s openai -a api_key -w
```

`-w` prints the key itself, so use it inside another command rather than on
its own. For example, to give every terminal an `OPENAI_API_KEY` environment
variable (which the OpenAI SDK picks up automatically), add this to
`~/.zshrc`:

```
export OPENAI_API_KEY=$(security find-generic-password -s openai -a api_key -w)
```

macOS controls which programs can read each Keychain item. The first time a
different program reads the key (another Python install or venv, or the
`security` command), macOS may ask for access. Choose "Always Allow" and it
won't ask again for that program.
