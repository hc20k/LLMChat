import logging

log_level = logging.DEBUG

logger = logging.getLogger("GPTEleven")
logger.setLevel(log_level)
color_formatter = logging.Formatter(
    "[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    "%m-%d %H:%M:%S",
)
reg_formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
)

file_handler = logging.FileHandler("debug.log")
file_handler.setLevel(log_level)
file_handler.setFormatter(reg_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(color_formatter)

if not logger.handlers:
    # add the file handler to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
