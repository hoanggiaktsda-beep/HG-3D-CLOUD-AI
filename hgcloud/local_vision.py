"""Real local CPU VLM inference; model proposals never certify dimensions."""
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .core import SceneError
from .vision import PROMPT, ROLES, normalize_response

GEOMETRY_PROMPT = PROMPT + '''
Output exactly one JSON object, no markdown. Required top-level fields: project
(string), objects (array), missing_information (array). Required object fields:
id, kind, center_mm (three numbers), placement_evidence, unknown_details,
dimensions (x, y, z). Required dimension fields: value_mm (number or null),
confidence, basis, bbox_px (pixel evidence rectangle or null), source_note.
No known scale means null dimensions. Do not invent a generic example object.
'''


def parse_proposal(text, source_hash, pixels):
    """Fail closed; all model-supplied geometry requires independent review."""
    if len(text) > 100_000:
        raise SceneError('Model response exceeds limit')
    stripped = text.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r'^```(?:json)?\s*|\s*```$', '', stripped)
    try:
        response = json.loads(stripped)
    except (ValueError, TypeError) as exc:
        raise SceneError('Model did not return valid geometry JSON') from exc
    result = normalize_response(response, source_hash, 'local_cpu_vlm')
    seen = set()
    grounded_metric_evidence = False
    for obj in result['objects']:
        ident = obj.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', ident) or ident in seen:
            raise SceneError('Invalid or duplicate proposed object id')
        seen.add(ident)
        if set(obj['dimensions']) != set('xyz'):
            raise SceneError('All three axes must be explicit; unknown axes must be null')
        if not all(isinstance(value, str) for value in obj['unknown_details']):
            raise SceneError('Unknown details must be text')
        for item in obj['dimensions'].values():
            value = item.get('value_mm')
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 100_000):
                raise SceneError('Invalid proposed dimension')
            bbox = item.get('bbox_px')
            if bbox is not None and not (isinstance(bbox, list) and len(bbox) == 4
                    and all(type(v) in (int, float) and math.isfinite(v) for v in bbox)
                    and 0 <= bbox[0] < bbox[2] <= pixels[0] and 0 <= bbox[1] < bbox[3] <= pixels[1]):
                raise SceneError('Invalid image evidence region')
            item['confidence'] = 'needs_confirmation'
            item['basis'] = 'model_proposal'
            item.pop('verified_by', None)
            if not isinstance(item.get('source_note'), str) or not item['source_note'].strip():
                raise SceneError('Missing image evidence note')
            if value is not None and bbox is not None:
                grounded_metric_evidence = True
        obj['placement_evidence']['confidence'] = 'needs_confirmation'
        if not obj['placement_evidence'].get('source_note'):
            raise SceneError('Missing placement evidence note')
    if not grounded_metric_evidence:
        raise SceneError('No grounded metric evidence; empty/template objects are not a 3D proposal')
    # A parsed response alone is NOT proof that model inference occurred.
    result['vision_provenance']['live_model_executed'] = False
    result['vision_provenance']['validation'] = 'schema only; execution must be recorded by provider'
    return result


def image_candidates(detections, pixels):
    """Real detector outputs are unscaled 2D observations, never metric 3D."""
    result = []
    for entry in detections:
        box, score, label = entry['bbox_px'], entry['score'], entry['label']
        if (not isinstance(label, str) or not label or type(score) not in (int, float)
                or not math.isfinite(score) or not .7 <= score <= 1
                or not isinstance(box, list) or len(box) != 4 or not all(type(v) in (int, float) and math.isfinite(v) for v in box)
                or not 0 <= box[0] < box[2] <= pixels[0] or not 0 <= box[1] < box[3] <= pixels[1]):
            raise SceneError('Invalid detector evidence')
        result.append(dict(id='detected_' + str(len(result) + 1), observed_class=label,
                           bbox_px=box, detector_score=score, geometry_status='UNSCALED_2D_ONLY',
                           confidence='needs_confirmation', dimensions_mm=dict(x=None, y=None, z=None),
                           center_mm=None, unknown_details=['Absolute scale', 'Depth', 'Hidden construction']))
    return dict(coordinate_system='original_image_pixels', objects=result,
                scene_ready=False, build_allowed=False, render_executed=False)


