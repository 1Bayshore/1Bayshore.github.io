from bs4 import BeautifulSoup
import datetime
import markdown

# First, take input from the userprint("Please enter the filename of the source text, as listed in the 'sources' directory:")
filename = input("filename: ")
if not (filename.endswith(".txt") or filename.endswith(".md")):
    filename += ".txt"
filename = filename.rpartition("/")[2]

print("Please enter a subject for the email:")
title = input("subject: ")
if title == "":
    title = "No Subject"

#  Next, read the source file and the template

text = ""
try:
    with open("sources/" + filename, encoding='utf-8') as f:
        text = f.read()
except FileNotFoundError:
    # Maybe it's .md instead
    with open("sources/" + filename.replace(".txt", ".md"), encoding='utf-8') as f:
        text = f.read()

template = ""
with open("templates/email-template.html", encoding='utf-8') as f:
    template = f.read()

# Customise the template text with the text from the source

soup = BeautifulSoup(template, 'html.parser')

soup.title.insert(0, title)
soup.find("h1", class_="title").append(title)

md_to_html = markdown.markdown(text, extensions=['tables'])

text_html = BeautifulSoup(md_to_html, "html.parser")

# Deal with image embedding
for i in text_html.find_all("img"):
    img_path = i['src']
    try:
        with open("sources/" + img_path, "rb") as f:
            img = f.read()
        with open("emails/media/" + img_path.rpartition("/")[2], "wb") as f:
            f.write(img)
        
    except FileNotFoundError:
        print("Warning: couldn't find image at sources/" + img_path)
    i['src'] = "/media/" + img_path

soup.find("div", class_="body").append(text_html)

# Make sure the filename of the output is valid for a url (TODO: More checking here)

output_filename = filename.partition(".")[0]
output_filename = output_filename.replace(" ", "-")
output_filename = output_filename.replace("_", "-")

current_time = datetime.date.today()

soup.find("div", class_="date").append(f"{current_time.day} {current_time.strftime('%B')} {current_time.year}")

with open(f"emails/{output_filename}.html", "x", encoding='utf-8') as f:
    f.write(soup.prettify())

# Report success

print("Email generated!")
