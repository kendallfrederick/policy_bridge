import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('updated_list.csv')
subjects = df['Subject']
subject_counts = subjects.value_counts()

# Create the pie chart with modern styling
fig, ax = plt.subplots(figsize=(12, 8))
colors = plt.cm.Set3(range(len(subject_counts)))  # Use a pleasant color palette

wedges, texts, autotexts = ax.pie(subject_counts.values, 
                                 labels=None,  # No labels on pie
                                 autopct='%1.1f%%', 
                                 colors=colors,
                                 startangle=90,
                                 wedgeprops={'edgecolor': 'white', 'linewidth': 2})

# Create legend labels with percentages from autotexts
legend_labels = [f"{subject} ({autotext.get_text()})" for subject, autotext in zip(subject_counts.index, autotexts)]

# Add clean legend with percentages
ax.legend(wedges, legend_labels, title="Congressional Subjects", 
          loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
          frameon=False, fontsize=10)

# Clean styling
ax.axis('equal')
plt.title('117th and 118th Congress Subjects', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.show()