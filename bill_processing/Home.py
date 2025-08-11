import streamlit as st

st.set_page_config(
    page_title="Policy AI",
    page_icon="👋",
)

st.write("# Welcome to our Policy AI Project! 👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
    We've developed a pipeline to fact check bills and congressional research reports to illustrate the connect/disconnect between policy and scientific research. 
    **👈 Select a demo from the sidebar** to see some what our tech can do!
    ### Want to learn more?
    - Check out our bitbucket: (https://bitbucket.org/intelligenesisllc/policy_ai/src/main/)
    - Jump into our [confluence documentation](https://intelligenesisllc.atlassian.net/wiki/spaces/PAP/overview)
    """
)