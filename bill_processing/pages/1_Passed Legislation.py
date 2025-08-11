import streamlit as st
import warnings

def main():

    import st_helpers.bill_get as bb
    import st_helpers.article_step as aa
    import st_helpers.claims_step as cc

    # Or suppress warnings matching a text pattern
    warnings.filterwarnings("ignore", message="some warning text")

    st.title('Bills that Became Laws')

    years = ['111 (2009-2010)','112 (2011-2012)','113 (2013-2014)','114 (2015-2016)','115 (2017-2018)','116 (2019-2020)','117 (2021-2022)','118 (2023-2024)','119 (2025-present)']
    congress_numbers = ['111','112','113','114','115','116','117','118','119']
    congress_num = st.radio('Select congress', congress_numbers)

    if congress_num:
        bb.display_congress(congress_num)
        num = st.text_input("Enter a bill number: ")

        if num: 
            division, title, df, bill = bb.display_bill(congress_num, num)
            keywords = []
            claims = []

            if st.button("Analyze",type="primary"): 
                keywords, claims = bb.analyze_bill(division, title, df, bill)
            
            if st.button("Begin research"):
                    with st.spinner("Searching for relevant research"):
                        aa.get_articles(keywords)
                    with st.spinner("Checking the bill against the research"):
                        cc.analyze_claims(claims)

            if st.button("Summarize",type ="primary"): 
                bb.summarize_bill(division,title,df,bill)
                
            

if __name__ == "__main__":
    main()