class LocalCPUVision:
    """Loads safetensors locally only; no remote code, API key, or network inference."""
    def __init__(self, model_dir, model_metadata, detector_dir=None, detector_metadata=None):
        import torch
        from transformers import AutoModelForVision2Seq, AutoProcessor
        self.torch = torch
        self.metadata = model_metadata
        self.detector_metadata = detector_metadata
        self.detector = None
        torch.set_num_threads(2)
        torch.manual_seed(0)
        self.processor = AutoProcessor.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForVision2Seq.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, torch_dtype=torch.float32, attn_implementation='eager').eval()
        if detector_dir:
            from transformers import AutoImageProcessor, AutoModelForObjectDetection
            self.detector_processor = AutoImageProcessor.from_pretrained(str(detector_dir), local_files_only=True, trust_remote_code=False)
            # The checkpoint contains backbone weights; never fetch a second timm checkpoint.
            self.detector = AutoModelForObjectDetection.from_pretrained(
                str(detector_dir), local_files_only=True, trust_remote_code=False,
                use_safetensors=True, use_pretrained_backbone=False).eval()

    def detect(self, image, original_size):
        if self.detector is None:
            return dict(status='NOT_CONNECTED', scene_ready=False, build_allowed=False, objects=[])
        inputs = self.detector_processor(images=image, return_tensors='pt')
        with self.torch.inference_mode():
            output = self.detector(**inputs)
        detections = self.detector_processor.post_process_object_detection(
            output, threshold=.7, target_sizes=self.torch.tensor([[original_size[1], original_size[0]]]))[0]
        rows = []
        for score, label, box in zip(detections['scores'], detections['labels'], detections['boxes']):
            coords = [max(0., min(float(value), float(original_size[i % 2]))) for i, value in enumerate(box)]
            if coords[0] >= coords[2] or coords[1] >= coords[3]:
                continue
            rows.append(dict(label=self.detector.config.id2label[int(label)], score=float(score), bbox_px=coords))
        geometry = image_candidates(rows, original_size)
        geometry.update(status='DETECTOR_EXECUTED_NOT_ACCEPTED', model=self.detector_metadata)
        return geometry

    def generate(self, image, prompt, max_tokens):
        messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt}]}]
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=text, images=[image], return_tensors='pt')
        with self.torch.inference_mode():
            ids = self.model.generate(**inputs, do_sample=False, max_new_tokens=max_tokens, use_cache=True)
        new_ids = ids[:, inputs['input_ids'].shape[1]:]
        return self.processor.batch_decode(new_ids, skip_special_tokens=True)[0], new_ids.shape[1]

    def analyze(self, intake_path):
        from PIL import Image
        intake_path = Path(intake_path)
        intake = json.loads(intake_path.read_text())
        source = (intake_path.parent / intake['source']).resolve()
        if source.parent != intake_path.parent.resolve() or source.is_symlink():
            raise SceneError('Source must stay inside intake directory')
        if hashlib.sha256(source.read_bytes()).hexdigest() != intake['sha256']:
            raise SceneError('Source image changed')
        with Image.open(source) as original:
            image = original.convert('RGB')
        # Bound CPU cost. Record scale so pixel coordinates cannot silently use original dimensions.
        original_size = list(image.size)
        image.thumbnail((768, 768))
        started = time.monotonic()
        geometry_2d = self.detect(image, original_size)
        caption, caption_tokens = self.generate(image, 'Describe only visible furniture and shapes. Do not guess materials, hidden parts or dimensions.', 96)
        raw, geometry_tokens = self.generate(image, GEOMETRY_PROMPT, 320)
        execution = dict(live_model_executed=True, mode='local_cpu_vlm', model=self.metadata,
                         source_sha256=intake['sha256'], input_type=intake['input_type'],
                         original_pixels=original_size, model_pixels=list(image.size),
                         inference_seconds=time.monotonic() - started,
                         generated_tokens=caption_tokens + geometry_tokens, roles=ROLES,
                         role_execution='18 review responsibilities; one actual local model', render_executed=False)
        result = dict(status='BLOCKED_INVALID_GEOMETRY', execution=execution, caption=caption,
                      caption_status='UNVERIFIED_MODEL_TEXT', image_geometry=geometry_2d,
                      raw_geometry_response=raw, observations=None, build_allowed=False)
        try:
            observations = parse_proposal(raw, intake['sha256'], list(image.size))
            # Keep bbox in the original-image coordinate system expected by compile_scene.
            sx, sy = [a / b for a, b in zip(original_size, image.size)]
            for obj in observations['objects']:
                for item in obj['dimensions'].values():
                    if item.get('bbox_px'):
                        item['bbox_px'] = [value * scale for value, scale in zip(item['bbox_px'], [sx, sy, sx, sy])]
            observations['vision_provenance'].update(live_model_executed=True, model=self.metadata,
                                                     validation='untrusted proposal; independent review required')
            result.update(status='ANALYZED_NEEDS_REVIEW', observations=observations,
                          reason='All measurements and placements require independent review before Blender')
        except SceneError as exc:
            result['reason'] = str(exc)
        return result
