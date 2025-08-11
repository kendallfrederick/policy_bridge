from llama_token_counter import LlamaTokenCounter

text = (
    f"""1. The Colorado River Indian Tribes (CRIT) are authorized to enter into agreements for the transfer or storage of a portion of its water allocation. 
    2. The CRIT is authorized to lease or exchange a portion of its consumptive use of water with facilities located in the Lower Basin of Arizona, as long as they are not located in Navajo, Apache, or Cochise counties.
    3. The CRIT is authorized to enter into storage agreements for underground storage facilities or groundwater savings facilities off the reservation.
    4. The CRIT is authorized to enter into agreements for water conservation or other methods for voluntarily leaving a portion of its reduced consumptive use in Lake Mead.
    5. Interior is granted authority to approve or disapprove agreements under this act, and must ensure that such agreements comply with federal environmental laws.
    6. The state of Arizona must be notified prior to entering into an agreement under this act.
    7. The CRIT's allocated water rights are reserved, including the right to use the remaining portion of its allocation.
    8. Allottees' water rights are protected from being interfered with by agreements under this act.
    9. The CRIT is entitled to all consideration from agreements under this act.
    10. The United States has limited liability against claims under this act, except for those relating to environmental requirements.
"""
)

counter = LlamaTokenCounter()

count = counter.count_tokens_sync(text)

if count > 8000:
    print("\nEXCEEDED CONTEXT LENGTH\n")
else:
    print(f"\n * just {count} tokens\n")

# tokens is slightly double word count