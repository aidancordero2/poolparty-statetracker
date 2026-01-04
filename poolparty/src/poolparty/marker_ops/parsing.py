"""XML-style marker parsing utilities for poolparty."""
import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET
from poolparty.types import Optional, Literal, Callable

# Regex pattern for XML-style marker tags
# 
# Example: <item id="5" type='main'/>
#          │ │   │                  │
#          │ │   │                  └─ Group 4: "/" (self-closing slash, or empty)
#          │ │   └─ Group 3: " id=\"5\" type='main'" (all attributes, or empty)
#          │ └─ Group 2: "item" (tag name)
#          └─ Group 1: "" (closing slash, or empty if opening tag)
#
# Other examples:
#   <div>       -> ("", "div", "", "")
#   </div>      -> ("/", "div", "", "")
#   <br/>       -> ("", "br", "", "/")
#   <a href="x"> -> ("", "a", " href=\"x\"", "")
TAG_PATTERN = re.compile(r'<(/?)(\w+)((?:\s+\w+=[\'"][^\'"]*[\'"])*)\s*(/?)>')


@dataclass
class ParsedMarker:
    """Represents a parsed XML-style region marker in a sequence."""
    name: str
    start: int          # Position of opening tag '<'
    end: int            # Position after closing tag '>' or '/>'
    content_start: int  # Position of first content character
    content_end: int    # Position after last content character
    strand: str         # '+' or '-'
    content: str        # The sequence content inside the marker
    declared_seq_length_str: Optional[str]  # None if not declared, 'None' if variable, '4' if declared as 4
    
    @property
    def is_zero_length(self) -> bool:
        """True if this is a zero-length (self-closing) marker."""
        return self.content_start == self.content_end
    
    @property
    def inferred_seq_length(self) -> int:
        """The actual length of the content (inferred from content)."""
        return len(self.content)
    
    @property
    def is_variable_length(self) -> bool:
        """True if seq_length was explicitly declared as 'None' (variable length marker)."""
        return self.declared_seq_length_str == 'None'


def _parse_attributes(attrs_str: str) -> tuple[str, Optional[str]]:
    """Parse strand and seq_length from an attributes string.
    
    Returns:
        (strand, declared_seq_length_str) where:
        - strand is '+' or '-' (defaults to '+')
        - declared_seq_length_str is None (not declared), 'None' (variable length),
          or the string representation of the declared int (e.g., '4')
    """
    strand = '+'
    declared_seq_length_str: Optional[str] = None
    
    if not attrs_str:
        return strand, declared_seq_length_str
    
    # Parse strand attribute
    strand_match = re.search(r"strand=['\"]([+-])['\"]", attrs_str)
    if strand_match:
        strand = strand_match.group(1)
    
    # Parse seq_length attribute
    seq_len_match = re.search(r"seq_length=['\"](\w+)['\"]", attrs_str)
    if seq_len_match:
        value = seq_len_match.group(1)
        if value == 'None':
            declared_seq_length_str = 'None'
        else:
            try:
                parsed_int = int(value)
                if parsed_int < 0:
                    raise ValueError(f"seq_length must be non-negative, got {parsed_int}")
                declared_seq_length_str = value  # Store the string representation
            except ValueError:
                raise ValueError(f"Invalid seq_length value: '{value}'. Must be an integer in quotes or 'None'.")
    
    return strand, declared_seq_length_str


