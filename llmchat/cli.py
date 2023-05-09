import argparse
import llmchat
from llmchat.config import Config
from llmchat.client import DiscordClient
from llmchat.logger import logger
import os


def main():
    logger.info(f"LLMChat v{llmchat.VERSION}")
    parser = argparse.ArgumentParser(description="An advanced, fully featured Discord chat bot. Created by @hc20k")
    parser.add_argument("--config-path", default="config.ini", help="Overrides the path to config.ini.", required=False)
    args = parser.parse_args()

    if not os.path.exists(args.config_path):
        logger.fatal(f"Config not found @ {args.config_path}. Copying example config to this path, please follow the instructions in the README.md to properly configure it.")

        if os.path.exists("config.example.ini"):
            import shutil
            shutil.copy("config.example.ini", args.config_path)
        else:
            import importlib.resources as pkg_resources
            example = pkg_resources.read_text(llmchat, "config.example.ini")
            with open(args.config_path, 'w') as f:
                f.write(example)

        return

    config = Config(args.config_path)
    client = DiscordClient(config)

