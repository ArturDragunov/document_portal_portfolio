Instead of using fitz/PyMuPDF, we use PyPDFLoader from Langchain. This is essentially a wrapper over PyMUPDF. It adds one more step during that extraction.

Before for document comparison or document analysis, we fetched all data, prepared 1 big string and gave it to LLM.
For conversations, it's not a good approach -> you can't give all the data to LLM.
For that reason we PyPDFLoader extracts data and converts it into Document() object. Then depending on the question, we fetch only relevant Documents.