def find_all_markers(seq: str) -> list[ParsedMarker]:
    """Find all markers in a sequence.
    
    Returns a list of ParsedMarker objects for each marker found.
    Raises ValueError if markers are malformed (unmatched open/close tags).
    Supports nested markers.
    """
    # Validate structure with stdlib XML parser
    try:
        ET.fromstring(f"<_root_>{seq}</_root_>")
    except ET.ParseError as e:
        raise ValueError(f"Invalid marker syntax: {e}")
    
    markers = []
    open_stack = []  # [(name, strand, declared_seq_length_str, tag_start, content_start)]
    
    for match in TAG_PATTERN.finditer(seq):
        is_close = match.group(1) == '/'
        name = match.group(2)
        attrs = match.group(3) or ''
        is_self_close = match.group(4) == '/'
        
        if is_self_close:
            # Self-closing tag: <name/>
            strand, declared_seq_length_str = _parse_attributes(attrs)
            # Validate seq_length for self-closing
            if declared_seq_length_str is not None and declared_seq_length_str not in ('0', 'None'):
                raise ValueError(
                    f"Self-closing marker '<{name}/>' has seq_length='{declared_seq_length_str}' "
                    f"but contains no content. Use seq_length='0' or omit the attribute."
                )
            markers.append(ParsedMarker(
                name=name,
                start=match.start(),
                end=match.end(),
                content_start=match.end(),
                content_end=match.end(),
                strand=strand,
                content='',
                declared_seq_length_str=declared_seq_length_str,
            ))
        elif is_close:
            # Closing tag: </name> - pop innermost matching open tag
            for i in reversed(range(len(open_stack))):
                if open_stack[i][0] == name:
                    oname, strand, declared_seq_length_str, ostart, cstart = open_stack.pop(i)
                    content = seq[cstart:match.start()]
                    # Validate seq_length if declared as an integer
                    if declared_seq_length_str is not None and declared_seq_length_str != 'None':
                        if len(content) != int(declared_seq_length_str):
                            raise ValueError(
                                f"Marker '<{oname}>' has seq_length='{declared_seq_length_str}' "
                                f"but content has length {len(content)}: '{content}'"
                            )
                    markers.append(ParsedMarker(
                        name=oname,
                        start=ostart,
                        end=match.end(),
                        content_start=cstart,
                        content_end=match.start(),
                        strand=strand,
                        content=content,
                        declared_seq_length_str=declared_seq_length_str,
                    ))
                    break
        else:
            # Opening tag: <name>
            strand, declared_seq_length_str = _parse_attributes(attrs)
            open_stack.append((name, strand, declared_seq_length_str, match.start(), match.end()))
    
    return sorted(markers, key=lambda m: m.start)


def has_marker(seq: str, name: str) -> bool:
    """Check if a marker with the given name exists in the sequence."""
    markers = find_all_markers(seq)
    return any(m.name == name for m in markers)


def validate_single_marker(seq: str, name: str) -> ParsedMarker:
    """Validate that exactly one marker with the given name exists.
    
    Returns the ParsedMarker if found.
    Raises ValueError if marker not found or appears multiple times.
    """
    markers = find_all_markers(seq)
    matching = [m for m in markers if m.name == name]
    
    if len(matching) == 0:
        available = [m.name for m in markers]
        if available:
            raise ValueError(
                f"Marker '{name}' not found in sequence. "
                f"Available markers: {available}"
            )
        else:
            raise ValueError(f"Marker '{name}' not found in sequence (no markers present)")
    
    if len(matching) > 1:
        positions = [m.start for m in matching]
        raise ValueError(
            f"Marker '{name}' appears {len(matching)} times in sequence "
            f"(at positions {positions}). Each marker must appear exactly once."
        )
    
    return matching[0]


def parse_marker(seq: str, name: str) -> tuple[str, str, str, str]:
    """Parse a named marker from a sequence.
    
    Returns (prefix, content, suffix, strand) where:
    - prefix: sequence before the marker (excluding the opening tag)
    - content: sequence inside the marker
    - suffix: sequence after the marker (excluding the closing tag)
    - strand: '+' or '-'
    
    Raises ValueError if marker not found or appears multiple times.
    """
    marker = validate_single_marker(seq, name)
    prefix = seq[:marker.start]
    suffix = seq[marker.end:]
    return prefix, marker.content, suffix, marker.strand


def strip_all_markers(seq: str) -> str:
    """Remove all marker tags from sequence, keeping content.
    
    Example:
        'ACG<region>TT</region>AA' -> 'ACGTTAA'
        'ACG<ins/>TT' -> 'ACGTT'
    """
    return TAG_PATTERN.sub('', seq)


def transform_nonmarker_chars(seq: str, transform_fn: Callable[[str], str]) -> str:
    """Apply a transformation to only non-marker characters in a sequence.
    
    Preserves XML marker tags exactly as they appear while transforming
    all other characters using the provided function.
    
    Example:
        transform_nonmarker_chars('ACgt<region>TT</region>', str.lower)
        -> 'acgt<region>tt</region>'
    """
    result = []
    last_end = 0
    for match in TAG_PATTERN.finditer(seq):
        # Transform text before this tag
        result.append(transform_fn(seq[last_end:match.start()]))
        # Keep the tag unchanged
        result.append(match.group(0))
        last_end = match.end()
    # Transform remaining text after last tag
    result.append(transform_fn(seq[last_end:]))
    return ''.join(result)


