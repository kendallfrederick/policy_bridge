import pandas as pd
import helpers as xx
import clean_html as cc
from bill_class import Bill

API_KEY = 'qo7lPHj8lcYm7TK9tEGascFIhm1cWqeZ9PJyxPEh'

class Content:
    def __init__(self, aligned_data: dict):
        """
        aligned_data should be a dictionary structured like:
        {
            "TITLE I": {
                "summary": "Summary text...",
                "full_text": "Full bill text..."
            },
            ...
        }
        """
        self.aligned_data = aligned_data
        self.titles = list(aligned_data.keys())

    def create_sections(self):
        """Print all titles with their associated summary and full text."""
        for title in self.titles:
            print(f"\n=== {title} ===")
            print("\n-- Summary --")
            print(self.aligned_data[title].get("summary", "[No summary]"))
            print("\n-- Full Text --")
            print(self.aligned_data[title].get("full_text", "[No full text]"))

    def get_by_title(self, title_label):
        """Return and print summary and full text for a given TITLE (e.g., 'I')."""
        title_key = f"TITLE {title_label.upper()}"
        if title_key in self.aligned_data:
            summary = self.aligned_data[title_key].get("summary", "[No summary]")
            full_text = self.aligned_data[title_key].get("full_text", "[No full text]")
            print(f"\n=== {title_key} ===")
            print("\n-- Summary --")
            print(summary)
            print("\n-- Full Text --")
            print(full_text)
            return {"summary": summary, "full_text": full_text}
        else:
            print(f"[Error] Title '{title_label}' not found in the document.")
            return None

    

# bill = Bill(number=5376, congress=117)
# # 3684: biparisan infrastructure bill
# # 5376: Inflation Reduction Act
# print(bill)
# tree = bill.get_text_root()

# aligned_data = cc.clean_legislative_xml(tree, bill.summary)

# titles = aligned_data.keys()
# print(titles)

# title2 = aligned_data['TITLE IV']
# print(title2.keys())
# subtitles = title2['summary'].keys()

# bill = Bill(number=5376, congress=117)
# tree = bill.get_text_root()

# aligned_data = cc.clean_legislative_xml(tree, bill.summary)

# content = Content(aligned_data)

# # content.create_sections()         # Print all
# content.get_by_title('IV')         # Get one
#print(content.list_titles())      # ['TITLE I', 'TITLE II', ...]
