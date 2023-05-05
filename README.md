# LLMChat
### A Discord chatbot that uses GPT-4, 3.5, 3, or LLaMA for text generation and ElevenLabs, Azure TTS, or Silero for voice chat.

**This is actively being improved! Pull requests and issues are very welcome!**

## Features:
    
- Realistic voice chat support with ElevenLabs, Azure TTS, Play.ht, Silero, or Bark models (NOTE: the voice chat is only stable if one person is speaking at a time)
- Long term message recalling using OpenAI's embeddings to detect similar topics talked about in the past
- Custom bot identity and name
- Support for all OpenAI text completion and chat completion models
- Support for local LLaMA models
- Local OpenAI Whisper support for speech recognition (as well as Google and Azure speech recognition)
- Chat-optimized commands
- Image recognition support with BLIP

![Screenshot of messages](assets/repo/message_ss.png)

> NOTE: Please only use this on small private servers. Right now it is set up for testing only, meaning anyone on the server can invoke its commands. Also, the bot will join voice chat whenever someone else joins!

## Installation

### Requirements

- At least 2gb of RAM

- ffmpeg
```bash
sudo apt-get install ffmpeg
```

- Dev version of Python
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.9-dev
```
> Tested on Python 3.9 but may work with other versions

- Pip
```bash
sudo apt-get install python3-pip
```

- PortAudio

```bash
sudo apt-get install portaudio19-dev
```

### Automatically Install Dependencies

Clone the project files and cd into the directory
```bash
git clone https://github.com/hc20k/LLMChat.git
cd LLMChat
```

Simply run 
```bash
python3.9 update.py -y
# -y installs required dependencies without user interaction
# Change python.x if using a different version of Python
```
to install all required dependencies. You will be asked if you want to install the optional dependencies for voice and/or image recognition in the script.

> NOTE: It's healthy to run `update.py` after a new commit is made, because requirements may be added.

### Manually Install Dependencies

If you were having trouble with the `update.py` script, you can install the dependencies manually using these commands.

Clone the project files and cd into the directory
```bash
git clone https://github.com/hc20k/LLMChat.git
cd LLMChat
```

Manually install the dependencies
```bash
pip install -r requirements.txt

# for voice support (ElevenLabs, bark, Azure, whisper)
pip install -r optional/voice-requirements.txt

# for BLIP support
pip install -r optional/blip-requirements.txt
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# for LLaMA support
pip install -r optional/llama-requirements.txt
```

## Configuration

Create the bot:
  
- Visit [Discord Developer Portal](https://discord.com/developers/applications)
  - Applications -> New Application  
- Generate Token for the app (discord_bot_token)  
  - Select App (Bot) -> Bot -> Reset Token (Save this token for later)
- Select App (Bot) -> Bot -> and turn on all intents
- Add Bot to server(s)  
  - Select App (Bot) -> OAuth2 -> URL Generator -> Select Scope: Bot, applications.commands  
  - Select Permissions: Administrator
  > NOTE: Administrator is required for the bot to work properly. If you want to use the bot without Administrator permissions, you can manually select the permissions you want to give the bot.
  - Open the generated link and add the bot to your desired server(s)


Copy the config file
```bash
cp config.example.ini config.ini
```

Edit the config file
```bash
nano config.ini
```

### [Bot]
`speech_recognition_service =`:
 - `whisper` - run OpenAI's Whisper locally. (Free)
 - `google` - use Google's online transcription service. (Free)
 - `azure` - use Microsoft Azure's online transcription service. ($)

`tts_service =`:
 - `elevenlabs` - use ElevenLabs for TTS. ($) (Further configuration in the `ElevenLabs` section required)
 - `azure` - use Azure cognitive services for TTS. ($) (Further configuration in the `Azure` section required)
 - `silero` - uses local [Silero models]

`audiobook_mode =`
 - `true` - the bot will read its responses to the user from the text chat.
 - `false` - the bot will listen in VC and respond with voice.

`llm = `:
 - `openai` - use OpenAI's API for LLM ($ Fast))
 - `llama` - use a local LLaMA model (Free, requires llama installation and is slower)

`blip_enabled =`
 - true - the bot will recognize images and respond to them (requires BLIP, installed from update.py)
 - false - the bot will not be able to recognize images

### [OpenAI]
`key =`
 - Your [OpenAI API key](https://platform.openai.com/account/api-keys)
`model =`
 - [Desired model](https://platform.openai.com/docs/models)
`use_embeddings =`
    - true - the bot will log and remember past messages and use them to generate more realistic responses (more expensive)
    - false - the bot will not log past messages and will generate responses based on the past few messages only (less expensive)

### [Discord]

`bot_api_key =`
 - The token you generated for the bot in the [Discord Developer Portal](https://discord.com/developers/applications)
`active_channels =`
 - A list of text and voice channel ids the bot should interact with, seperated by commas
 - *Example*: `1090126458803986483,922580158454562851` or `all` (Bot will interact with every channel)

### [Azure], [ElevenLabs], [Silero], [Play.ht]
Supply your API keys for the service you chose for `tts_service`.

## Starting The Bot:

After changing the configuration files, start the bot
```bash
python3.9 main.py
```

Or run the bot in the background useing [screen](https://www.gnu.org/software/screen/manual/screen.html) to keep it running after you disconnect from a server.
```bash
screen -S name python3.9 main.py
# Press `Ctrl+a` then `d` to detach from the running bot.
```

## Discord Commands

### Bot Settings:
- `/model` - Allows you to change the current model. If you're in OpenAI mode, it will allow you to select from the OpenAI models. If you're in LLaMA mode, it will allow you to select a file from the `LLaMA.search_path` folder.
- `/avatar [url]` - Allows you to easily set the chatbot's avatar to a specific URL.
- `/message_context_count` - (default 20) Sets the amount of messages that are sent to the AI for context. Increasing this number will increase the amount of tokens you'll use.
- `/configure` - Allows you to set the chatbot's name, identity description, and optional reminder text (a context clue sent further along in the transcript so the AI will consider it more)

### Utilties:
- `/reload_config` - Reloads all of the settings in the config.ini.
- `/purge` - Deletes all of the messages in the current channel. *DANGEROUS*. I should probably disable this but I use it during testing.
- `/system [message]` - Allows you to send a message as the `system` role. Only supported for OpenAI models >= gpt-3.5-turbo.
- `/retry` - Allows you to re-infer the last message, in case you didn't like it.

### Info:
- `/print_info` - Prints some info about the bot. (Its name, identity, and model as well as your name and identity)
- `/your_identity` - Allows you to set your own name and identity (What the chatbot knows about you)