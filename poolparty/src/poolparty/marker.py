"""Marker class for poolparty - placeholder tags for sequence insertion."""
from .types import Optional, beartype


@beartype
class Marker:
    """A marker placeholder that can be inserted into sequences."""
    
    def __init__(self, name: Optional[str] = None) -> None:
        """Initialize Marker and register with the active Party."""
        from .party import get_active_party
        party = get_active_party()
        if party is None:
            raise RuntimeError(
                "Markers must be created inside a Party context. "
                "Use: with pp.Party() as party: ..."
            )
        self._party = party
        self._id = party._get_next_marker_id()
        self._name: str = ""
        self.name = name if name is not None else f'marker[{self._id}]'
        party._register_marker(self)
    
    @property
    def id(self) -> int:
        """Unique ID for this marker."""
        return self._id
    
    @property
    def name(self) -> str:
        """Name of this marker."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Set marker name, validating uniqueness with the Party."""
        self._party._validate_marker_name(value, self)
        old_name = self._name
        self._name = value
        if old_name:
            self._party._update_marker_name(self, old_name, value)
    
    @property
    def tag(self) -> str:
        """Return the marker tag string, e.g., '{marker[0]}'."""
        return f'{{{self.name}}}'
    
    def __repr__(self) -> str:
        return f"Marker(id={self._id}, name={self.name!r}, tag={self.tag!r})"
