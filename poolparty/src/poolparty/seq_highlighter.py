"""Sequence highlighting with regex-based ANSI styling."""
import re
from .types import Literal, Sequence, beartype

# ANSI escape codes for styling
STYLE_CODES = {
    'red':      '91',
    'green':    '92',
    'yellow':   '93',
    'blue':     '94',
    'magenta':  '95',
    'cyan':     '96',
    'bold':     '1',
    'underline':'4',
}

StyleType = Literal['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'bold', 'underline']

# Regex to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'\033\[[0-9;]*m')


@beartype
class Highlighter:
    """Applies regex-based ANSI styling to sequences."""
    
    def __init__(self, regex: str, style: StyleType) -> None:
        """Create a highlighter with a regex pattern and style.
        
        Args:
            regex: Regular expression pattern to match.
            style: ANSI style to apply ('red', 'green', 'yellow', 'blue', 
                   'magenta', 'cyan', 'bold', 'underline').
        """
        self.regex = regex
        self.style = style
        self._pattern = re.compile(regex)
        self._code = STYLE_CODES[style]
    
    def apply(self, text: str) -> str:
        """Apply this highlighter to text, returning styled string.
        
        Note: For multiple overlapping highlights, use apply_highlights() instead.
        """
        clean_text = self.reset(text)
        start_code = f'\033[{self._code}m'
        reset_code = '\033[0m'
        return self._pattern.sub(lambda m: f'{start_code}{m.group()}{reset_code}', clean_text)
    
    @staticmethod
    def reset(text: str) -> str:
        """Strip all ANSI escape codes from text."""
        return ANSI_ESCAPE_PATTERN.sub('', text)
    
    def __repr__(self) -> str:
        return f"Highlighter(regex={self.regex!r}, style={self.style!r})"


@beartype
def apply_highlights(text: str, highlighters: Sequence[Highlighter]) -> str:
    """Apply multiple highlighters with proper overlap handling.
    
    Uses character-by-character style tracking so overlapping regions
    get all applicable styles combined (e.g., red + underline).
    """
    if not highlighters:
        return text
    
    # Strip any existing ANSI codes
    clean_text = Highlighter.reset(text)
    n = len(clean_text)
    if n == 0:
        return clean_text
    
    # Track styles for each character position
    char_styles: list[set[str]] = [set() for _ in range(n)]
    
    # Apply each highlighter's matches to the style tracking
    for hl in highlighters:
        for match in hl._pattern.finditer(clean_text):
            for i in range(match.start(), match.end()):
                char_styles[i].add(hl._code)
    
    # Build output with combined ANSI codes
    result = []
    current_styles: set[str] = set()
    
    for i, char in enumerate(clean_text):
        new_styles = char_styles[i]
        if new_styles != current_styles:
            if current_styles:
                result.append('\033[0m')  # Reset previous styles
            if new_styles:
                codes = ';'.join(sorted(new_styles))
                result.append(f'\033[{codes}m')
            current_styles = new_styles
        result.append(char)
    
    # Reset at end if we have active styles
    if current_styles:
        result.append('\033[0m')
    
    return ''.join(result)
