import datetime
from pathlib import Path

print("Please enter the filename, as listed in the 'sources' directory:")
filename = input("filename: ")
if not filename.endswith(".txt"):
    filename += ".txt"

print("Please enter a title for the post:")
title = input("title: ")
if title == "":
    title = "Untitled"

text = ""
with open("sources/" + filename) as f:
    text = f.read()

template = ""
with open("template.html") as f:
    template = f.read()

text = text.replace("\t", "<p>") # note actual tab character
text = text.replace("\n", "</p>\n")
if not text.endswith("</p>"):
    text += "</p>"

final_html = template.replace("{{title}}", title)
final_html = final_html.replace("{{body}}", text)

output_filename = filename.partition(".")[0]
output_filename = output_filename.replace(" ", "-")
output_filename = output_filename.replace("_", "-")

current_time = datetime.date.today()

dir_path = Path(f"site/{current_time.year}/{current_time.month}/{current_time.day}")

dir_path.mkdir(parents=True, exist_ok=True)

with open(f"site/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html", "x") as f:
    f.write(final_html)

print("Post generated!")
