from pypdf import PdfReader
from urllib.request import urlopen, Request
from io import BytesIO
from datetime import datetime

class Report:

    def __init__(self, subject, id):
        self.id = id
        self.data = get_df(subject, id) # one row data frame
        self.title = self.data['title'].iloc[0] 
        self.date = datetime.fromisoformat(self.data['date'].iloc[0]).date()
        self.update = datetime.fromisoformat(self.data['update'].iloc[0]).date()
        self.pdf = self.data['pdf'].iloc[0]
        self.summary = self.data['summary'].iloc[0]

    def __repr__(self):
        return (f"{self.title}\n"
             f"{self.id} published {self.date}\n"
             f"updated on {self.update}\n"
             f"Summary: {self.summary}\n"
             f"PDF: {self.pdf}\n\n")
    
def get_df(subject, id):
    import pandas as pd
    path = f"congress_api_to_df/crs/{subject}.csv"

    df = pd.read_csv(path)
    if 'id' not in df.columns:
        raise ValueError(f"DataFrame does not contain 'id' columns. Check the file {path}.")
    specific_row = df[df['id'] == id]
    return specific_row

def remote_pdf_reader(url):
    try:
        # Create a Request object to include headers if necessary (e.g., User-Agent)
        req = Request(url)
        
        # Open the URL and read the content
        with urlopen(req) as remote_file:
            remote_pdf_content = remote_file.read()

        # Create a BytesIO object to treat the content as a file
        memory_file = BytesIO(remote_pdf_content)

        # Create a PdfReader object from the BytesIO object
        reader = PdfReader(memory_file)
        return reader

    except Exception as e:
        print(f"Error processing PDF from URL: {e}")
        return None
    
if __name__ == "__main__":
    
    report = Report('R47583')
    print(report)

    reader = remote_pdf_reader(report.pdf)
    number_of_pages = len(reader.pages)
    page = reader.pages[3]
    text = page.extract_text()

    print(f"num pages: {number_of_pages}")
    print(text)

    import webbrowser
    webbrowser.open(report.pdf)

    