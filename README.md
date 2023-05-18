# LLMChat
### A Discord chatbot that uses GPT-4, 3.5, 3, or LLaMA for text generation and ElevenLabs, Azure TTS, or Silero for voice chat.

**This is actively being improved! Pull requests and issues are very welcome!**

## Features:
    
- Realistic voice chat support with ElevenLabs, Azure TTS, Play.ht, Silero, or Bark models
>NOTE: The voice chat is only stable if one person is speaking at a time
- Image recognition support with BLIP
- Long term message recalling using OpenAI's embeddings to detect similar topics talked about in the past
- Custom bot identity and name
- Support for all OpenAI text completion and chat completion models
- Support for local LLaMA (GGML) models
- Local OpenAI Whisper support for speech recognition (as well as Google and Azure speech recognition)
- Chat-optimized commands

![Screenshot of messages](assets/repo/message_ss.png)

> NOTE: Please only use this on small private servers. Right now it is set up for testing only, meaning anyone on the server can invoke its commands. Also, the bot will join voice chat whenever someone else joins!

## Installation

### Setting up a server

Setup a server to run the bot on, so it can run when your computer is off 24/7. For this guide, I will be using DigitalOcean, but you can use any server host you want. Skip this section if you already have a server or want to run it locally.

1. Create a DigitalOcean account [here](https://cloud.digitalocean.com/registrations/new)

1. Create a droplet
 - [Open your dashboard](https://cloud.digitalocean.com/droplets)
 - Click "Create" -> "Droplets"
 - Select whatever region is closest to you and doesn't have any notes.
 - Choose an image>Ubuntu>Ubuntu 20.04 (LTS) x64
 - Droplet Type>Basic
 - CPU options>Premium Intel (Regular is $1 cheaper but much slower.)
 - 2 GB / 1 Intel CPU / 50 GB Disk / 2 TB Transfer (You need at least 2GB of Ram & 50GB of storage is more than enough storage for this bot.)
 - Choose Authentication Method>Password>Pick a password
 - Enable backups if you want. (This will cost extra but allow you to go back to a previous version of your server if you mess something up.)
 - Create Droplet

2. Connect to your droplet
 - [Open your dashboard](https://cloud.digitalocean.com/droplets)
 - Find your droplet>more>access console
 - Log in as...root>Launch Droplet Console

### Requirements

- At least 2gb of RAM

- ffmpeg
```bash
# Linux:
sudo apt-get install ffmpeg
# For Windows, install from here: https://ffmpeg.org/download.html
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

Simply run 
```bash
pip3.9 install "LLMChat[blip,llama,voice] @ git+https://github.com/hc20k/LLMChat.git"
# Change pip.x if using a different version of Python
```
to install all required dependencies. If you don't want to install any extra features, remove the `blip` (image recognition), `llama` (LLaMA support), and/or `voice` (voice chat support) from the command.

> NOTE: In order to update to the latest commit, run `pip3.9 install "LLMChat[blip,llama,voice] @ git+https://github.com/hc20k/LLMChat.git" --upgrade`

Run:
```bash
mkdir llmchat && cd llmchat # create a directory for the bot
llmchat # run the cli
```
> Skip to [Configuration](#configuration)

### Manual Install

Clone the repo:
```bash
git clone git@github.com:hc20k/LLMChat.git
```

Install from source:
```bash
cd LLMChat
python3.9 setup.py install
```

Run:
```bash
python main.py
# or 
llmchat
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


Create the config file
```bash
llmchat # running the cli will drop the example config file

# or if you're running from source:
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
 - `silero` - uses local [Silero models](https://github.com/snakers4/silero-models) via pytorch. (Free)
 - `play.ht` - uses [Play.ht](https://play.ht/) for TTS. API key needed. ($)
 - `bark` - uses local [Bark](https://github.com/suno-ai/bark) models for TTS. Optimal graphics card needed. (Free)

`audiobook_mode =`
 - `true` - the bot will read its responses to the user from the text chat.
 - `false` - the bot will listen in VC and respond with voice.

`llm = `:
 - `openai` - use OpenAI's API for LLM ($ Fast)
 - `llama` - use a local LLaMA (GGML) model (Free, requires `llama` installation and is slower)

`blip_enabled =`
 - `true` - the bot will recognize images and respond to them (requires `blip` installation)
 - `false` - the bot will not be able to recognize images

### [OpenAI]
`key =`
 - Your [OpenAI API key](https://platform.openai.com/account/api-keys)

`model =`
 - [Desired model](https://platform.openai.com/docs/models)

`reverse_proxy_url = ` *optional*
- Allows you to use a specified reverse proxy.

`use_embeddings =`

[What are embeddings?](https://platform.openai.com/docs/guides/embeddings)
 - `true` - the bot will create embeddings for each message and will be able to recall highly relevant information, ensuring more accurate responses (more expensive)
 - `false` - the bot will NOT create embeddings for each message and will be less likely to recall relevant information (less expensive)

`similarity_threshold = ` *a float ranging from 0 - 1, default 0.83*
- the bot will only use past messages with a relevancy rating above this number. 

`max_similar_messages = ` *an integer, default 5*
- the maximum number of relevant messages that the bot will be reminded of

### [Anthropic]

> **Note:** Anthropic's models are only suited for assistance, meaning they will refuse to impersonate a character.

`key =`
 - Your [Anthropic API key](https://console.anthropic.com/)

`model =`
- Any one of `claude-v1, claude-v1-100k, claude-instant-v1, claude-instant-v1-100k, claude-v1.3, claude-v1.3-100k, claude-v1.2, claude-v1.0,
            claude-instant-v1.1, claude-instant-v1.1-100k, claude-instant-v1.0`

### [Poe] 
> **CAUTION!**
> 
> Poe doesn't work nearly as well as the other supported LLMs. There is no support for editing messages, and the method used for injecting the initial prompt / reminder does not work as well.

`cookie =`
- Your Poe browser token, instructions on how to find that [here](https://github.com/ading2210/poe-api#finding-your-token)

`model = `
- any one of `capybara, beaver, a2_2, a2, chinchilla, nutria`. Use `/list_models` for a list of all usable models.

### [Discord]

`bot_api_key =`
 - The token you generated for the bot in the [Discord Developer Portal](https://discord.com/developers/applications)
`active_channels =`
 - A list of text and voice channel ids the bot should interact with, seperated by commas
 - *Example*: `1090126458803986483,922580158454562851` or `all` (Bot will interact with every channel)

### [Azure], [ElevenLabs], [Silero], [Play.ht]
Supply your API keys & desired voice for the service you chose for `tts_service`

## Starting The Bot:

After changing the configuration files, start the bot
```bash
llmchat
```

Or run the bot in the background using [screen](https://www.gnu.org/software/screen/manual/screen.html) to keep it running after you disconnect from a server.
```bash
screen -S name llmchat
# Press `Ctrl+a` then `d` to detach from the running bot.
```

## Discord commands

### Bot Settings:
- `/configure` - Allows you to set the chatbot's name, identity description, and optional reminder text (a context clue sent further along in the transcript so the AI will consider it more)
- `/model` - Allows you to change the current model. If you're in OpenAI mode, it will allow you to select from the OpenAI models. If you're in LLaMA mode, it will allow you to select a file from the `LLaMA.search_path` folder.
- `/avatar [url]` - Allows you to easily set the chatbot's avatar to a specific URL.
- `/message_context_count` - (default 20) Sets the amount of messages that are sent to the AI for context. Increasing this number will increase the amount of tokens you'll use.
- `/audiobook_mode` - (default `false`) Allows you to change `Bot.audiobook_mode` without manually editing the config.

### Utilities:
- `/reload_config` - Reloads all of the settings in the config.ini.
- `/purge` - Deletes all of the messages in the current channel. *DANGEROUS*. I should probably disable this but I use it during testing.
- `/system [message]` - Allows you to send a message as the `system` role. Only supported for OpenAI models >= gpt-3.5-turbo.
- `/retry` - Allows you to re-infer the last message, in case you didn't like it.

### Info:
- `/print_info` - Prints some info about the bot. (Its name, identity, and model as well as your name and identity)
- `/your_identity` - Allows you to set your own name and identity (What the chatbot knows about you)

## CLI arguments
- `--config-path [path]` - Override the path to config.ini
