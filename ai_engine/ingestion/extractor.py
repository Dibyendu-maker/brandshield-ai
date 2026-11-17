from pathlib import Path

import docx
import pymupdf  # PyMuPDF
from PIL import Image


class DocumentExtractor:
    """Extracts text content and metadata from multiple document and media formats."""

    @staticmethod
    def extract_from_file(file_path: str) -> dict[str, any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext in [".txt", ".md", ".markdown"]:
            return DocumentExtractor._extract_text(path)
        elif ext == ".pdf":
            return DocumentExtractor._extract_pdf(path)
        elif ext in [".docx", ".doc"]:
            return DocumentExtractor._extract_docx(path)
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            return DocumentExtractor._extract_image_info(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_text(path: Path) -> dict[str, any]:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "format": path.suffix.lstrip("."),
            "text": content.strip(),
            "sections": [{"title": path.stem, "content": content.strip(), "page": 1}],
            "metadata": {"char_count": len(content), "filename": path.name},
        }

    @staticmethod
    def _extract_pdf(path: Path) -> dict[str, any]:
        doc = pymupdf.open(str(path))
        full_text = []
        sections = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            if page_text:
                full_text.append(page_text)
                sections.append(
                    {
                        "title": f"Page {page_idx + 1}",
                        "content": page_text,
                        "page": page_idx + 1,
                    }
                )

        combined = "\n\n".join(full_text)
        return {
            "format": "pdf",
            "text": combined,
            "sections": sections,
            "metadata": {
                "page_count": len(doc),
                "char_count": len(combined),
                "filename": path.name,
            },
        }

    @staticmethod
    def _extract_docx(path: Path) -> dict[str, any]:
        doc = docx.Document(str(path))
        paragraphs = []
        sections = []
        current_heading = "Introduction"
        current_content = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style.name.startswith("Heading"):
                if current_content:
                    sections.append(
                        {
                            "title": current_heading,
                            "content": "\n".join(current_content),
                            "page": 1,
                        }
                    )
                    current_content = []
                current_heading = text
            else:
                current_content.append(text)
            paragraphs.append(text)

        if current_content:
            sections.append(
                {
                    "title": current_heading,
                    "content": "\n".join(current_content),
                    "page": 1,
                }
            )

        combined = "\n\n".join(paragraphs)
        return {
            "format": "docx",
            "text": combined,
            "sections": sections
            if sections
            else [{"title": "Body", "content": combined, "page": 1}],
            "metadata": {
                "paragraph_count": len(paragraphs),
                "char_count": len(combined),
                "filename": path.name,
            },
        }

    @staticmethod
    def _extract_image_info(path: Path) -> dict[str, any]:
        with Image.open(path) as img:
            width, height = img.size
            img_format = img.format
            mode = img.mode

        return {
            "format": path.suffix.lstrip("."),
            "text": "",  # Visual content processed via vision module
            "sections": [],
            "metadata": {
                "filename": path.name,
                "width": width,
                "height": height,
                "image_format": img_format,
                "color_mode": mode,
            },
        }

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Intelligent semantic paragraph chunking."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # keep last element for overlap if possible
                current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
                current_len = sum(len(x) for x in current_chunk)

            current_chunk.append(p)
            current_len += p_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        if not chunks and text.strip():
            # Fallback character chunking for unbroken blocks
            words = text.split()
            step = 80
            for i in range(0, len(words), step):
                chunks.append(" ".join(words[i : i + step + 15]))

        return chunks
