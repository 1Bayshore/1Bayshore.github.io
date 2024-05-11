from bs4 import BeautifulSoup
import datetime
from pathlib import Path

# First, take input from the user

print("Select a mode: (n)ew, (u)pdate, or (d)elete:")
mode_txt = input("mode: ")
while mode_txt not in ["n", "new", "u", "update", "d", "delete"]:
    print("Please enter a valid mode:")
    mode_txt = input("mode: ")

mode = ""

if mode_txt in ["n", "new"]:
    mode = "new"

elif mode_txt in ["u", "update"]:
    mode = "update"

elif mode_txt in ["d", "delete"]:
    mode = "delete"

if mode == "new":
    print("Please enter the filename of the source text, as listed in the 'sources' directory:")
    filename = input("filename: ")
    if not filename.endswith(".txt"):
        filename += ".txt"
    filename = filename.rpartition("/")[2]

    print("Please enter a title for the post:")
    title = input("title: ")
    if title == "":
        title = "Untitled"

    print("Please input any tags for the post, separated by commas:")
    print("(Note: tags should be valid in urls)")
    tags_str = input("tags: ")

elif mode == "update":
    print("Please enter the url of the post, including everything after the first slash:")
    url = input("url: ")
    if not url.startswith("/"):
        url = "/" + url
    
    filename = url.rpartition("/")[2].replace(".html", ".txt")

    print("Please enter the new title for the post, or leave blank to keep the current one:")
    title = input("title: ")

    print("Please input any tags for the post, separated by commas:")
    print("(Note: tags should be valid in urls)")
    print("(Note: replaces all existing tags)")
    print("(Leave blank to keep existing tags)")
    tags_str = input("tags: ")

elif mode == "delete":
    print("Please enter the url of the post, including everything after the first slash:")
    url = input("url: ")
    if not url.startswith("/"):
        url = "/" + url

#  Next, read the source file and the template
if mode in ["new", "update"]:
    if mode == "new":
        read_new_txt = True
    else:
        print("Please enter (y) to update text from the file or (n) to not update text")
        read_new_txt = True if input("Update text: ") in ["y", "yes"] else False
    
    if read_new_txt:
        text = ""
        with open("sources/" + filename) as f:
            text = f.read()
    
    else:
        text = ""
        with open("site" + url) as f:
            soupa = BeautifulSoup(f.read())
            text = "\n".join([x.get_text() for x in soupa.find("div", class_="body").find_all("p")])

    if title == "":
        with open("site" + url) as f:
            soupb = BeautifulSoup(f.read())
            title = soupb.find("h1", class_="title").get_text().strip()

    template = ""
    with open("template.html") as f:
        template = f.read()

# Customise the template text with the text from the source

    soup = BeautifulSoup(template, 'html.parser')

    soup.title.insert(0, title)
    soup.find("h1", class_="title").append(title)

    for i in text.splitlines():
        t_line = i.strip()
        soup.find("div", class_="body").append(BeautifulSoup("<p>" + t_line + "</p>", "html.parser"))

# Separate the tags by commas to make a list, and turn that into <a> tags

    if tags_str == "" and mode == "update":
        with open("site" + url) as f:
            soupc = BeautifulSoup(f.read())
            tags_list = [x.get_text() for x in soupc.find("div", class_="tags").find_all("a")]

    else:
        tags_list = [x.strip() for x in tags_str.split(",")]

    tags_html = ""
    for i in tags_list:
        tags_html += f'<a href="/tags/{i}.html">{i}</a>, '

    tags_html = tags_html[:-2] # remove the last comma and space
    soup.find("div", class_="tags").append(BeautifulSoup(tags_html, "html.parser"))


# Make sure the filename of the output is valid for a url (TODO: More checking here)

    output_filename = filename.partition(".")[0]
    output_filename = output_filename.replace(" ", "-")
    output_filename = output_filename.replace("_", "-")

# Get the current date, to use as an index for the post
if mode == "new":
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

    if prev_post_link:
        soup.find("a", class_="prev")['href'] = prev_post_link
    
elif mode == "update":
    next_link = ""
    prev_link = ""
    with open("site" + url) as f:
        n_text = f.read()
        soup2 = BeautifulSoup(n_text, "html.parser")
        try:
            prev_link = soup2.find("a", class_="prev")['href']
        except KeyError:
            pass # modifying the first post
        try:
            next_link = soup2.find("a", class_="next")['href']
        except KeyError:
            pass # modifying the last post
    if prev_link:
        soup.find("a", class_="prev")['href'] = prev_link
    if next_link:
        soup.find("a", class_="next")['href'] = next_link

# Save tags for later (if updating)

if mode == "update":
    d_tags_list = []
    with open("site" + url) as f:
        f_content = f.read()
        soup3 = BeautifulSoup(f_content, "html.parser")
        for i in soup3.find("div", class_="tags").find_all("a"):
            d_tags_list.append(i.text.strip())

# If in "new" mode, write the file. Will raise an error if the file already exists

