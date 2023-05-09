import importlib.metadata
VERSION = "Unknown"
try:
    VERSION = importlib.metadata.version("llmchat")
except BaseException as e:
    print("Couldn't get LLMChat version: ", str(e))