from archivePackage.archive import Page, Resource

def test_links():
    Page.archivePrefix = "https://www.mvnu.edu"
    page = Page("")
    text = None
    with open("archivePackage/test_page.html", 'r') as f:
        text = f.read()
    page.pageText = text
    page.createSoup()
    hrefs = page.getLinksFromSoup()
    print(hrefs)
    assert len(hrefs) == 333
    