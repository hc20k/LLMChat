# LLMChat
### A Discord chatbot that uses GPT-4 (or 3.5, or 3, or LLaMA) for text generation and ElevenLabs (or Azure TTS) for voice chat.
*Tested with Python 3.9*

**This is actively being improved! Pull requests and issues are very welcome!**

## Features:

- Realistic voice chat support with ElevenLabs and Azure TTS (both require API keys) (Note: the voice chat is only stable if one person is speaking at a time)
- Custom bot identity and name
- Support for all OpenAI text completion and chat completion models
- Support for local LLaMA models
- Local whisper support for speech recognition (as well as Google speech recognition)
- Chat-optimized commands

![Screenshot of messages](assets/repo/message_ss.png)

## How to use:

Install the dependencies:
```bash
pip install -r requirements.txt
```
Rename the `config.example.ini` file to `config.ini` and replace the fields that say `REPLACE ME`

### Possible field values:
`Bot.speech_recognition_service`:
 - `whisper` - run OpenAI's Whisper locally. (Free)
 - `google` - use Google's online transcription service. (Free)

`Bot.tts_service`:
 - `elevenlabs` - use ElevenLabs for TTS. ($) (Further configuration in the `ElevenLabs` section required)
 - `azure` - use Azure cognitive services for TTS. ($) (Further configuration in the `Azure` section required)

`Bot.llm`:
- `openai` - use the OpenAI API for inference. ($) (Further configuration in the `OpenAI` section required)
- `llama` - use a local LLaMA model for inference. (Free) **If you're using this bot for voice chat, LLaMA is not recommended. It is very slow.** (Further configuration in the `LLaMA` section required)

After changing these values, you can run the bot:
```bash
python main.py
```

### Have fun!

## Command reference

- `/print_info` - Prints some info about the bot. (Its name, identity, and model as well as your name and identity)
- `/identity` - Allows you to set the chatbot's name and identity description
- `/your_identity` - Allows you to set your own name and identity (What the chatbot knows about you)
- `/avatar [url]` - Allows you to easily set the chatbot's avatar to a specific URL.
- `/purge` - Deletes all of the messages in the current channel. *DANGEROUS*. I should probably disable this but I use it during testing.
- `/model` - Allows you to change the current model. If you're in OpenAI mode, it will allow you to select from the OpenAI models. If you're in LLaMA mode, it will allow you to select a file from the `LLaMA.search_path` folder.
- `/retry` - Allows you to re-infer the last message, in case you didn't like it.
- `/system [message]` - Allows you to send a message as the `system` role. Only supported for OpenAI models >= gpt-3.5-turbo.
- `/message_context_count` - (default 20) Sets the amount of messages that are sent to the AI for context. Increasing this number will increase the amount of tokens you'll use.