def reverse_complement_with_markers(
    seq: str, 
    complement_fn: Callable[[str], str]
) -> str:
    """Reverse complement a sequence while preserving XML marker structure.
    
    Markers are repositioned based on their content coordinates:
    - Region markers [start, end) map to [n-end, n-start) in reversed sequence
    - Self-closing markers at position i map to position n-i
    
    Example:
        # complement_fn maps A<->T, C<->G
        reverse_complement_with_markers('ACG<region>TT</region>AA', complement_fn)
        -> 'TT<region>AA</region>CGT'
    """
    # Parse markers
    markers = find_all_markers(seq)
    
    # If no markers, just reverse complement the content
    if not markers:
        return ''.join(complement_fn(c) for c in reversed(seq))
    
    # Get content without markers
    content = strip_all_markers(seq)
    n = len(content)
    
    # Build mapping from literal positions to content positions
    nonmarker_positions = get_nonmarker_positions(seq)
    literal_to_content = {lit: i for i, lit in enumerate(nonmarker_positions)}
    
    # Calculate content ranges for each marker and their new positions
    marker_info = []
    for m in markers:
        if m.is_zero_length:
            # Self-closing marker: find its content position
            # It's positioned "before" the character at the next content position
            # Find the content position after this marker
            content_pos = None
            for lit_pos in range(m.end, len(seq) + 1):
                if lit_pos in literal_to_content:
                    content_pos = literal_to_content[lit_pos]
                    break
            if content_pos is None:
                content_pos = n  # At the end
            
            # New position: n - content_pos
            new_pos = n - content_pos
            
            # Determine seq_length for build_marker_tag
            if m.declared_seq_length_str == 'None':
                seq_length_arg = -1  # Will produce seq_length='None'
            elif m.declared_seq_length_str is not None:
                seq_length_arg = int(m.declared_seq_length_str)
            else:
                seq_length_arg = None
            
            marker_info.append({
                'name': m.name,
                'strand': m.strand,
                'seq_length_arg': seq_length_arg,
                'is_zero_length': True,
                'new_start': new_pos,
                'new_end': new_pos,
            })
        else:
            # Region marker: find content start and end
            content_start = literal_to_content[m.content_start]
            # content_end is one past the last character inside the marker
            # m.content_end is the literal position of the closing tag '<'
            # We need to find the content index after the last content char
            if m.content_end == m.content_start:
                # Empty marker content
                content_end = content_start
            else:
                # Find the last content character before m.content_end
                last_content_literal = m.content_end - 1
                while last_content_literal >= m.content_start and last_content_literal not in literal_to_content:
                    last_content_literal -= 1
                if last_content_literal >= m.content_start:
                    content_end = literal_to_content[last_content_literal] + 1
                else:
                    content_end = content_start
            
            # New positions: [n - end, n - start)
            new_start = n - content_end
            new_end = n - content_start
            
            # Determine seq_length for build_marker_tag
            if m.declared_seq_length_str == 'None':
                seq_length_arg = -1
            elif m.declared_seq_length_str is not None:
                seq_length_arg = int(m.declared_seq_length_str)
            else:
                seq_length_arg = None
            
            marker_info.append({
                'name': m.name,
                'strand': m.strand,
                'seq_length_arg': seq_length_arg,
                'is_zero_length': False,
                'new_start': new_start,
                'new_end': new_end,
            })
    
    # Reverse complement the content
    rc_content = ''.join(complement_fn(c) for c in reversed(content))
    
    # Build result by inserting markers at their new positions
    # We need to handle overlapping/nested markers properly
    # Strategy: collect all "events" (marker starts and ends) and process in order
    
    events = []  # (position, priority, event_type, marker_idx)
    # Priority: lower = processed first at same position
    # For opening tags: use marker length as priority (longer markers open first)
    # For closing tags: use negative marker length (shorter markers close first)
    # For self-closing: use 0
    
    for idx, mi in enumerate(marker_info):
        if mi['is_zero_length']:
            events.append((mi['new_start'], 0, 'self_close', idx))
        else:
            marker_len = mi['new_end'] - mi['new_start']
            events.append((mi['new_start'], -marker_len, 'open', idx))
            events.append((mi['new_end'], marker_len, 'close', idx))
    
    # Sort events by position, then by priority
    events.sort(key=lambda e: (e[0], e[1]))
    
    # Build result
    result = []
    last_pos = 0
    
    for pos, priority, event_type, idx in events:
        # Add content up to this position
        if pos > last_pos:
            result.append(rc_content[last_pos:pos])
            last_pos = pos
        
        mi = marker_info[idx]
        if event_type == 'self_close':
            result.append(build_marker_tag(
                mi['name'],
                content='',
                strand=mi['strand'],
                seq_length=mi['seq_length_arg'],
            ))
        elif event_type == 'open':
            # Build opening tag
            attrs = []
            if mi['strand'] == '-':
                attrs.append("strand='-'")
            if mi['seq_length_arg'] is not None:
                if mi['seq_length_arg'] == -1:
                    attrs.append("seq_length='None'")
                else:
                    attrs.append(f"seq_length='{mi['seq_length_arg']}'")
            attrs_str = ' ' + ' '.join(attrs) if attrs else ''
            result.append(f"<{mi['name']}{attrs_str}>")
        elif event_type == 'close':
            result.append(f"</{mi['name']}>")
    
    # Add remaining content
    if last_pos < n:
        result.append(rc_content[last_pos:])
    
    return ''.join(result)


