### Files in Bill Processing Folder

(it got messy fast)

1. **scrape.py**: this is where i started playing around with the congress api. doesn't produce an organized output

2. **pull_laws.py**: produced the original laws_list csv with data from every bill that became law in the 117th and 118th congress. then added functions to get summaries, committees, subjects, and related bills to add to a huuuuuge csv file. these files make it easy to access info about the bills -- link to xml text alongside other fields.

3. **api_client.py**: doesn't need to be touched, but called every time i use the congress api key to establish the client

4. **udpate_csv.py**: used this to add sponsor and subject to the csv without remaking it before i added the related bills and other more helpful stuff

5. **visuals.py**: right now it just reads in the csv and makes a cute pie chart of the different topics. helped me figure out which subjects to split off into their own filtered files.

6. **split_by_subject.py**: create new csv files for different categories of bills. i wonder if i should try filtering for bills that have an empty related bills section (meaning its not an amendment)

7. **tokens.py**: tiktoken used to count the number of tokens in the text file. has a neaten() function that gives the txt file contents to ollama and tells it to fix formatting. has been known to hallucinate... working on it.

8. **helpers.py**: xml processing functions because the congress api is so annoying. one call returns xml with a link to more xml that has a link to the xml i actually want. bleh. but this file helpers make it easier. 

    * get_xml_from_link(url, api_key=None) --> returns the xml root 
    * print_clean_xml(elem, level=0)
    * get_url_from_text_versions(root) --> returns dictionary with 'full text' as key and value that's the xml link

9. **process.py**: process_bill function cleans the xml (just gets the legis-body contents) and removes a lot of tags. still comes out pretty messy with newlines and indents that come from the congress api structure. saves the output to a txt file. also has helper functions that print xml tags and whatnot that i used when writing the main function.

10. **bill_class.py**: creates and prints a bill object! next step is to get it to store sections of the action text of the bill.

11. **clean_html.py**: helper function to clean the html summary with *beautiful soup*. probably should have done this before storing the summaries in the csv. or should just filter to only useful categories because some fo the military ones are really long. 

12. **claimify.py**: drafting chain prompts to extract claims. playing around with prompt engineering.

13. **df_from_xml.py**: 