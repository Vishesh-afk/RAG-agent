import os
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"

import logging
import time
from pathlib import Path
from typing import Dict, Any, Tuple
from dataclasses import dataclass

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1" # Disable symlink warnings

@dataclass
class PDFExtractionConfig:
    """ PDF extraction configuration with GPU support"""
    enable_ocr: bool = True
    images_scale: float = 2.0
    include_images: bool = True
    include_tables: bool = True

class PDFExtractor:
    """ PDF content extractor using Docling with GPU support, without table extraction."""

    def __init__(self, config: PDFExtractionConfig = None):
        self.config = config or PDFExtractionConfig()
        self.setup_converter()

    def setup_converter(self):
        """Setup Docling document converter with options optimized for stability."""
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.config.enable_ocr
        # Disable heavy picture description model to prevent std::bad_alloc memory spikes on large PDFs
        pipeline_options.do_picture_description = False
        pipeline_options.do_table_structure = self.config.include_tables
        pipeline_options.images_scale = min(1.0, self.config.images_scale)
        try:
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )
        except Exception as e:
            logging.error(f"Failed to initialize docling: {e}")

    def _extract_with_pypdf(self, pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Fallback PDF extraction using pypdf for high stability."""
        import pypdf
        logger.info(f"Using pypdf fallback extraction for {pdf_path.name}")
        start_time = time.time()

        reader = pypdf.PdfReader(str(pdf_path))

        # Try to get a real title from PDF metadata first
        title = pdf_path.stem
        try:
            pdf_info = reader.metadata
            if pdf_info and pdf_info.title and pdf_info.title.strip():
                title = pdf_info.title.strip()
                logger.info(f"Using PDF metadata title (pypdf fallback): {title!r}")
        except Exception:
            pass

        extracted_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_text.append(f"## Page {i+1}\n\n{page_text}")

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
            "extraction_method": "pypdf_fallback",
            "content_type": "pdf"
        }
        return full_content, metadata

    def _extract_title_from_docling(self, doc, fallback: str) -> str:
        """
        Try to extract a meaningful document title from the Docling document.

        Priority:
        1. PDF metadata 'title' field (from the document properties / description)
        2. First title/section-header element found in the document body
        3. The provided fallback (filename stem)
        """
        # 1. Check PDF metadata stored by Docling under doc.description
        try:
            meta_title = getattr(doc, "description", None)
            if meta_title and hasattr(meta_title, "title") and meta_title.title:
                title = meta_title.title.strip()
                if title:
                    logger.info(f"Using PDF metadata title: {title!r}")
                    return title
        except Exception:
            pass

        # 2. Walk body items for the first heading / title element
        try:
            from docling_core.types.doc.labels import DocItemLabel
            title_labels = {DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER}
            for item, _ in doc.iterate_items():
                if getattr(item, "label", None) in title_labels:
                    text = item.text.strip() if hasattr(item, "text") else ""
                    if text:
                        logger.info(f"Using first heading as title: {text!r}")
                        return text
        except Exception:
            pass

        logger.info(f"No title found in document; using filename stem: {fallback!r}")
        return fallback

    def extract_pdf_content(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract content from a single PDF file using Docling, with automatic fallback."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Extracting content with Docling: {pdf_path.name}")
        start_time = time.time()

        try:
            result = self.converter.convert(str(pdf_path))
            end_time = time.time()

            doc = result.document
            content_text = doc.export_to_markdown()

            if not content_text or len(content_text.strip()) == 0:
                raise ValueError("Docling returned empty content")

            # Try to get a meaningful title; fall back to the filename stem
            title = self._extract_title_from_docling(doc, fallback=pdf_path.stem)

            metadata = {
                "source": str(pdf_path),
                "title": title,
                "filename": pdf_path.stem,
                "processing_time": round(end_time - start_time, 2),
                "pages": len(doc.pages),
                "texts": len(doc.texts),
                "pictures": len(doc.pictures),
                "tables": len(doc.tables),
                "extraction_method": "docling",
                "content_type": "pdf"
            }
            return content_text, metadata
        except Exception as e:
            logger.warning(f"Docling extraction failed for {pdf_path.name} ({e}), falling back to pypdf...")
            return self._extract_with_pypdf(pdf_path)


def create_pdf_extractor(config: PDFExtractionConfig = None) -> PDFExtractor:
    """Create PDF extractor instance"""
    return PDFExtractor(config)
