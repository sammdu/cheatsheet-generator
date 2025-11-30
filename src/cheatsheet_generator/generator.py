"""PDF generator for cheat sheets."""

import math
from pathlib import Path
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import BaseDocTemplate

from cheatsheet_generator.models import CheatSheet, Hotkey


class ConditionalSpacer(Flowable):
    """A spacer that only adds space if not at the top of a frame."""

    def __init__(self, height, frame_height, total_frame_padding_vertical):
        Flowable.__init__(self)
        self.height = height
        self.frame_height = frame_height
        self.total_frame_padding_vertical = total_frame_padding_vertical

    def wrap(self, availWidth, availHeight):
        """Calculate the space needed - return 0 if at frame top."""
        # Frame has vertical padding, so actual available = frame_height - total_padding
        # If availHeight is close to this value, we're at frame top
        expected_available_at_top = (
            self.frame_height - self.total_frame_padding_vertical
        )

        # Use 95% threshold to detect frame top, accounting for rounding
        threshold_percentage = 0.95
        if availHeight >= expected_available_at_top * threshold_percentage:
            return (availWidth, 0)  # Skip spacing at frame top
        return (availWidth, self.height)  # Add spacing elsewhere

    def draw(self):
        """Nothing to draw."""
        pass


class PDFGenerator:
    """Generates PDF cheat sheets from CheatSheet objects."""

    # Layout constants
    COLUMN_SPACING = 15
    FRAME_PADDING_TOP = 6
    FRAME_PADDING_BOTTOM = 6
    FRAME_PADDING_LEFT = 3
    FRAME_PADDING_RIGHT = 3

    # Border constants
    SECTION_BORDER_WIDTH = 1

    def __init__(self, cheat_sheet: CheatSheet):
        """Initialize the PDF generator."""
        self.cheat_sheet = cheat_sheet
        self.config = cheat_sheet.config

        # Calculate derived font sizes
        self.title_font_size = self.config.header_font_size + 3
        self.section_header_font_size = self.config.header_font_size + 1
        self.subsection_header_font_size = self.config.font_size + 1

        # Calculate derived spacing values
        self.title_line_height = self.title_font_size * 1.25
        self.title_space_after = 12
        self.section_header_line_height = self.section_header_font_size
        self.section_header_space_after = 8

        # Calculate section header padding for visual centering
        # All-caps text needs less top padding, more bottom padding
        self.section_header_padding_top = 2
        self.section_header_padding_right = 3
        self.section_header_padding_bottom = 6
        self.section_header_padding_left = 3

        # Calculate total frame padding (used for ConditionalSpacer)
        self.total_frame_padding_vertical = (
            self.FRAME_PADDING_TOP + self.FRAME_PADDING_BOTTOM
        )

        self.styles = self._create_styles()

    def _get_page_size(self) -> Tuple[float, float]:
        """Get the page size based on configuration."""
        # Select base paper size
        if self.config.paper_size.lower() == "a4":
            base_size = A4
        else:  # default to letter
            base_size = LETTER

        # Apply orientation
        if self.config.orientation.lower() == "landscape":
            return landscape(base_size)
        else:  # default to portrait
            return base_size

    def _create_styles(self) -> dict:
        """Create paragraph styles for the PDF."""
        styles = getSampleStyleSheet()

        # Subsection header spacing constants
        subsection_space_after = 3
        subsection_space_before = 5
        subsection_left_indent = 8

        # Hotkey style spacing
        hotkey_space_after = 1

        custom_styles = {
            "title": ParagraphStyle(
                "title",
                parent=styles["Heading1"],
                fontSize=self.title_font_size,
                textColor=colors.black,
                alignment=TA_CENTER,
                spaceAfter=self.title_space_after,
                fontName="Helvetica-Bold",
                leading=self.title_line_height,
            ),
            "section_header": ParagraphStyle(
                "section_header",
                parent=styles["Heading2"],
                fontSize=self.section_header_font_size,
                textColor=colors.white,
                alignment=TA_CENTER,
                spaceAfter=0,  # Spacing handled by explicit Spacer
                spaceBefore=0,  # Spacing handled by ConditionalSpacer
                leftIndent=0,
                rightIndent=0,
                fontName="Helvetica-Bold",
                borderWidth=self.SECTION_BORDER_WIDTH,
                borderColor=colors.black,
                # All-caps text sits on baseline with unused descender space below
                # Need MORE bottom padding to compensate and center the text
                borderPadding=(
                    self.section_header_padding_top,
                    self.section_header_padding_right,
                    self.section_header_padding_bottom,
                    self.section_header_padding_left,
                ),
                backColor=colors.black,
                leading=self.section_header_line_height,
            ),
            "subsection_header": ParagraphStyle(
                "subsection_header",
                parent=styles["Heading3"],
                fontSize=self.subsection_header_font_size,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=subsection_space_after,
                spaceBefore=subsection_space_before,
                leftIndent=subsection_left_indent,
                fontName="Helvetica-Bold",
            ),
            "hotkey": ParagraphStyle(
                "hotkey",
                parent=styles["Normal"],
                fontSize=self.config.font_size,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=hotkey_space_after,
                leftIndent=0,
                fontName="Helvetica",
            ),
        }

        return custom_styles

    def _calculate_layout(self) -> Tuple[float, float]:
        """Calculate column width and usable page dimensions."""
        page_width, page_height = self._get_page_size()
        usable_width = page_width - (2 * self.config.margin)
        usable_height = page_height - (2 * self.config.margin)

        total_column_spacing = (self.config.columns - 1) * self.COLUMN_SPACING
        column_width = (usable_width - total_column_spacing) / self.config.columns

        return column_width, usable_height

    def _create_hotkey_table(self, hotkeys: List[Hotkey]) -> Table:
        """Create a table for hotkeys."""
        if not hotkeys:
            return None

        # Table layout constants
        key_column_percentage = 0.35
        desc_column_percentage = 0.65

        # Table cell padding
        cell_bottom_padding = 1
        cell_top_padding = 1
        cell_left_padding = 3
        cell_right_padding = 3

        # Separator line width
        separator_line_width = 0.25

        column_width, _ = self._calculate_layout()

        data = []
        for hotkey in hotkeys:
            from xml.sax.saxutils import escape

            escaped_key = escape(hotkey.key)
            escaped_desc = escape(hotkey.description)

            key_text = f"<font name='Courier-Bold'>{escaped_key}</font>"
            desc_text = escaped_desc

            data.append(
                [
                    Paragraph(key_text, self.styles["hotkey"]),
                    Paragraph(desc_text, self.styles["hotkey"]),
                ]
            )

        key_width = column_width * key_column_percentage
        desc_width = column_width * desc_column_percentage

        table = Table(data, colWidths=[key_width, desc_width])
        table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), self.config.font_size),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), cell_bottom_padding),
                    ("TOPPADDING", (0, 0), (-1, -1), cell_top_padding),
                    ("LEFTPADDING", (0, 0), (-1, -1), cell_left_padding),
                    ("RIGHTPADDING", (0, 0), (-1, -1), cell_right_padding),
                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -2),
                        separator_line_width,
                        colors.lightgrey,
                    ),
                ]
            )
        )

        return table

    def _count_section_items(self, subsections: dict) -> int:
        """Count total items in a section."""
        total = 0
        for hotkeys in subsections.values():
            total += len(hotkeys)
        return total

    def _get_actual_frame_height(self) -> float:
        """Get the actual frame height used in the document."""
        page_size = self._get_page_size()
        _, page_height = page_size
        usable_height = page_height - 2 * self.config.margin

        if self.config.fill_top_half:
            # In fill_top_half mode, frames are half height with margin between
            return (usable_height - self.config.margin) / 2
        else:
            # Standard mode uses full height
            return usable_height

    def _build_content(self) -> List:
        """Build the content for the PDF."""
        content = []

        title = Paragraph(self.cheat_sheet.title, self.styles["title"])
        content.append(title)
        content.append(Spacer(1, 12))

        sections = self.cheat_sheet.get_sections()

        # Calculate actual frame height for ConditionalSpacer
        # Must account for fill_top_half mode
        frame_height = self._get_actual_frame_height()

        # Section breaking thresholds
        large_section_threshold = 200  # Height above which to break by subsections
        small_section_threshold = 100  # Height below which to keep together
        min_items_for_breaking = 3  # Minimum items to consider breaking

        section_items = []
        first_section = True

        for section_name, subsections in sections.items():
            section_height = self._estimate_section_height(subsections)
            total_items = self._count_section_items(subsections)

            section_content = []

            # Create spacing element before section
            # Skip for first section after title
            section_spacing_element = None
            if not first_section:
                if self.config.section_align_flush:
                    section_spacing_element = ConditionalSpacer(
                        self.config.section_spacing,
                        frame_height,
                        self.total_frame_padding_vertical,
                    )
                else:
                    section_spacing_element = Spacer(1, self.config.section_spacing)
                section_content.append(section_spacing_element)
            first_section = False

            section_header_text = f"<b>{section_name.upper()}</b>"
            section_header = Paragraph(
                section_header_text, self.styles["section_header"]
            )
            section_content.append(section_header)
            section_content.append(Spacer(1, self.section_header_space_after))

            for subsection_name, hotkeys in subsections.items():
                if subsection_name != "General":
                    subsection_header_text = f"<i>{subsection_name}</i>"
                    subsection_header = Paragraph(
                        subsection_header_text, self.styles["subsection_header"]
                    )
                    section_content.append(subsection_header)

                table = self._create_hotkey_table(hotkeys)
                if table:
                    section_content.append(table)
                    section_content.append(Spacer(1, self.config.subsection_spacing))

            # Apply section_no_awkward_breaks logic
            if self.config.section_no_awkward_breaks:
                # If section has fewer than minimum items, keep it together
                if total_items < min_items_for_breaking:
                    section_items.append(KeepTogether(section_content))
                # If section is very large, break it up by subsections
                elif section_height > large_section_threshold:
                    for i, (subsection_name, hotkeys) in enumerate(subsections.items()):
                        if i == 0:
                            # First subsection includes section header
                            subsection_content = [
                                section_header,
                                Spacer(1, self.section_header_space_after),
                            ]
                        else:
                            subsection_content = []

                        if subsection_name != "General":
                            subsection_header_text = f"<i>{subsection_name}</i>"
                            subsection_header = Paragraph(
                                subsection_header_text, self.styles["subsection_header"]
                            )
                            subsection_content.append(subsection_header)

                        table = self._create_hotkey_table(hotkeys)
                        if table:
                            subsection_content.append(table)
                            subsection_content.append(
                                Spacer(1, self.config.subsection_spacing)
                            )

                        if len(subsection_content) > 0:
                            section_items.append(KeepTogether(subsection_content))
                # Medium sections, keep together if small enough
                elif section_height < small_section_threshold:
                    section_items.append(KeepTogether(section_content))
                else:
                    # Medium/large sections: keep header with first subsection
                    # Also keep subsection header with content
                    first_subsection = True
                    header_with_first = []

                    for subsection_name, hotkeys in subsections.items():
                        subsection_content = []

                        if first_subsection:
                            # Include section spacing and header with first subsection
                            if section_spacing_element:
                                header_with_first.append(section_spacing_element)
                            header_with_first.append(section_header)
                            header_with_first.append(
                                Spacer(1, self.section_header_space_after)
                            )
                            first_subsection = False

                        if subsection_name != "General":
                            subsection_header_text = f"<i>{subsection_name}</i>"
                            subsection_header = Paragraph(
                                subsection_header_text, self.styles["subsection_header"]
                            )
                            subsection_content.append(subsection_header)

                        table = self._create_hotkey_table(hotkeys)
                        if table:
                            subsection_content.append(table)
                            subsection_content.append(
                                Spacer(1, self.config.subsection_spacing)
                            )

                        if len(header_with_first) > 0:
                            # First subsection: keep with section header
                            header_with_first.extend(subsection_content)
                            section_items.append(KeepTogether(header_with_first))
                            header_with_first = []
                        else:
                            # Subsequent subsections: keep header with table
                            if len(subsection_content) > 0:
                                section_items.append(KeepTogether(subsection_content))
            else:
                # Original logic without awkward break prevention
                # Still prevent orphaned headers
                if section_height > large_section_threshold:
                    for i, (subsection_name, hotkeys) in enumerate(subsections.items()):
                        if i == 0:
                            # First subsection includes section header
                            subsection_content = [
                                section_header,
                                Spacer(1, self.section_header_space_after),
                            ]
                        else:
                            subsection_content = []

                        if subsection_name != "General":
                            subsection_header_text = f"<i>{subsection_name}</i>"
                            subsection_header = Paragraph(
                                subsection_header_text, self.styles["subsection_header"]
                            )
                            subsection_content.append(subsection_header)

                        table = self._create_hotkey_table(hotkeys)
                        if table:
                            subsection_content.append(table)
                            subsection_content.append(
                                Spacer(1, self.config.subsection_spacing)
                            )

                        if len(subsection_content) > 0:
                            section_items.append(KeepTogether(subsection_content))

                elif section_height < small_section_threshold:
                    section_items.append(KeepTogether(section_content))
                else:
                    # Keep header with first subsection to prevent orphaning
                    # Also keep each subsection header with its content
                    first_subsection = True
                    header_with_first = []

                    for subsection_name, hotkeys in subsections.items():
                        subsection_content = []

                        if first_subsection:
                            # Include section spacing and header with first subsection
                            if section_spacing_element:
                                header_with_first.append(section_spacing_element)
                            header_with_first.append(section_header)
                            header_with_first.append(
                                Spacer(1, self.section_header_space_after)
                            )
                            first_subsection = False

                        if subsection_name != "General":
                            subsection_header_text = f"<i>{subsection_name}</i>"
                            subsection_header = Paragraph(
                                subsection_header_text, self.styles["subsection_header"]
                            )
                            subsection_content.append(subsection_header)

                        table = self._create_hotkey_table(hotkeys)
                        if table:
                            subsection_content.append(table)
                            subsection_content.append(
                                Spacer(1, self.config.subsection_spacing)
                            )

                        if len(header_with_first) > 0:
                            header_with_first.extend(subsection_content)
                            section_items.append(KeepTogether(header_with_first))
                            header_with_first = []
                        else:
                            # Subsequent subsections: keep header with table
                            if len(subsection_content) > 0:
                                section_items.append(KeepTogether(subsection_content))

        content.extend(section_items)
        return content

    def _estimate_section_height(self, subsections: dict) -> float:
        """Estimate the height needed for a section."""
        # Height estimation constants
        section_header_spacing_estimate = 15
        subsection_header_spacing_estimate = 8

        total_height = 0

        # Section header height
        section_header_height = (
            self.config.header_font_size + section_header_spacing_estimate
        )
        total_height += section_header_height

        # Subsections height
        for subsection_name, hotkeys in subsections.items():
            if subsection_name != "General":
                subsection_header_height = (
                    self.config.font_size + subsection_header_spacing_estimate
                )
                total_height += subsection_header_height

            hotkeys_height = len(hotkeys) * self.config.row_height
            total_height += hotkeys_height
            total_height += self.config.subsection_spacing

        total_height += self.config.section_spacing

        return total_height

    def generate(self, output_path: Path) -> None:
        """Generate the PDF cheat sheet."""
        doc = self._create_multicolumn_doc(output_path)
        content = self._build_content()
        doc.build(content)

    def _create_multicolumn_doc(self, output_path: Path) -> BaseDocTemplate:
        """Create a multi-column document template."""
        page_size = self._get_page_size()
        doc = BaseDocTemplate(
            str(output_path),
            pagesize=page_size,
            topMargin=self.config.margin,
            bottomMargin=self.config.margin,
            leftMargin=self.config.margin,
            rightMargin=self.config.margin,
        )

        page_width, page_height = page_size

        # Calculate frame dimensions
        total_horizontal_margin = 2 * self.config.margin
        total_column_spacing = (self.config.columns - 1) * self.COLUMN_SPACING
        frame_width = (
            page_width - total_horizontal_margin - total_column_spacing
        ) / self.config.columns

        # Frame boundary display (0=hide, 1=show)
        show_frame_boundary = 0

        frames = []

        if self.config.fill_top_half:
            # 2-row layout: top half fills first, then bottom half
            # Calculate frame height for 2 rows with margin between them
            usable_height = page_height - total_horizontal_margin
            rows_count = 2
            frame_height = (usable_height - self.config.margin) / rows_count

            # Create top row frames (left to right)
            for i in range(self.config.columns):
                x = self.config.margin + i * (frame_width + self.COLUMN_SPACING)
                # Top row starts from the top
                y = self.config.margin + frame_height + self.config.margin
                frame = Frame(
                    x,
                    y,
                    frame_width,
                    frame_height,
                    leftPadding=self.FRAME_PADDING_LEFT,
                    rightPadding=self.FRAME_PADDING_RIGHT,
                    topPadding=self.FRAME_PADDING_TOP,
                    bottomPadding=self.FRAME_PADDING_BOTTOM,
                    showBoundary=show_frame_boundary,
                )
                frames.append(frame)

            # Create bottom row frames (left to right)
            for i in range(self.config.columns):
                x = self.config.margin + i * (frame_width + self.COLUMN_SPACING)
                # Bottom row
                y = self.config.margin
                frame = Frame(
                    x,
                    y,
                    frame_width,
                    frame_height,
                    leftPadding=self.FRAME_PADDING_LEFT,
                    rightPadding=self.FRAME_PADDING_RIGHT,
                    topPadding=self.FRAME_PADDING_TOP,
                    bottomPadding=self.FRAME_PADDING_BOTTOM,
                    showBoundary=show_frame_boundary,
                )
                frames.append(frame)
        else:
            # Standard single-row layout
            frame_height = page_height - total_horizontal_margin
            for i in range(self.config.columns):
                x = self.config.margin + i * (frame_width + self.COLUMN_SPACING)
                frame = Frame(
                    x,
                    self.config.margin,
                    frame_width,
                    frame_height,
                    leftPadding=self.FRAME_PADDING_LEFT,
                    rightPadding=self.FRAME_PADDING_RIGHT,
                    topPadding=self.FRAME_PADDING_TOP,
                    bottomPadding=self.FRAME_PADDING_BOTTOM,
                    showBoundary=show_frame_boundary,
                )
                frames.append(frame)

        template = PageTemplate(id="multicolumn", frames=frames)
        doc.addPageTemplates([template])

        return doc

    def estimate_pages(self) -> int:
        """Estimate the number of pages needed."""
        _, usable_height = self._calculate_layout()

        total_hotkeys = len(self.cheat_sheet.hotkeys)
        sections = self.cheat_sheet.get_sections()

        # Estimation constants
        title_height_estimate = 30
        section_header_height_estimate = 15
        subsection_header_height_estimate = 12
        min_pages = 1

        # Calculate component heights
        title_height = title_height_estimate
        section_headers_height = len(sections) * section_header_height_estimate
        total_subsections = sum(len(subsections) for subsections in sections.values())
        subsection_headers_height = (
            total_subsections * subsection_header_height_estimate
        )
        hotkey_height = total_hotkeys * self.config.row_height
        spacing_height = len(sections) * self.config.section_spacing

        # Sum all heights
        total_height = (
            title_height
            + section_headers_height
            + subsection_headers_height
            + hotkey_height
            + spacing_height
        )

        # Distribute across columns
        effective_height = total_height / self.config.columns

        # Calculate number of pages needed
        pages = math.ceil(effective_height / usable_height)
        return max(min_pages, pages)
