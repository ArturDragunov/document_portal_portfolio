# Testing code for document comparison using LLMs

import io
from pathlib import Path
from archive.src.document_compare.data_ingestion import DocumentIngestion
from archive.src.document_compare.document_comparator import DocumentComparatorLLM

# ---- Setup: Load local PDF files as if they were "uploaded" ---- #
def load_fake_uploaded_file(file_path: Path):
    """
    Simulates file uploads for testing/development purposes.
    
    Creates a fake "uploaded file" object by reading a local PDF file's raw bytes
    and wrapping them in io.BytesIO() to create a file-like object in memory.
    This mimics what happens when users upload files through web interfaces 
    (like Streamlit's st.file_uploader()), which return BytesIO objects.
    
    Allows testing PDF processing pipeline with local files that behave 
    like uploaded ones, without waiting for real user uploads.
    """
    return io.BytesIO(file_path.read_bytes())  # simulate .getbuffer()

# ---- Step 1: Save and combine PDFs ---- #
def test_compare_documents():
    ref_path = Path("C:\\Users\\Artur Dragunov\\Documents\\GIT\\document_portal\\data\\document_compare\\Long_Report_V1.pdf")
    act_path = Path("C:\\Users\\Artur Dragunov\\Documents\\GIT\\document_portal\\data\\document_compare\\Long_Report_V2.pdf")

    # Wrap them like Streamlit UploadedFile-style
    class FakeUpload:
        """
        Mimics Streamlit's UploadedFile interface for testing purposes.
        
        Streamlit's UploadedFile objects have a .getbuffer() method that returns 
        the raw bytes of the uploaded file. This class replicates that exact 
        interface - when something calls .getbuffer() on this fake upload object, 
        it returns the _buffer (the file's bytes) just like a real Streamlit 
        upload would.
        
        This allows using the same code for both real uploads and fake ones 
        during testing.
        """
        def __init__(self, file_path: Path):
            self.name = file_path.name
            self._buffer = file_path.read_bytes()
            # A method that reads a file's entire content as raw binary data (bytes).
            # Every file - whether it's a PDF, image, text file - is ultimately just a sequence of bytes on disk.
        def getbuffer(self): # → returns stored bytes when requested
            return self._buffer
            # Buffer: A temporary storage area in memory that holds data.
            # Think of it like a container that holds the file's bytes after they've been read from disk.

    # Instantiate
    comparator = DocumentIngestion()
    ref_upload = FakeUpload(ref_path)
    act_upload = FakeUpload(act_path)

    # *** Save files and combine ***
    # Save reference and actual PDF files in the session directory -> these are uploaded by users via UI
    ref_file, act_file = comparator.save_uploaded_files(ref_upload, act_upload) 
    # return ref_path, act_path
    
    # two PDFs are combined into 1 big text which then will be fed into LLM for comparison
    combined_text = comparator.combine_documents() # can handle more than 1 document!
    comparator.clean_old_sessions(keep_latest=3)

    print("\n Combined Text Preview (First 1000 chars):\n")
    print(combined_text[:1000])

    # ---- Step 2: Run LLM comparison ---- #
    llm_comparator = DocumentComparatorLLM()
    df = llm_comparator.compare_documents(combined_text)
    
    print("\n Comparison DataFrame:\n")
    print(df)

if __name__ == "__main__":
    test_compare_documents()