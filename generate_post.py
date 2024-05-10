import datetime
from pathlib import Path

# First, take input from the user
print("Please enter the filename, as listed in the 'sources' directory:")
filename = input("filename: ")
if not filename.endswith(".txt"):
    filename += ".txt"

print("Please enter a title for the post:")
title = input("title: ")
if title == "":
    title = "Untitled"

print("Please input any tags for the post, separated by commas:")
print("(Note: tags should be valid in urls)")
tags_str = input("tags: ")

# Next, read the source file and the template
text = ""
with open("sources/" + filename) as f:
    text = f.read()

template = ""
with open("template.html") as f:
    template = f.read()

# Customise the template text with the text from the source

text = text.replace("\t", "<p>") # note actual tab character
text = text.replace("\n", "</p>\n")
if not text.endswith("</p>"):
    text += "</p>"

# Separate the tags by commas to make a list, and turn that into <a> tags

tags_list = [x.strip() for x in tags_str.split(",")]
tags_html = "Tags: "
for i in tags_list:
    tags_html += f'<a href="/tags/{i}.html">{i}</a>, '

tags_html = tags_html[:-2] # remove the last comma and space

# Make sure the filename of the output is valid for a url (TODO: More checking here)

output_filename = filename.partition(".")[0]
output_filename = output_filename.replace(" ", "-")
output_filename = output_filename.replace("_", "-")

# Get the current date, to use as an index for the post
current_time = datetime.date.today()

# Create the directory in which the file will go

dir_path = Path(f"site/{current_time.year}/{current_time.month}/{current_time.day}")
dir_path.mkdir(parents=True, exist_ok=True)

# Get the previous post from the previous post file

prev_post_link = ""

try:
    with open("prev_post_link.txt") as f:
        prev_post_link = f.read()
except FileNotFoundError:
    pass # just leave the string blank

# Finalise the template

final_html = template.replace("{{title}}", title)
final_html = final_html.replace("{{body}}", text)
final_html = final_html.replace("{{tags}}", tags_html)

if prev_post_link: # account for first post, where there is no prev_post_link
    final_html = final_html.replace('<a class="prev">Previous</a>', f'<a class="prev" href="{prev_post_link}">Previous</a>')

# Write the file. Will raise an error if the file already exists

with open(f"site/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html", "x") as f:
    f.write(final_html)

# Set the previous post file to this post

with open("prev_post_link.txt", "w") as f:
    f.write(f"/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html")

# Add a link to the file on the homepage (index.html)

link_txt = f'<p><b>{current_time.year}-{current_time.month}-{current_time.day}: </b><a href="/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html">{title}</a></p>\n'

idx_page = ""

with open("site/index.html") as f:
    idx_page = f.read()

idx_page = idx_page.replace("<!--Most recent post marker - do not remove-->", "<!--Most recent post marker - do not remove-->\n" + link_txt)

with open("site/index.html", "w") as f:
    f.write(idx_page)

# Create and/or update the tag pages as necessary

for i in tags_list:
    try:
        tag_page_content = ""

        with open(f"site/tags/{i}.html") as f:
            tag_page_content = f.read()
        tag_page_content = tag_page_content.replace("<!--Most recent post marker - do not remove-->", "<!--Most recent post marker - do not remove-->\n" + link_txt)

        with open(f"site/tags/{i}.html", "w") as f:
            f.write(tag_page_content)
    
    except FileNotFoundError:
        tag_page_content = ""

        with open("tag_template.html") as f:
            tag_page_content = f.read()
        
        tag_page_content = tag_page_content.replace("{{tag}}", i)
        tag_page_content = tag_page_content.replace("{{body}}", link_txt)

        with open(f"site/tags/{i}.html", "w") as f:
            f.write(tag_page_content)

# Update the "next" link on the previous post to point to this one

prev_post_html = ""

if prev_post_link:
    try:
        with open("site" + prev_post_link) as f:
            prev_post_html = f.read()
        
        prev_post_html = prev_post_html.replace('<a class="next">Next</a>', f'<a class="next" href="/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html">Next</a>')

        with open("site" + prev_post_link, "w") as f:
            f.write(prev_post_html)

    except FileNotFoundError or PermissionError:
        pass # it's the first post, no previous one to be updated


# Report success

print("Post generated!")
