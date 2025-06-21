import cv2
import numpy as np
from abc import ABC, abstractmethod
from .function_container import get_function, register_function
from typing import Callable, Union, Tuple, Optional
import inspect

class MediaElement(ABC):
    def __init__(self, start: float, duration: float):
        self._start = start
        self._duration = duration
        self._size: Tuple[int, int] = (0, 0)
        self._position: str = register_function(lambda t: (0, 0))
        self._opacity: str = register_function(lambda t: 1)
        self._scale: str = register_function(lambda t: 1)

    def set_position(self, value: Union[Callable[[float], Tuple[int, int]], Tuple[int, int]]):
        self._position = self._save_as_function(value)

    def set_opacity(self, value: Union[Callable[[float], float], float]):
        self._opacity = self._save_as_function(value)

    def set_scale(self, value: Union[Callable[[float], float], float]):
        self._scale = self._save_as_function(value)

    def set_size(self, width: Optional[int] = None, height: Optional[int] = None) -> None:
        if width is None and height is None:
            raise ValueError(f"Either width ({width}) or height ({height}) must contain a value")
        
        if width is None:
            if height <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int((height / self._size[1]) * self._size[0])
            new_h = int(height)
        elif height is None:
            if width <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int(width)
            new_h = int((width / self._size[0]) * self._size[1])
        else:
            new_w = int(width)
            new_h = int(height)
        
        self._size = (new_w, new_h)

    def _save_as_function(self, value: Union[Callable, float, Tuple[int, int]]) -> str:
        if inspect.isfunction(value):
            return register_function(value)
        fn = lambda t, v=value: v
        return register_function(fn)

    @property
    def position(self):
        return get_function(self._position)
    
    @property
    def opacity(self):
        return get_function(self._opacity)
    
    @property
    def scale(self):
        return get_function(self._scale)
    
    @property
    def size(self):
        return self._size

    @property
    def start(self):
        return self._start
    
    @property
    def duration(self):
        return self._duration
    
    @property
    def end(self):
        return self.start + self.duration

    @abstractmethod
    def get_frame(self, t_rel: float) -> np.ndarray:
        pass

    def render(self, bg: np.ndarray, t_global: float) -> np.ndarray:
        t_rel = (t_global - self._start)
        if not (0 <= t_rel <= self._duration):
            return bg

        frame = self.get_frame(t_rel)
        x, y = self.position(t_rel)
        x, y = int(x), int(y)
        s = self.scale(t_rel)
        alpha_val = self.opacity(t_rel)

        # TODO: I think there's room for performance improvement over here... 

        # source: https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html#ga47a974309e9102f5f08231edc7e7529d
        # "To shrink an image, it will generally look best with INTER_AREA interpolation, whereas to enlarge an image,
        #  it will generally look best with INTER_CUBIC (slow) or INTER_LINEAR (faster but still looks OK)."
        interpolation_method = cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC
        scaled_w, scaled_h = int(self._size[0] * s), int(self._size[1] * s)
        frame = cv2.resize(frame, (scaled_w, scaled_h), interpolation=interpolation_method)
        frame = np.clip(frame, 0.0, 255.0)
        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

        # apply opacity
        frame[:, :, 3] = frame[:, :, 3] * alpha_val

        H, W = bg.shape[:2]
        h, w = frame.shape[:2]

        # position of frame over background
        y1_bg = max(y, 0)
        x1_bg = max(x, 0)
        y2_bg = min(y + h, H)
        x2_bg = min(x + w, W)

        # if the frame is outside the background, then we just ignore it
        if y1_bg >= y2_bg or x1_bg >= x2_bg:
            return bg

        # positions of frame 
        y1_fr = y1_bg - y       # if y < 0 then y1_fr > 0
        x1_fr = x1_bg - x
        y2_fr = y2_bg - y
        x2_fr = x2_bg - x

        roi = bg[y1_bg:y2_bg, x1_bg:x2_bg]
        sub_fr = frame[y1_fr:y2_fr, x1_fr:x2_fr]

        frame_alpha = sub_fr[..., 3] / 255.0
        if bg.shape[2] == 3:
            # we're blending a BGR image (the background) with a BGRA image (the frame)
            inv = 1.0 - frame_alpha
            for c in range(3):
                roi[..., c] = sub_fr[..., c] * frame_alpha + roi[..., c] * inv
        else:
            # we're blending two BGRA images (we apply Porter–Duff "source over")
            bg_alpha = roi[..., 3] / 255.0
            final_alpha = frame_alpha + bg_alpha * (1.0 - frame_alpha)

            for c in range(3):
                roi[..., c] = (sub_fr[..., c] * frame_alpha + roi[..., c] * bg_alpha * (1.0 - frame_alpha)) / np.clip(final_alpha, 1e-6, 1.0)

            roi[..., 3] = final_alpha * 255.0
            bg[y1_bg:y2_bg, x1_bg:x2_bg] = roi

        return bg
