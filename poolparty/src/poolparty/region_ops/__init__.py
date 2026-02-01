"""Region module for poolparty - XML-style region tags for sequence annotation."""

# Import parsing utilities (no dependencies on Operation)
from ..utils.parsing_utils import (
    TAG_PATTERN,
    ParsedRegion,
    build_region_tags,
    find_all_regions,
    get_length_without_tags,
    get_literal_positions,
    get_nontag_positions,
    has_region,
    nontag_pos_to_literal_pos,
    parse_region,
    strip_all_tags,
    validate_single_region,
)
from .annotate_region import annotate_region as annotate_region
from .apply_at_region import apply_at_region as apply_at_region
from .extract_region import extract_region as extract_region

# Import operation functions (Operation is now available)
from .insert_tags import insert_tags as insert_tags
from .region_multiscan import RegionMultiScanOp
from .region_multiscan import region_multiscan as region_multiscan
from .region_scan import RegionScanOp
from .region_scan import region_scan as region_scan
from .remove_tags import remove_tags as remove_tags
from .replace_region import replace_region as replace_region

__all__ = [
    # Parsing utilities
    "TAG_PATTERN",
    "ParsedRegion",
    "parse_region",
    "find_all_regions",
    "has_region",
    "validate_single_region",
    "strip_all_tags",
    "get_length_without_tags",
    "get_nontag_positions",
    "get_literal_positions",
    "nontag_pos_to_literal_pos",
    "build_region_tags",
    # Operations
    "annotate_region",
    "insert_tags",
    "extract_region",
    "replace_region",
    "apply_at_region",
    "remove_tags",
    "region_scan",
    "region_multiscan",
    "RegionScanOp",
    "RegionMultiScanOp",
]
