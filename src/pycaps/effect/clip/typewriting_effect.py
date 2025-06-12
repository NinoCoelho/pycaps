from .clip_effect import ClipEffect
from pycaps.common import Document, WordClip, ElementState
from pycaps.tag import TagCondition
from typing import Optional
from pycaps.logger import logger

class TypewritingEffect(ClipEffect):
    """
    Affect that applies a typewriting effect to the words that match the tag condition.
    This effect creates a new image clip for each letter of the word, so it's very slow.

    If you need a faster alternative for this effect, check the TypewritingAnimation class.
    """
    def __init__(self, tag_condition: Optional[TagCondition] = None):
        self.tag_condition: Optional[TagCondition] = tag_condition

    def run(self, document: Document) -> None:
        for line in document.get_lines():
            self._renderer.open_line(line, ElementState.WORD_BEING_NARRATED)
            for i, word in enumerate(line.words):
                if self.tag_condition and not self.tag_condition.evaluate(list(word.get_all_tags())):
                    continue
                for clip in word.clips:
                    self._apply_typewriting(i, clip)
            self._renderer.close_line()

    def _apply_typewriting(self, word_index: int, clip: WordClip) -> None:
        from moviepy.editor import ImageClip, CompositeVideoClip
        import numpy as np

        if not clip.has_state(ElementState.WORD_BEING_NARRATED):
            return
        word = clip.get_word()
        number_of_letters = len(word.text)
        word_duration = word.time.end - word.time.start
        letter_duration = word_duration / number_of_letters
        new_clips = []
        for i in range(number_of_letters):
            image = self._renderer.render_word(word_index, word, ElementState.WORD_BEING_NARRATED, i+1)
            if not image:
                continue
            y_position = 0
            if clip.layout.size.height != image.height:
                logger().warning("The fragment height is not equal to the whole word height. This could cause the text to be misaligned.")
                logger().warning(f"Word height: {clip.layout.size.height} | Fragment height: {image.height}")
                logger().warning("If this is unexpected, report this issue")
                logger().warning("As quick fix, try to use another font family or force a line-height/height for each word.")
                y_position = (clip.layout.size.height - image.height) / 2
            
            image_clip: ImageClip = (
                ImageClip(np.array(image))
                .set_start(i * letter_duration)
                .set_duration(letter_duration)
                .set_position((0, y_position))
            )
            new_clips.append(image_clip)

        if len(new_clips) > 0:
            clip.moviepy_clip = CompositeVideoClip(new_clips, size=(clip.layout.size.width, clip.layout.size.height))
            clip.moviepy_clip = (
                clip.moviepy_clip
                .set_position((clip.layout.position.x, clip.layout.position.y))
                .set_start(word.time.start)
                .set_duration(word_duration)
            )