def get_length_without_markers(seq: str) -> int:
    """Get sequence length excluding marker tags (but including marker content)."""
    return len(strip_all_markers(seq))


def get_nonmarker_positions(seq: str) -> list[int]:
    """Get raw string positions of all characters excluding marker tag interiors.
    
    Returns positions of characters that are NOT part of marker tags.
    This includes marker content but excludes the <...> tag syntax itself.
    """
    # Find all marker tag spans (the tags themselves, not content)
    tag_spans: set[int] = set()
    for match in TAG_PATTERN.finditer(seq):
        for i in range(match.start(), match.end()):
            tag_spans.add(i)
    
    return [i for i in range(len(seq)) if i not in tag_spans]


def get_literal_positions(seq: str) -> list[int]:
    """Get all raw string positions in a sequence.
    
    Returns list(range(len(seq))). Provided for API completeness
    alongside get_nonmarker_positions and get_molecular_positions.
    """
    return list(range(len(seq)))


def nonmarker_pos_to_literal_pos(seq: str, nonmarker_pos: int) -> int:
    """Convert a non-marker position to a literal string position.
    
    Args:
        seq: Sequence string possibly containing markers.
        nonmarker_pos: Position in non-marker coordinate space (0-indexed).
            Can be 0 to len(nonmarker_positions) inclusive, where the
            maximum value represents "one past the end" for slicing.
    
    Returns:
        The corresponding literal string position.
    
    Raises:
        ValueError: If nonmarker_pos is out of range.
    """
    nonmarker_positions = get_nonmarker_positions(seq)
    seq_len = len(nonmarker_positions)
    
    if nonmarker_pos < 0 or nonmarker_pos > seq_len:
        raise ValueError(
            f"nonmarker_pos ({nonmarker_pos}) out of range [0, {seq_len}]"
        )
    
    if nonmarker_pos == seq_len:
        return len(seq)  # One past the end
    return nonmarker_positions[nonmarker_pos]


def build_marker_tag(
    name: str, 
    content: str = '', 
    strand: str = '+',
    seq_length: Optional[int] = None,
    explicit_strand: bool = False,
) -> str:
    """Build an XML marker tag string.
    
    Args:
        name: Marker name
        content: Content to wrap (empty string for zero-length marker)
        strand: '+' or '-' ('+' is omitted from output by default)
        seq_length: Optional declared seq_length (None to omit, -1 for 'None')
        explicit_strand: If True, include strand='+' explicitly (useful for strand='both')
    
    Returns:
        XML marker string like '<name>content</name>' or '<name/>'
    """
    attrs = []
    if strand == '-':
        attrs.append("strand='-'")
    elif explicit_strand:
        attrs.append("strand='+'")
    if seq_length is not None:
        if seq_length == -1:
            attrs.append("seq_length='None'")
        else:
            attrs.append(f"seq_length='{seq_length}'")
    
    attrs_str = ' ' + ' '.join(attrs) if attrs else ''
    
    if content == '':
        return f"<{name}{attrs_str}/>"
    else:
        return f"<{name}{attrs_str}>{content}</{name}>"


def _validate_markers(seq: str) -> set:
    """
    Parse markers from a sequence string and register/validate with Party.
    
    For each marker found:
    - If seq_length attribute is declared and not 'None': validate content matches
    - If seq_length='None': register as variable-length (seq_length=None)
    - If no seq_length attribute: infer seq_length from content length
    
    This function should be called by any function that takes a user sequence
    string and creates a Pool (like from_seq).
    
    Parameters
    ----------
    seq : str
        The sequence string potentially containing XML markers.
    
    Returns
    -------
    set[Marker]
        Set of Marker objects found in the sequence.
    
    Raises
    ------
    ValueError
        If marker length conflicts with previously registered marker.
    """
    from ..party import get_active_party
    from ..marker import Marker
    
    party = get_active_party()
    if party is None:
        # No active party, return empty set
        return set()
    
    markers_found: set[Marker] = set()
    region_markers = find_all_markers(seq)
    
    for rm in region_markers:
        # Determine the seq_length to register
        if rm.declared_seq_length_str == 'None':
            # Explicitly declared as variable length
            seq_length = None
        elif rm.declared_seq_length_str is not None:
            # Explicitly declared with a specific length (already validated in parsing)
            seq_length = int(rm.declared_seq_length_str)
        else:
            # Not declared, infer from content
            seq_length = len(rm.content)
        
        # Register with party (will raise if conflict)
        marker = party.register_marker(rm.name, seq_length)
        markers_found.add(marker)
    
    return markers_found
