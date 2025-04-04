from bs4 import BeautifulSoup
import datetime
from pathlib import Path
import markdown

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
    if not (filename.endswith(".txt") or filename.endswith(".md")):
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
        try:
            with open("sources/" + filename, encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            # Maybe it's .md instead
            with open("sources/" + filename.replace(".txt", ".md"), encoding='utf-8') as f:
                text = f.read()
    
    else:
        text = ""
        with open("site" + url, encoding='utf-8') as f:
            soupa = BeautifulSoup(f.read(), "html.parser")
            text = "\n".join([x.get_text() for x in soupa.find("div", class_="body").find_all("p")])

    if title == "": # XXX does this code ever run?
        with open("site" + url, encoding='utf-8') as f:
            soupb = BeautifulSoup(f.read(), "html.parser")
            title = soupb.find("h1", class_="title").get_text().strip()

    template = ""
    with open("templates/template.html", encoding='utf-8') as f:
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
            with open("site/media/" + img_path.rpartition("/")[2], "wb") as f:
                f.write(img)
            
        except FileNotFoundError:
            print("Warning: couldn't find image at sources/" + img_path)
        i['src'] = "/media/" + img_path

    # Deal with iframe creation
    for j in text_html.find_all("a"):
        html_path = j['href']
        potential_tidle = []
        for k in j.previous_siblings:
            potential_tidle.append(k.text)
        try:
            if potential_tidle[-1].endswith("~"):
                j.replace_with(BeautifulSoup(f'<div class="ibox"><iframe src="/interactives/{html_path}" title="{j.text}"></iframe></div>', "html.parser"))

            try:
                with open("sources/" + html_path, "r", encoding="utf-8") as f:
                    html_file = f.read()
                with open("site/interactives/" + html_path.rpartition("/")[2], "w", encoding="utf-8") as f:
                    f.write(html_file)
                
            except FileNotFoundError:
                print("Warning: couldn't find interactive at sources/" + html_path)
        except IndexError:
            print("Found ordinary link, not iframe")

    soup.find("div", class_="body").append(text_html)

# Separate the tags by commas to make a list, and turn that into <a> tags

    if tags_str == "" and mode == "update":
        with open("site" + url, encoding='utf-8') as f:
            soupc = BeautifulSoup(f.read(), "html.parser")
            tags_list = [x.get_text().strip() for x in soupc.find("div", class_="tags").find_all("a")]

    else:
        tags_list = [x.strip() for x in tags_str.split(",")]
    
    if tags_list == [""]:
        tags_list = []

    tags_html = ""
    for i in tags_list:
        tags_html += f'<a href="/tags/{i}.html">{i}</a>, '

    if tags_html != "":
        tags_html = tags_html[:-2] # remove the last comma and space
        soup.find("div", class_="tags").append(BeautifulSoup(tags_html, "html.parser"))


# Make sure the filename of the output is valid for a url (TODO: More checking here)

    output_filename = filename.partition(".")[0]
    output_filename = output_filename.replace(" ", "-")
    output_filename = output_filename.replace("_", "-")

# Get the current date, to use as an index for the post

    if mode == "new":
        current_time = datetime.date.today()
    else:
        current_time = datetime.datetime.strptime(url.rpartition("/")[0], "/%Y/%m/%d")

    soup.find("div", class_="date").append(f"{current_time.day} {current_time.strftime('%B')} {current_time.year}")

# Create the directory in which the file will go

if mode == "new":
    dir_path = Path(f"site/{current_time.year}/{current_time.month}/{current_time.day}")
    dir_path.mkdir(parents=True, exist_ok=True)

# Get the previous post from the previous post file

    prev_post_link = ""

    try:
        with open("templates/prev_post_link.txt", encoding='utf-8') as f:
            prev_post_link = f.read()
    except FileNotFoundError:
        pass # just leave the string blank

    if prev_post_link:
        soup.find("a", class_="prev")['href'] = prev_post_link
    
elif mode == "update":
    next_link = ""
    prev_link = ""
    with open("site" + url, encoding='utf-8') as f:
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
    with open("site" + url, encoding='utf-8') as f:
        f_content = f.read()
        soup3 = BeautifulSoup(f_content, "html.parser")
        for i in soup3.find("div", class_="tags").find_all("a"):
            d_tags_list.append(i.text.strip())

# If in "new" mode, write the file. Will raise an error if the file already exists

if mode == "new":
    with open(f"site/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html", "x", encoding='utf-8') as f:
        f.write(soup.prettify())

# If in "update" mode, replace the file, first confirming that it already exists
elif mode == "update":
    with open("site" + url, "w", encoding='utf-8') as f:
        f.write(soup.prettify())

# If in "delete" mode, delete the file, first saving the tags (to be deleted later) and the next link of the previous page
elif mode == "delete":
    prev_page = ""
    d_tags_list = []
    with open("site" + url, encoding='utf-8') as f:
        f_content = f.read()
        soup3 = BeautifulSoup(f_content, "html.parser")
        prev_page = soup3.find("a", class_="prev")['href']
        for i in soup3.find("div", class_="tags").find_all("a"):
            d_tags_list.append(i.text.strip())
    
    del_path = Path("site" + url)
    del_path.unlink()

# Set the previous post file to this post

if mode == "new":
    with open("templates/prev_post_link.txt", "w", encoding='utf-8') as f:
        f.write(f"/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html")

# Add a link to the file on the homepage (index.html) if necessary

if mode == "new":
    link_txt = f'<p><b>{current_time.year}-{current_time.month}-{current_time.day}: </b><a href="/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html">{title}</a></p>\n'

    idx_page = ""

    with open("site/index.html", encoding='utf-8') as f:
        idx_page = f.read()

    soup4 = BeautifulSoup(idx_page, "html.parser")
    soup4.find("div", class_="recentPosts").insert(0, BeautifulSoup(link_txt, "html.parser"))

    with open("site/index.html", "w", encoding='utf-8') as f:
        f.write(soup4.prettify())

if mode == "update":
    link_txt = f'<p><b>{url.split("/")[1]}-{url.split("/")[2]}-{url.split("/")[3]}: </b><a href="{url}">{title}</a></p>\n'

# Delete link to the file on the homepage (index.html) if necessary

elif mode == "delete":
    idx_page = ""
    with open("site/index.html", encoding='utf-8') as f:
        idx_page = f.read()
    
    soup5 = BeautifulSoup(idx_page, "html.parser")
    soup5.find("div", class_="recentPosts").find("p").replace_with("")

    with open("site/index.html", "w", encoding='utf-8') as f:
        f.write(soup5.prettify())

# Create and/or update the tag pages as necessary

if mode in ["update", "delete"]:
    for i in d_tags_list:
        print(d_tags_list)
        try:
            tag_page_content = ""
            with open(f"site/tags/{i}.html", encoding='utf-8') as f:
                tag_page_content = f.read()
            
            soup6 = BeautifulSoup(tag_page_content, "html.parser")
            for j in soup6.find("div", class_="body").find_all("p"):
                if j.find('a')['href'] == url:
                    j.replace_with("")
            
            if soup6.find("div", class_="body").text.strip() == "":
                # tag is empty, time to delete
                del_page = Path(f"site/tags/{i}.html")
                del_page.unlink()
            else:
                with open(f"site/tags/{i}.html", "w", encoding='utf-8') as f:
                    f.write(soup6.prettify())

        except FileNotFoundError:
            pass

if mode in ["new", "update"]:
    for i in tags_list:
        i = i.strip()
        try:
            tag_page_content = ""
            with open(f"site/tags/{i}.html", encoding='utf-8') as f:
                tag_page_content = f.read()
            
            soup7 = BeautifulSoup(tag_page_content, "html.parser")
            soup7.find("div", class_="body").insert(0, BeautifulSoup(link_txt, "html.parser"))

            with open(f"site/tags/{i}.html", "w", encoding='utf-8') as f:
                f.write(soup7.prettify())

        except FileNotFoundError:
            tag_page_content = ""
            with open("templates/tag_template.html", encoding='utf-8') as f:
                tag_page_content = f.read()
            
            soup8 = BeautifulSoup(tag_page_content, "html.parser")
            soup8.title.insert(0, i)
            soup8.find("h1", class_="title").insert(0, i)
            soup8.find("div", class_="body").insert(0, BeautifulSoup(link_txt, "html.parser"))

            with open(f"site/tags/{i}.html", "w", encoding='utf-8') as f:
                f.write(soup8.prettify())

# Update the "next" link on the previous post to point to this one

if mode == "new":
    prev_post_html = ""

    if prev_post_link:
        try:
            with open("site" + prev_post_link, encoding='utf-8') as f:
                prev_post_html = f.read()
                        
            soup9 = BeautifulSoup(prev_post_html, "html.parser")
            tag = soup9.find("a", "next")
            tag['href'] = f"/{current_time.year}/{current_time.month}/{current_time.day}/{output_filename}.html"

            with open("site" + prev_post_link, "w", encoding='utf-8') as f:
                f.write(soup9.prettify())

        except FileNotFoundError or PermissionError:
            pass # it's the first post, no previous one to be updated

# If deleting the most recent post, reset the "next" pointer to the previous one
# TODO: If deleting a post in the middle, reset the poniters on both sides of it

if mode == "delete":
    prev_post_link = ""

    try:
        with open("templates/prev_post_link.txt", encoding='utf-8') as f:
            prev_post_link = f.read()
    except FileNotFoundError:
        pass # just leave the string blank

    if prev_post_link == url:
        prev_site = ""
        with open("site" + prev_page, encoding='utf-8') as f:
            prev_site = f.read()
        soup10 = BeautifulSoup(prev_site, "html.parser")
        del soup10.find("a", class_="next")['href']

        with open("site" + prev_page, "w", encoding='utf-8') as f:
            f.write(soup10.prettify())

        with open("templates/prev_post_link.txt", "w", encoding='utf-8') as f:
            f.write(prev_page)

# Report success

if mode == "new":
    print("Post generated!")
elif mode == "update":
    print("Post updated!")
elif mode == "delete":
    print("Post deleted.")
