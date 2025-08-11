import congress_api_to_df.helpers as xx
import congress_api_to_df.clean_html as cc

import congress_api_to_df.df_from_xml as dd

class Bill:
    """
    Represents a bill with its metadata and content.

    Should store:
    - title
    - number
    - congress
    - type (e.g., "H.R.", "S.")
    - sponsor
    - subject
    - topics
    - text access URL
    - urls to related bills
    - committees
    - summary
    - legislative body content

    
    """

    def __init__(self, number, congress):
        self.number = number
        self.congress = congress
        self.data = self.get_df(number, congress) # one row data frame
        self.title = self.data['Title'].iloc[0] if 'Title' in self.data.columns else f"Bill {self.number} of {self.congress}th Congress"
        self.type = self.data['Type'].iloc[0] if 'Type' in self.data.columns else None
        self.sponsor = self.data['Sponsor'].iloc[0] if 'Sponsor' in self.data.columns else None
        self.subject = self.data['Subject'].iloc[0] if 'Subject' in self.data.columns else None
        self.topics = self.data['Topics'].iloc[0] if 'Topics' in self.data.columns else None
        self.text_access = self.data['Text Access'].iloc[0] if 'Text Access' in self.data.columns else None
        self.related_bills = self.data['Related Bills'].iloc[0] if 'Related Bills' in self.data.columns else None
        self.committees = self.data['Committees'].iloc[0] if 'Committees' in self.data.columns else None
        self.summary = self.get_summary(self.data)  # Assuming get_summary is a function that extracts summary from the data
        self.content = Content(self) # create a Content object for this bill
        self.url = self.get_url()

    def get_url(self):
        url = self.data['Text Access'].iloc[0] if 'Text Access' in self.data.columns else None
        # if url:
        #     url += f"&api_key={API_KEY}"
        return url

    def get_df(self, number, congress):
        import pandas as pd
        path = f"by_congress/detailed_{congress}_laws_list.csv"

        # path = "detailed.csv"
        df = pd.read_csv(path)
        # Check if the columns exist
        if 'Number' not in df.columns or 'Congress' not in df.columns:
            raise ValueError(f"DataFrame does not contain 'Number' or 'Congress' columns. Check the file {path}.")
        
        print(f"\n\n\nSearching for bill {number} in {congress}th Congress...\n\n")

        # print(f"DataFrame columns: {df.columns.tolist()}\n\n")
        # print(f"List numbers: {df['Number'].tolist()}\n\n")
        # print("List congresses: ", df['Congress'].tolist())

        specific_row =  df[(df['Number'] == number) & (df['Congress'] == congress)]
        print(f"found it: {specific_row}")
        return specific_row

    def get_related_bills(self):
        if self.related_bills:

            bills = []

            for url in self.related_bills.split(','):

                parts = url.split('/')
                if 'bill' in parts:
                    index = parts.index('bill')
                    congress = parts[index + 1]
                    last = parts[index + 3]
                    num = last.split('?')[0] 
                    pair = (congress, num)
                    bills.append(pair)
            
            num = len(bills)
            return num, bills
        return 0, None
    
    def open_related_bills(self):
        """
        creates bill objects for each related bill
        """
        num_bills, bills = self.get_related_bills()
        if num_bills != 0:
            related_bills = []
            for congress, number in bills:
                try:
                    bill = Bill(number=int(number), congress=int(congress))
                    related_bills.append(bill)
                except Exception:
                    print(f"bill {number} is not in file")
                    continue
            return related_bills
        else:
            print("list is empty")
            return "No related bills found."


    def get_summary(self, data):
        summary = self.data['Summary'].iloc[0] if 'Summary' in self.data.columns else None
        if summary:
            return cc.clean_legislative_html(summary) 
        else:
            return "No summary available."
        
    def get_xml_tree(self):
        """
        Fetches the full text root of the bill from the text access URL.
        """
        if self.text_access:
            try:
                print(f"text access: {self.text_access}")
                tree = xx.get_tree_from_link(self.text_access, API_KEY)
                return tree
            except Exception as e:
                print(f"Error fetching text: {e}")
                return None
        else:
            print("No text access URL available.")
            return "No text access URL available."
        
    def get_xml_root(self):
        """
        Fetches the  root of the bill from the text access URL.
        """
        if self.text_access:
            try:
                root = xx.get_room_from_link(self.text_access, API_KEY)
                return root
            except Exception as e:
                print(f"Error fetching text: {e}")
                return None
        else:
            return "No text access URL available."
                
    def __repr__(self):
        return (f"{self.title}\n"
             f"{self.type} {self.number} - {self.congress}th Congress\n"
             f"Sponsor: {self.sponsor}\nSubject: {self.subject}\n"
             f"Topics: {self.topics}\n"
             f"Committees: {self.committees}\n\n")
             # f"Summary: {self.summary}\n"
             # f"Related Bills: {self.related_bills}\n"
             # f"Text Access: {self.text_access}\n"


class Content:
    """
    Represents the full text content of a bill/
    """

    def __init__(self, bill: Bill):
        self.bill = bill
        self.full_df = dd.clean_legis_xml(bill.get_xml_tree())
        self.sum_df = dd.parse_structured_summary(bill.summary)

    def __repr__(self):
        return f"Content for {self.bill.title}:\n{self.full_df.head()}\n\nSummary DataFrame:\n{self.sum_df.head()}"
    
    def save_to_csv(self):
        """
        Saves the content DataFrame to a CSV file.
        """
        self.full_df.to_csv(f"extra_docs/full_text_dfs/{self.bill.congress}-{self.bill.number}.csv", index=False)
        self.sum_df.to_csv(f"extra_docs/summary_dfs/{self.bill.congress}-{self.bill.number}.csv", index=False)
        print(f"Content saved to {self.bill.congress}-{self.bill.number}.csv")
        

if __name__ == "__main__":

    bill = Bill(number=957, congress=117)
    print(bill)
    print(bill.content)


    bill.content.save_to_csv()