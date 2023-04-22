from logger import logger
from PIL.Image import Image

class BLIP:
    def __init__(self):
        from transformers import BlipProcessor, BlipForConditionalGeneration
        import torch
        logger.info("Loading BLIP model...")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large", torch_dtype=torch.float16).to(self.device)

    def process_image(self, image: Image):
        inputs = self.processor(image, "Image attached of", return_tensors="pt").to(self.device, torch.float16)
        generated_ids = self.model.generate(**inputs)
        return self.processor.decode(generated_ids[0], skip_special_tokens=True)