if mode == "new":
    with open(f"site/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html", "x") as f:
        f.write(soup.prettify())

# If in "update" mode, replace the file, first confirming that it already exists
elif mode == "update":
    with open("site" + url, "w") as f:
        f.write(soup.prettify())

# If in "delete" mode, delete the file, first saving the tags (to be deleted later) and the next link of the previous page
elif mode == "delete":
    prev_page = ""
    d_tags_list = []
    with open("site" + url) as f:
        f_content = f.read()
        soup3 = BeautifulSoup(f_content, "html.parser")
        prev_page = soup3.find("a", class_="prev")['href']
        for i in soup3.find("div", class_="tags").find_all("a"):
            d_tags_list.append(i.text.strip())
    
    del_path = Path("site" + url)
    del_path.unlink()

# Set the previous post file to this post

if mode == "new":
    with open("prev_post_link.txt", "w") as f:
        f.write(f"/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html")

# Add a link to the file on the homepage (index.html) if necessary

if mode == "new":
    link_txt = f'<p><b>{current_time.year}-{current_time.month}-{current_time.day}: </b><a href="/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html">{title}</a></p>\n'

    idx_page = ""

    with open("site/index.html") as f:
        idx_page = f.read()

    soup4 = BeautifulSoup(idx_page, "html.parser")
    soup4.find("div", class_="recentPosts").insert(0, BeautifulSoup(link_txt, "html.parser"))

    with open("site/index.html", "w") as f:
        f.write(soup4.prettify())

if mode == "update":
    link_txt = f'<p><b>{url.split("/")[1]}-{url.split("/")[2]}-{url.split("/")[3]}: </b><a href="{url}">{title}</a></p>\n'

# Delete link to the file on the homepage (index.html) if necessary

elif mode == "delete":
    idx_page = ""
    with open("site/index.html") as f:
        idx_page = f.read()
    
    soup5 = BeautifulSoup(idx_page, "html.parser")
    soup5.find("div", class_="recentPosts").find("p").replace_with("")

    with open("site/index.html", "w") as f:
        f.write(soup5.prettify())

# Create and/or update the tag pages as necessary

if mode in ["update", "delete"]:
    for i in d_tags_list:
        print(d_tags_list)
        try:
            tag_page_content = ""
            with open(f"site/tags/{i}.html") as f:
                tag_page_content = f.read()
            
            soup6 = BeautifulSoup(tag_page_content, "html.parser")
            for j in soup6.find("div", class_="body").find_all("p"):
                if i in j.text:
                    j.replace_with("")

            with open(f"site/tags/{i}.html", "w") as f:
                f.write(soup6.prettify())

        except FileNotFoundError:
            pass

if mode in ["new", "update"]:
    for i in tags_list:
        try:
            tag_page_content = ""
            with open(f"site/tags/{i}.html") as f:
                tag_page_content = f.read()
            
            soup7 = BeautifulSoup(tag_page_content, "html.parser")
            soup7.find("div", class_="body").insert(0, BeautifulSoup(link_txt, "html.parser"))

            with open(f"site/tags/{i}.html", "w") as f:
                f.write(soup7.prettify())

        except FileNotFoundError:
            tag_page_content = ""
            with open("tag_template.html") as f:
                tag_page_content = f.read()
            
            soup8 = BeautifulSoup(tag_page_content, "html.parser")
            soup8.title.insert(0, i)
            soup8.find("h1", class_="title").insert(0, i)
            soup8.find("div", class_="body").insert(0, BeautifulSoup(link_txt, "html.parser"))

            with open(f"site/tags/{i}.html", "w") as f:
                f.write(soup8.prettify())

# Update the "next" link on the previous post to point to this one

if mode == "new":
    prev_post_html = ""

    if prev_post_link:
        try:
            with open("site" + prev_post_link) as f:
                prev_post_html = f.read()
                        
            soup9 = BeautifulSoup(prev_post_html, "html.parser")
            tag = soup9.find("a", "next")
            tag['href'] = f"/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html"

            with open("site" + prev_post_link, "w") as f:
                f.write(soup9.prettify())

        except FileNotFoundError or PermissionError:
            pass # it's the first post, no previous one to be updated

# If deleting the most recent post, reset the "next" pointer to the previous one
# TODO: If deleting a post in the middle, reset the poniters on both sides of it

if mode == "delete":
    prev_post_link = ""

    try:
        with open("prev_post_link.txt") as f:
            prev_post_link = f.read()
    except FileNotFoundError:
        pass # just leave the string blank

    if prev_post_link == url:
        prev_site = ""
        with open("site" + prev_page) as f:
            prev_site = f.read()
        soup10 = BeautifulSoup(prev_site, "html.parser")
        del soup10.find("a", class_="next")['href']

        with open("site" + prev_page, "w") as f:
            f.write(soup10.prettify())

        with open("prev_post_link.txt", "w") as f:
            f.write(prev_page)

# Report success

if mode == "new":
    print("Post generated!")
elif mode == "update":
    print("Post updated!")
elif mode == "delete":
    print("Post deleted.")
