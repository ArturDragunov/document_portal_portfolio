import sys
import uuid
from pathlib import Path
import fitz # manipulating with PDF files (read/extract)
from datetime import datetime, timezone
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException


class DocumentIngestion:
    """
    Handles saving, reading, and combining of PDFs for comparison with session-based versioning.
    """

    def __init__(self, base_dir: str = "data/document_compare", session_id=None):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir) # base directory from where to fetch data
        self.session_id = session_id or f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True) # create a folder for data comparison (if parent folders not exist -> create them as well)

        self.log.info("DocumentComparator initialized", session_path=str(self.session_path))
    def delete_existing_files(self):
            """
            Deletes existing files at the specified paths. It deletes all the files inside the folder.
            Better solution would be to recreate a folder instead.
            """
            try:
                if self.base_dir.exists() and self.base_dir.is_dir():
                    for file in self.base_dir.iterdir():
                        if file.is_file():
                            file.unlink() # unlink means to delete
                            self.log.info("File deleted", path=str(file))
                    self.log.info("Directory cleaned", directory=str(self.base_dir))
            except Exception as e:
                self.log.error(f"Error deleting existing files: {e}")
                raise DocumentPortalException("An error occurred while deleting existing files.", sys)
    def save_uploaded_files(self, reference_file, actual_file):
        """
        Save reference and actual PDF files in the session directory.
        """
        try:
            # self.delete_existing_files() -> not needed anymore as we use sessions
            # self.log.info('Existing files deleted successfully.')
            ref_path = self.session_path / reference_file.name # first version of the file
            act_path = self.session_path / actual_file.name # updated file

            if not reference_file.name.lower().endswith(".pdf") or not actual_file.name.lower().endswith(".pdf"):
                raise ValueError("Only PDF files are allowed.")

            with open(ref_path, "wb") as f:
                f.write(reference_file.getbuffer())
                # f.write(reference_file)  # Can't write a file object directly -> check getbuffer_explained.md for explanation

            with open(act_path, "wb") as f:
                f.write(actual_file.getbuffer())

            self.log.info("Files saved", reference=str(ref_path), actual=str(act_path), session=self.session_id)
            return ref_path, act_path

        except Exception as e:
            self.log.error("Error saving PDF files", error=str(e), session=self.session_id)
            raise DocumentPortalException("Error saving files", sys)

    def read_pdf(self, pdf_path: Path) -> str:
        """
        Read text content of a PDF page-by-page. Scanned PDF won't work here. For that we need OCR.
        """
        try:
            with fitz.open(pdf_path) as doc:
                # Encryption means converting a document into a coded format to prevent unauthorized access.
                # It transforms readable information (plaintext) into an unreadable format (ciphertext) using an algorithm and a key,
                # ensuring only those with the correct key can decode and read the document. 
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}") # we can't process it

                all_text = []
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num) # thanks to fitz, we have these in-build methods available
                    text = page.get_text()  # type: ignore
                    if text.strip(): # Empty string or string with only whitespace → False
                        all_text.append(f"\n --- Page {page_num + 1} --- \n{text}")
                    # "   hello   ".strip()  # returns "hello"
                    # "   \n\t   ".strip()   # returns "" (empty string)
                    # "".strip()             # returns "" (empty string)

            self.log.info("PDF read successfully", file=str(pdf_path), pages=len(all_text))
            return "\n".join(all_text) # we join all pages using new sentence \n sign

        except Exception as e:
            self.log.error("Error reading PDF", file=str(pdf_path), error=str(e))
            raise DocumentPortalException("Error reading PDF", sys)

    def combine_documents(self) -> str:
        """
        Combine content of all PDFs in session folder into a single string.
        """
        try:
            doc_parts = []
            for file in sorted(self.session_path.iterdir()):
                if file.is_file() and file.suffix.lower() == ".pdf":
                    content = self.read_pdf(file) # reads pdf page by page and it combines these pages to a single string
                    doc_parts.append(f"Document: {file.name}\n{content}")

            combined_text = "\n\n".join(doc_parts)
            self.log.info("Documents combined", count=len(doc_parts), session=self.session_id)
            return combined_text

        except Exception as e:
            self.log.error("Error combining documents", error=str(e), session=self.session_id)
            raise DocumentPortalException("Error combining documents", sys)

    def clean_old_sessions(self, keep_latest: int = 3):
        """
        Optional method to delete older session folders, keeping only the latest N.
        """
        try:
            session_folders = sorted(
                [f for f in self.base_dir.iterdir() if f.is_dir()],
                reverse=True
            )
            for folder in session_folders[keep_latest:]:
                for file in folder.iterdir():
                    file.unlink()
                folder.rmdir()
                self.log.info("Old session folder deleted", path=str(folder))

        except Exception as e:
            self.log.error("Error cleaning old sessions", error=str(e))
            raise DocumentPortalException("Error cleaning old sessions", sys)