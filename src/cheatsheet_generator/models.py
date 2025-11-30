from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Hotkey:
    key: str
    description: str
    section: str
    subsection: str = ""

    def __post_init__(self):
        if not self.key or not self.description or not self.section:
            raise ValueError("Key, description, and section are required")


@dataclass
class CheatSheetConfig:
    title: str = "Hotkey Cheat Sheet"
    font_size: int = 7
    header_font_size: int = 10
    margin: float = 25
    columns: int = 5
    row_height: float = 11
    section_spacing: float = 8
    subsection_spacing: float = 4
    paper_size: str = "letter"  # letter, a4
    orientation: str = "portrait"  # portrait, landscape
    fill_top_half: bool = False  # 2-row layout: fill top half before bottom
    section_align_flush: bool = True  # Remove section spacing if first in column
    section_no_awkward_breaks: bool = True  # Avoid breaking small sections

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheatSheetConfig":
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class CheatSheet:
    title: str
    hotkeys: List[Hotkey]
    config: CheatSheetConfig = None

    def __post_init__(self):
        if self.config is None:
            self.config = CheatSheetConfig(title=self.title)

    def get_sections(self) -> Dict[str, Dict[str, List[Hotkey]]]:
        sections = {}

        for hotkey in self.hotkeys:
            if hotkey.section not in sections:
                sections[hotkey.section] = {}

            subsection = hotkey.subsection or "General"
            if subsection not in sections[hotkey.section]:
                sections[hotkey.section][subsection] = []

            sections[hotkey.section][subsection].append(hotkey)

        return sections
