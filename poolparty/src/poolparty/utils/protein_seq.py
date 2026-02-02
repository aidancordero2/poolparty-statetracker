"""ProteinSeq class for protein sequences with styling support."""

from dataclasses import dataclass

from .seq import Seq, _NOT_COMPUTED
from .style_utils import SeqStyle, styles_suppressed

# Valid amino acid characters (single-letter codes + stop codon)
VALID_PROTEIN_CHARS = frozenset("ACDEFGHIKLMNPQRSTVWYacdefghiklmnpqrstvwy*")


@dataclass(frozen=True)
class ProteinSeq(Seq):
    """Protein sequence with styling support.

    Subclass of Seq specialized for amino acid sequences. Uses protein alphabet
    for molecular coordinate computation instead of DNA alphabet.
    """

    def __repr__(self) -> str:
        """String representation."""
        num_styles = len(self.style.style_list) if self.style else 0
        return f"ProteinSeq(len={len(self.string)}, styles={num_styles})"

    def _ensure_coord_maps(self) -> None:
        """Compute coordinate maps using protein alphabet."""
        if self._nontag_to_literal is _NOT_COMPUTED or (
            self._nontag_to_literal == () and len(self.string) > 0
        ):
            from . import parsing_utils

            string = self.string
            n = len(string)

            # Fast path: no tags possible if no '<' character
            if "<" not in string:
                # For tag-free strings: nontag coords == literal coords
                identity_map = tuple(range(n))

                # molecular_to_literal: only valid amino acid characters
                molecular_positions = []
                for i, c in enumerate(string):
                    if c in VALID_PROTEIN_CHARS:
                        molecular_positions.append(i)
                molecular_to_literal = tuple(molecular_positions)

                # literal_to_molecular: reverse mapping (None for non-AA chars)
                literal_to_molecular_list = [None] * n
                for mol_idx, lit_pos in enumerate(molecular_to_literal):
                    literal_to_molecular_list[lit_pos] = mol_idx
                literal_to_molecular = tuple(literal_to_molecular_list)

                object.__setattr__(self, "_nontag_to_literal", identity_map)
                object.__setattr__(self, "_molecular_to_literal", molecular_to_literal)
                object.__setattr__(self, "_literal_to_nontag", identity_map)
                object.__setattr__(self, "_literal_to_molecular", literal_to_molecular)
            else:
                # Has tags - need full parsing
                nontag_positions = parsing_utils.get_nontag_positions(string)
                nontag_to_literal = tuple(nontag_positions)

                # molecular_to_literal: only valid amino acid characters
                molecular_positions = []
                for lit_pos in nontag_positions:
                    char = string[lit_pos]
                    if char in VALID_PROTEIN_CHARS:
                        molecular_positions.append(lit_pos)
                molecular_to_literal = tuple(molecular_positions)

                # literal_to_nontag: map literal positions to nontag
                literal_to_nontag_list = [None] * n
                for nontag_idx, lit_pos in enumerate(nontag_to_literal):
                    literal_to_nontag_list[lit_pos] = nontag_idx
                literal_to_nontag = tuple(literal_to_nontag_list)

                # literal_to_molecular: map literal positions to molecular
                literal_to_molecular_list = [None] * n
                for mol_idx, lit_pos in enumerate(molecular_to_literal):
                    literal_to_molecular_list[lit_pos] = mol_idx
                literal_to_molecular = tuple(literal_to_molecular_list)

                object.__setattr__(self, "_nontag_to_literal", nontag_to_literal)
                object.__setattr__(self, "_molecular_to_literal", molecular_to_literal)
                object.__setattr__(self, "_literal_to_nontag", literal_to_nontag)
                object.__setattr__(self, "_literal_to_molecular", literal_to_molecular)

    @classmethod
    def from_string(cls, string: str, style: SeqStyle | None = None) -> "ProteinSeq":
        """Create ProteinSeq from string.

        Parameters
        ----------
        string : str
            Protein sequence string (single-letter amino acid codes).
        style : SeqStyle | None, default=None
            Optional style. If None, creates empty style (or None if suppressed).

        Returns
        -------
        ProteinSeq
            New ProteinSeq with coordinate maps.
        """
        from . import parsing_utils

        if style is None:
            style = None if styles_suppressed() else SeqStyle.empty(len(string))

        # Fast path: no tags
        if "<" not in string:
            seq = cls.__new__(cls)
            object.__setattr__(seq, "string", string)
            object.__setattr__(seq, "style", style)
            object.__setattr__(seq, "_clean", string)
            object.__setattr__(seq, "_regions", ())
            object.__setattr__(seq, "_nontag_to_literal", _NOT_COMPUTED)
            object.__setattr__(seq, "_molecular_to_literal", _NOT_COMPUTED)
            object.__setattr__(seq, "_literal_to_nontag", _NOT_COMPUTED)
            object.__setattr__(seq, "_literal_to_molecular", _NOT_COMPUTED)
            return seq

        # Parse regions
        regions = tuple(parsing_utils.find_all_regions(string, _skip_validation=True))
        clean = parsing_utils.strip_all_tags(string)

        seq = cls.__new__(cls)
        object.__setattr__(seq, "string", string)
        object.__setattr__(seq, "style", style)
        object.__setattr__(seq, "_clean", clean)
        object.__setattr__(seq, "_regions", regions)
        object.__setattr__(seq, "_nontag_to_literal", _NOT_COMPUTED)
        object.__setattr__(seq, "_molecular_to_literal", _NOT_COMPUTED)
        object.__setattr__(seq, "_literal_to_nontag", _NOT_COMPUTED)
        object.__setattr__(seq, "_literal_to_molecular", _NOT_COMPUTED)

        return seq

    @classmethod
    def empty(cls) -> "ProteinSeq":
        """Create empty ProteinSeq."""
        return cls.from_string("", SeqStyle.empty(0))

    def with_style(self, style: SeqStyle | None) -> "ProteinSeq":
        """Return copy with updated style (preserves coordinate maps)."""
        seq = ProteinSeq.__new__(ProteinSeq)
        object.__setattr__(seq, "string", self.string)
        object.__setattr__(seq, "style", style)
        object.__setattr__(seq, "_clean", self._clean)
        object.__setattr__(seq, "_regions", self._regions)
        object.__setattr__(seq, "_nontag_to_literal", self._nontag_to_literal)
        object.__setattr__(seq, "_molecular_to_literal", self._molecular_to_literal)
        object.__setattr__(seq, "_literal_to_nontag", self._literal_to_nontag)
        object.__setattr__(seq, "_literal_to_molecular", self._literal_to_molecular)
        return seq

    def add_style(self, style_spec: str, positions) -> "ProteinSeq":
        """Return copy with additional style added."""
        if self.style is None:
            return self
        new_style = self.style.add_style(style_spec, positions)
        return self.with_style(new_style)
