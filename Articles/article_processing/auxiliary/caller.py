import subprocess

# Stores lists of keywords as test cases
keyword_list1 = ["Energy efficiency", "Water treatment facilities", "Wastewater treatment facilities", "Smart manufacturing", "Energy management systems", "Sustainable manufacturing", "Information technology advancements"]
keyword_list2 = ["Broadband", "Middle mile infrastructure", "Underserved areas", "Indian Tribe", "Tribal government", "Carrier-neutral interconnection", "Regulatory barriers", "National security interests", "Wholesale broadband service", "Last mile networks"]
keyword_list3 = ["Publicly owned treatment works", "Low-income individuals", "Moderate-income individuals", "Competitive grant program", "Eligible entities", "Qualified individuals"]

# Runs keyword_populate.py subprocess with keywords in keyword list as arguments
# Update absolute path based on system
program_path = "/Users/intern7/Policy_Project/policy_ai/Articles/article_processing/keyword_populate.py"
subprocess.run(["python3", program_path] + keyword_list1)