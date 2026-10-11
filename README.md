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
