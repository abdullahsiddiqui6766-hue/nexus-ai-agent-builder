from pathlib import Path
from pypdf import PdfReader


class DocumentLoader:
    """Extract text from supported PDF and TXT documents."""

    def __init__(
        self,
        max_file_size: int = 2 * 1024 * 1024,
        max_text_length: int = 100_000,
    ) -> None:
        if max_file_size < 1:
            raise ValueError("Maximum file size must be positive.")

        if max_text_length < 1:
            raise ValueError("Maximum text length must be positive.")

        self.max_file_size = max_file_size
        self.max_text_length = max_text_length

    def load(self, file_path: str | Path) -> str:
        """Load a PDF or TXT file and return its extracted text."""

        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError("The requested document was not found.")

        if path.suffix.lower() not in {".pdf", ".txt"}:
            raise ValueError("Only PDF and TXT files are supported.")

        if path.stat().st_size > self.max_file_size:
            raise ValueError("Document exceeds the maximum file size.")

        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8-sig")
        else:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")

            extracted = []

            for page in reader.pages:
                page_text = page.extract_text() or ""

                if page_text:
                    extracted.append(page_text)

                if sum(len(part) for part in extracted) > self.max_text_length:
                    raise ValueError("Extracted text exceeds the permitted limit.")

            text = "\n\n".join(extracted)

        text = text.strip()

        if len(text) > self.max_text_length:
            raise ValueError("Extracted text exceeds the permitted limit.")

        if not text:
            raise ValueError("No readable text was found in the document.")

        return text