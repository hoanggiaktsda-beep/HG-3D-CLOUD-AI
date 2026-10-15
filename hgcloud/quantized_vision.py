"""Optional larger CPU experiment; actual int8 language layers, float vision encoder."""
from .local_vision import LocalCPUVision
from .core import KINDS


class QuantizedCPUVision(LocalCPUVision):
    def __init__(self, model_dir, metadata):
        import torch
        from transformers import AutoModelForVision2Seq, AutoProcessor
        self.torch = torch
        self.metadata = metadata
        self.detector = None
        self.detector_metadata = None
        torch.set_num_threads(4)
        torch.manual_seed(0)
        self.processor = AutoProcessor.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False,
            min_pixels=256 * 28 * 28, max_pixels=512 * 28 * 28)
        self.model = AutoModelForVision2Seq.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.float32,
            low_cpu_mem_usage=True, attn_implementation='eager').eval()
        # Keep the vision encoder and its dtype/device introspection intact.
        # No calibration data, original dimensions, or example responses are used.
        torch.ao.quantization.quantize_dynamic(self.model.model, {torch.nn.Linear},
                                               dtype=torch.qint8, inplace=True)
        self.metadata['quantization'] = 'dynamic int8 language Linear layers; float32 vision and embeddings'

    def generate(self, image, prompt, max_tokens):
        if max_tokens == 320:
            prompt += (f'\nImage coordinate grid: width {image.width}, height {image.height} pixels. '
                       'bbox_px must fit this grid. Allowed kind values: ' + ', '.join(sorted(KINDS)) +
                       '. If the furniture class is unsupported, use box only for its observed envelope; '
                       'name the visible class in project and list unmodeled shape in unknown_details. '
                       'Never claim that an envelope reproduces the full shape.')
        return super().generate(image, prompt, 512 if max_tokens == 320 else max_tokens)
