import azure.cognitiveservices.speech as speechsdk
import discord
import elevenlabslib as ell
import requests
import whisper
from PIL import Image
from discord import app_commands
from discord.interactions import Interaction

from blip import BLIP
from config import Config

# models
from llm_sources import LLMSource
from llm_sources.llama import LLaMA
from llm_sources.oai import OpenAI
from logger import logger, console_handler, color_formatter
from persistence import PersistentData
from voice_support import BufferAudioSink


class DiscordClient(discord.Client):
    def __init__(self, config: Config):
        self.config = config

        intents = discord.Intents.default()
        intents.message_content = True
        super(DiscordClient, self).__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(
            app_commands.Command(
                name="info",
                description="Prints some information about the bot.",
                callback=self.print_info,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="configure",
                description="Configure the chatbot.",
                callback=self.show_configure,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="your_identity",
                description="Sets your identity.",
                callback=self.set_your_identity,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="avatar",
                description="Sets the chatbot's avatar.",
                callback=self.set_avatar,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="purge",
                description="Deletes all messages in channel. [DANGEROUS!]",
                callback=self.purge_channel,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="model", description="Changes the LLM.", callback=self.set_model
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="retry",
                description="Retries the last message.",
                callback=self.retry_last_message,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="system",
                description="Sends a message as the system role. Only avaliable for >= GPT3.5.",
                callback=self.send_system,
            )
        )
        self.tree.add_command(
            app_commands.Command(
                name="message_context_count",
                description="Sets the message context count. Default is 10.",
                callback=self.set_message_context_count,
            )
        )

        # setup TTS fields
        self.eleven = None
        self.speech_config = None
        self.audio_config = None
        self.speech_synthesizer = None
        self.setup_tts()

        self.llm: LLMSource = None

        if self.config.bot_speech_recognition_service == "whisper":
            logger.info("Loading whisper model...")
            self.whisper: whisper.Whisper = whisper.load_model(
                "base", download_root="models/whisper/"
            )
        else:
            self.whisper = None

        if self.config.bot_blip_enabled:
            self.blip = BLIP()
        else:
            self.blip = None

        self.db: PersistentData = None
        self.sink = None
        self.run(
            self.config.discord_bot_api_key,
            log_handler=console_handler,
            log_formatter=color_formatter,
        )

    def setup_tts(self):
        if self.config.bot_tts_service == "elevenlabs":
            logger.info("Logging into ElevenLabs...")
            self.eleven = ell.ElevenLabsUser(self.config.elevenlabs_key)
        elif self.config.bot_tts_service == "azure":
            logger.info("Logging into Azure...")
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.config.azure_key, region=self.config.azure_region
            )
            self.audio_config = speechsdk.audio.AudioOutputConfig(
                filename="../temp.wav"
            )
            self.speech_config.speech_synthesis_voice_name = self.config.azure_voice
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, audio_config=self.audio_config
            )

    def setup_llm(self):
        logger.info(f"LLM: {self.config.bot_llm}")
        params = [self, self.config, self.db]
        if self.config.bot_llm == "openai":
            self.llm = OpenAI(*params)
        elif self.config.bot_llm == "llama":
            self.llm = LLaMA(*params)
        else:
            logger.critical(f"Unknown LLM: {self.config.bot_llm}")

        logger.info(f"Current model: {self.llm.current_model_name}")

    async def retry_last_message(self, ctx: Interaction):
        history_item = self.db.last
        if not history_item:
            response = await self.llm.generate_response(ctx.user)
            sent_message = await ctx.channel.send(response)
            self.db.append(sent_message)
            await ctx.response.send_message("Done!", delete_after=0.1)
            return

        author_id, content, message_id = history_item
        last_message = await ctx.channel.fetch_message(message_id)

        if author_id != self.user.id:
            # not from me
            response = await self.llm.generate_response(ctx.user)
            sent_message = await ctx.channel.send(response)
            self.db.append(sent_message)
        else:
            await last_message.edit(content="*Retrying...*")
            self.db.remove(last_message.id)
            response = await self.llm.generate_response(ctx.user)
            await last_message.edit(content=response)
            self.db.append(last_message)

        await ctx.response.send_message("Message retried.", delete_after=0.5)

    async def set_message_context_count(self, ctx: Interaction, count: int):
        self.config.llm_context_messages_count = count
        await ctx.response.send_message(
            f"Set message context count to {count}", delete_after=3
        )

    async def set_avatar(self, ctx: Interaction, url: str):
        r = requests.get(url, stream=True)
        await self.user.edit(avatar=r.content)
        await ctx.response.send_message(f"Avatar set!", delete_after=3)

    async def print_info(self, ctx: Interaction):
        name, identity = self.db.get_identity(ctx.user.id)

        embed = discord.Embed(title="LLMChat info")
        embed.add_field(name="LLM source", value=self.config.bot_llm)
        embed.add_field(name="Model", value=self.llm.current_model_name)
        embed.add_field(name="Name", value=self.config.bot_name)
        embed.add_field(name="Description", value=self.config.bot_identity)
        embed.add_field(name="\u200B", value="\u200B",
                        inline=False)  # seperator
        embed.add_field(
            name="Your info (set this information with /your_identity)",
            value="\u200B",
            inline=False,
        )
        embed.add_field(
            name="Name", value=name if name is not None else "*Not set!*")
        embed.add_field(
            name="Description", value=identity if identity is not None else "*Not set!*"
        )

        await ctx.response.send_message(embed=embed)

    async def purge_channel(self, ctx: Interaction):
        await ctx.response.send_message(f"Channel purged!", delete_after=3)
        await ctx.channel.purge()
        self.db.clear()

    async def set_model(self, ctx: Interaction):
        this = self

        class ModelSelect(discord.ui.Select):
            def __init__(self, llm: LLMSource):
                self.llm = llm
                super(ModelSelect, self).__init__(
                    options=[discord.SelectOption(
                        label=m, value=m, default=llm.current_model_name == m) for m in llm.list_models()],
                    placeholder="Select a model...",
                )

            async def callback(self, ctx: Interaction):
                model = ctx.data["values"][0]
                self.llm.set_model(model)
                await this.change_presence(activity=discord.Game(name=model))
                await ctx.response.edit_message(content=f"Model changed to *{self.llm.current_model_name}*", embed=None, delete_after=3)

        select = ModelSelect(self.llm)
        view = discord.ui.View()
        view.add_item(select)

        await ctx.response.send_message("Select a model:", view=view)

    async def send_system(self, ctx: Interaction, message: str):
        if self.config.bot_llm == "openai" and self.llm.use_chat_completion:
            await ctx.response.send_message(f"**System**: {message}")
            self.db.system(message, ctx.id)
        else:
            await ctx.response.send_message(
                "Error: System messages are only supported in OpenAI models, gpt-3.5-turbo and newer.",
                delete_after=5,
            )

    async def set_your_identity(self, ctx: Interaction):
        this = self

        name, desc = self.db.get_identity(ctx.user.id)

        class IdentityModal(discord.ui.Modal):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)

                self.add_item(
                    discord.ui.TextInput(
                        label="Name",
                        custom_id="name",
                        placeholder=ctx.user.display_name,
                        default=name,
                    )
                )
                self.add_item(
                    discord.ui.TextInput(
                        label="Description",
                        placeholder=f"{ctx.user.display_name} is a discord user who doesn't know what to put for their description.",
                        custom_id="description",
                        style=discord.TextStyle.paragraph,
                        default=desc,
                    )
                )

            async def on_submit(self, interaction: Interaction):
                this.db.set_identity(
                    ctx.user.id, self.children[0].value, self.children[1].value
                )
                await interaction.response.send_message("Changes committed.", delete_after=3)

        modal = IdentityModal(title=f"Edit {ctx.user.display_name}'s identity")

        await ctx.response.send_modal(modal)

    async def show_configure(self, ctx: Interaction):
        this = self

        class ConfigureModal(discord.ui.Modal):
            def __init__(self, page=1, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)

                self.add_item(
                    discord.ui.TextInput(
                        label="Name",
                        custom_id="name",
                        placeholder="Jackson",
                        default=this.config.bot_name,
                    )
                )
                self.add_item(
                    discord.ui.TextInput(
                        label="Description",
                        custom_id="description",
                        placeholder="Jackson is a cool bot. He types in all lowercase because he's edgy.",
                        style=discord.TextStyle.paragraph,
                        default=this.config.bot_identity,
                    )
                )
                self.add_item(
                    discord.ui.TextInput(
                        label="Reminder",
                        custom_id="reminder",
                        placeholder="A short context clue to remind the bot to stay in character.",
                        style=discord.TextStyle.paragraph,
                        default=this.config.bot_reminder,
                        required=False,
                    )
                )

            async def on_submit(self, interaction: Interaction):

                this.config.bot_name = self.children[0].value
                await interaction.guild.me.edit(nick=this.config.bot_name)
                this.config.bot_identity = self.children[1].value

                if self.children[2].value:
                    this.config.bot_reminder = self.children[2].value

                await interaction.response.send_message("Changes committed.", delete_after=3)

        modal = ConfigureModal(title="Configure chatbot")

        await ctx.response.send_modal(modal)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        await self.wait_until_ready()
        self.db: PersistentData = PersistentData(self)
        self.setup_llm()
        await self.tree.sync()
        self.event(self.on_voice_state_update)

    async def on_speech(self, speaker_id, speech):
        speaker = discord.utils.get(self.get_all_members(), id=speaker_id)
        self.db.speech(speaker, speech)
        response = await self.llm.generate_response(speaker)
        self.db.speech(self.user, response)

        vc: discord.VoiceClient = self.voice_clients[0]
        vc.stop()

        if self.config.bot_tts_service == "elevenlabs":
            voice = self.eleven.get_voices_by_name(
                self.config.elevenlabs_voice)[0]

            logger.debug("Using voice", voice.get_name())
            data = voice.generate_audio_bytes(response, stability=0.2)
            with open("../temp_out.wav", "wb") as f:
                f.write(data)
                f.close()
        else:
            speech = self.speech_synthesizer.speak_text_async(response).get()
            with open("../temp_out.wav", "wb") as f:
                f.write(speech.audio_data)
                f.close()
        stream = discord.FFmpegPCMAudio("temp_out.wav")

        self.sink.is_speaking = True

        def _after_speaking(_):
            self.sink.is_speaking = False
            logger.debug("Stopped speaking.")

        vc.play(stream, after=_after_speaking)

    async def on_speech_error(self):
        vc: discord.VoiceClient = self.voice_clients[0]
        vc.stop()
        stream = discord.FFmpegPCMAudio("assets/error.wav")
        vc.play(stream)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if after.channel and len(self.voice_clients) == 0:
            vc: discord.VoiceClient = await after.channel.connect()
            self.sink = BufferAudioSink(
                self.on_speech, self.on_speech_error, self.whisper
            )
            vc.listen(self.sink)
        elif member.guild.voice_client:
            if self.sink:
                self.sink.cleanup()
            await member.guild.voice_client.disconnect()

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        self.db.remove(payload.message_id)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        self.db.edit(payload.message_id, payload.data["content"])

    async def on_message(self, message: discord.Message):
        if message.author.id == self.user.id:
            # from me
            return

        if self.config.bot_blip_enabled:
            for a in message.attachments:
                if not a.content_type.startswith("image/"):
                    continue

                # download image
                r = requests.get(a.url, stream=True)
                r.raise_for_status()
                img = Image.open(r.raw).convert("RGB")
                caption = self.blip.process_image(img)
                logger.info(f"Image caption: {caption}")
                message.content += f"\n[{caption}]"

        self.db.append(message)

        async with message.channel.typing():
            try:
                response = await self.llm.generate_response(invoker=message.author)
            except Exception as e:
                await message.channel.send(f"Exception thrown while trying to generate message:\n```{str(e)}```")

                # since it failed remove the message
                self.db.remove(message.id)
                raise e

        logger.debug(f"Response: {response}")
        sent_message = await message.channel.send(response)
        self.db.append(sent_message)
