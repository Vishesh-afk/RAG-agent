import logging
import time
from pathlib import Path
from typing import Dict, Any, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PDFExtractionConfig:
    """PDF extraction configuration."""
    # OCR / image / table flags kept for API compatibility — pypdf ignores them.
    # Re-enable docling (see optional section below) to make use of these.
    enable_ocr: bool = False
    images_scale: float = 1.0
    include_images: bool = False
    include_tables: bool = False


class PDFExtractor:
    """PDF content extractor using pypdf (pure-Python, zero heavy deps).

    Docling (PyTorch-based) has been removed from the default stack to keep
    the Docker image lean (~1.5 GB saved).  To re-enable it locally, install
    docling and set USE_DOCLING=1 in your environment — the code will pick it
    up automatically via the optional path below.
    """

    def __init__(self, config: PDFExtractionConfig = None):
        self.config = config or PDFExtractionConfig()

    # ------------------------------------------------------------------
    # Primary extraction — pypdf (pure Python, no ML deps)
    # ------------------------------------------------------------------

    def extract_pdf_content(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract content from a PDF file using pypdf."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting PDF content: {pdf_path.name}")
        return self._extract_with_pypdf(pdf_path)

    def _extract_with_pypdf(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from a PDF using pypdf."""
        import pypdf

        start_time = time.time()
        reader = pypdf.PdfReader(str(pdf_path))

        # --- title: PDF metadata → first non-empty page heading → filename ---
        title = self._extract_title_pypdf(reader, pdf_path.stem)

        extracted_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_text.append(f"## Page {i + 1}\n\n{page_text}")

        full_content = "\n\n".join(extracted_text)
        end_time = time.time()

        metadata = {
            "source": str(pdf_path),
            "title": title,
            "filename": pdf_path.stem,
            "processing_time": round(end_time - start_time, 2),
            "pages": len(reader.pages),
            "texts": len(extracted_text),
            "pictures": 0,
            "tables": 0,
            "extraction_method": "pypdf",
            "content_type": "pdf",
        }
        return full_content, metadata

    @staticmethod
    def _extract_title_pypdf(reader, fallback: str) -> str:
        """Return the best available title from a pypdf PdfReader."""
        # 1. PDF metadata /Title field
        try:
            info = reader.metadata
            if info and getattr(info, "title", None) and info.title.strip():
                title = info.title.strip()
                logger.info(f"Using PDF metadata title: {title!r}")
                return title
        except Exception:
            pass

        # 2. First non-trivially-short line of page 1 that looks like a heading
        try:
            first_page_text = reader.pages[0].extract_text() or ""
            for line in first_page_text.splitlines():
                line = line.strip()
                if 4 <= len(line) <= 120:
                    logger.info(f"Using first page heading as title: {line!r}")
                    return line
        except Exception:
            pass

        logger.info(f"No title found; using filename stem: {fallback!r}")
        return fallback


# ---------------------------------------------------------------------------
# Optional: Docling-based extractor (heavy — requires `pip install docling`)
# Set USE_DOCLING=1 in your environment to activate.
# ---------------------------------------------------------------------------

def _try_docling_extract(pdf_path: Path, config: PDFExtractionConfig) -> Tuple[str, Dict[str, Any]] | None:
    """
    Attempt extraction with Docling (AI-based layout parser).
    Returns None if docling is not installed.
    """
    import os
    if not os.getenv("USE_DOCLING"):
        return None

    try:
        import os as _os
        _os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
        _os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = config.enable_ocr
        pipeline_options.do_picture_description = False
        pipeline_options.do_table_structure = config.include_tables
        pipeline_options.images_scale = min(1.0, config.images_scale)

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        start_time = time.time()
        result = converter.convert(str(pdf_path))
        doc = result.document
        content_text = doc.export_to_markdown()

        if not content_text or not content_text.strip():
            return None

        # Title extraction
        title = pdf_path.stem
        try:
            meta_title = getattr(doc, "description", None)
            if meta_title and getattr(meta_title, "title", None) and meta_title.title.strip():
                title = meta_title.title.strip()
        except Exception:
            pass

        if title == pdf_path.stem:
            try:
                from docling_core.types.doc.labels import DocItemLabel
                for item, _ in doc.iterate_items():
                    if getattr(item, "label", None) in {DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER}:
                        text = getattr(item, "text", "").strip()
                        if text:
                            title = text
                            break
            except Exception:
                pass

        return content_text, {
            "source": str(pdf_path),
            "title": title,
            "filename": pdf_path.stem,
            "processing_time": round(time.time() - start_time, 2),
            "pages": len(doc.pages),
            "texts": len(doc.texts),
            "pictures": len(doc.pictures),
            "tables": len(doc.tables),
            "extraction_method": "docling",
            "content_type": "pdf",
        }

    except ImportError:
        logger.warning("USE_DOCLING=1 set but docling is not installed — falling back to pypdf.")
        return None
    except Exception as e:
        logger.warning(f"Docling extraction failed ({e}) — falling back to pypdf.")
        return None


def create_pdf_extractor(config: PDFExtractionConfig = None) -> PDFExtractor:
    """Create a PDF extractor instance."""
    return PDFExtractor(config)
