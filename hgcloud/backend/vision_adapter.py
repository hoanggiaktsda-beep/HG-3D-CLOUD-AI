"""Configurable boundary; no network/paid provider enabled by default."""
from typing import Protocol
class VisionUnavailable(RuntimeError):pass
class VisionProvider(Protocol):
    def analyze(self,image:bytes,input_type:str,instruction:str)->dict:...
class DisabledVisionProvider:
    def analyze(self,image,input_type,instruction):
        raise VisionUnavailable('CHƯA KẾT NỐI AI thị giác được cấp quyền')
def configure_provider(name='disabled'):
    if name!='disabled':raise VisionUnavailable('Provider not installed or authorized; no external request made')
    return DisabledVisionProvider()
