import time
from bs4 import BeautifulSoup as bs
import re
import os
import datetime
import asyncio
import aiohttp
import aiofiles
from typing import List
import html
import sys
from app import globals



#Regex to match resource links
uploads = re.compile(r'[\'\"\(\/\s](uploads[^\.\"\']+?\.[a-zA-Z0-9]{2,5})[\'\"\)\s]')
assets =  re.compile(r'[\'\"\(\/\s](assets[^\.\"\']+?\.[a-zA-Z0-9]{2,5})[\'\"\)\s]')
stylesheets = re.compile(r'/stylesheets.*?\.css')


#Regex to match links to ignore
tags = re.compile(r'^/tags')
news = re.compile(r'/news')

limit: asyncio.Semaphore = None
id: int = None


class Resource:

    alreadyDownloaded: List[str] = []
    mvnuPrefix: str = 'https://mvnu.edu'
    archivePrefix: str = None
    connectionErrors: int = 0
    maxConnectionErrors: int = 30

    def __init__(self, baseLink: str, origin: str):

        self.bytes: bytes = None
        self.valid: bool = None
        self.mvnuUrl: str = None
        self.archiveUrl: str = None
        self.baseLink: str = None
        self.origin: str = origin

        if not baseLink.startswith('/'):
            baseLink = '/' + baseLink
        self.baseLink = baseLink

        self.archiveUrl = Resource.archivePrefix + baseLink
        self.mvnuUrl = Resource.mvnuPrefix + baseLink

    async def createBytes(self, session: aiohttp.ClientSession):
        try:
            async with limit:
                if Resource.connectionErrors > Resource.maxConnectionErrors:
                    return -1
                async with session.get(self.mvnuUrl) as r:
                    if not r.ok:
                        with open(Resource.archivePrefix + "/errors.txt", 'a') as errorFile:
                            errorFile.write(str(r.status) + " " + self.mvnuUrl + "\n")
                            errorFile.write("From: " + self.origin + "\n\n")
                        if r.status >= 500:
                            print("ERROR: ", r.status)
                            Resource.connectionErrors += 1
                        self.valid = False
                    else:
                        self.bytes = await r.read()
                        await asyncio.sleep(0)
                        self.valid = True
                    return 0
        
        except Exception as e:
            print("error downloading ", self.baseLink)
            print(e)
            if "payload" in str(e):
                print("Retrying")
                await self.createBytes(session)

    async def saveBytes(self):
        async with aiofiles.open(self.archiveUrl, mode='wb') as f:
            await f.write(self.bytes)
            Resource.alreadyDownloaded.append(self.baseLink)


    def makeDirs(self):
        if not os.path.exists(os.path.dirname(self.archiveUrl)):
            os.makedirs(os.path.dirname(self.archiveUrl))

    def __repr__(self):
        return self.baseLink




class Page:

    alreadyDownloaded: List[str] = []
    archivePrefix: str = None
    mvnuPrefix: str = 'https://mvnu.edu'
    connectionErrors: int = 0
    maxConnectionErrors: int = 30


    def __init__ (self, baseUrl: str, parentPage: str = "") -> None:

        self.baseUrl: str = None
        self.archiveUrl: str = None
        self.mvnuUrl: str = None
        self.soup: bs = None
        self.pageText: str = None
        self.resources: List[Resource] = []
        self.valid: bool = None
        self.parentPage: Page = parentPage

        if not baseUrl.startswith('/'):
            baseUrl = '/' + baseUrl
        self.baseUrl = baseUrl

        if baseUrl == '/':
            self.archiveUrl = Page.archivePrefix + '/index.html'
        else:
            self.archiveUrl = Page.archivePrefix + baseUrl

        if not self.archiveUrl.endswith('.html'):
            self.archiveUrl += '.html'

        self.mvnuUrl = Page.mvnuPrefix + baseUrl



    def createResourceLinks(self):
        uploadLinks = re.findall(uploads, self.pageText)
        uploadLinks = [f'/{link}' for link in uploadLinks]

        assetLinks = re.findall(assets, self.pageText)
        assetLinks = [f'/{link}' for link in assetLinks]

        styleLinks = re.findall(stylesheets, self.pageText)

        links = []
        links.extend(uploadLinks)
        links.extend(assetLinks)
        links.extend(styleLinks)

        links = list(set(links))
        for link in links:
            if link not in Resource.alreadyDownloaded:
                self.resources.append(Resource(html.unescape(link), self.mvnuUrl))


    def createSoup(self):
        self.soup = bs(self.pageText, 'html.parser')

    

    def getLinksFromSoup(self):
        if self.soup is None:
            print("ERROR: soup has not been created yet")
            return []
        else:
            hrefs = []
            body = self.soup.body
            newTag = self.soup.new_tag("div", style="display: flex; width: 100%; height: 100px; background-color: blue; font-size: 30px; justify-content: center; align-items: center;")
            body.insert(0, newTag)
            newTag.string = "THIS IS AN ARCHIVED PAGE"
            for a in self.soup.findAll('a', href=True):
                a['href'] = a['href'].strip()
                if re.match(r"((?<=mvnu\.edu)|^/)[^\.\?]*", a['href']) and not re.match(r"/uploads", a['href']):
                    if a['href'] == '/':
                        a['href'] = '/index.html'
                    else:
                        a['href'] = re.match(r"((?<=mvnu\.edu)|^/)[^\.\?]*", a['href']).group(0)
                        a['href'] += '.html'
                        hrefs.append(a['href'])
            self.pageText = str(self.soup)
            return hrefs



    async def createPageText(self, session: aiohttp.ClientSession):
        try:
            async with limit:
                if Page.connectionErrors > Page.maxConnectionErrors:
                    return -1
                async with session.get(self.mvnuUrl) as r:
                    Page.alreadyDownloaded.append(self.baseUrl)
                    if not r.ok:
                        with open(Page.archivePrefix + "/errors.txt", 'a') as errorFile:
                            errorFile.write(str(r.status) + " " + self.mvnuUrl + "\n")
                            errorFile.write("From: " + self.parentPage + "\n\n")
                        if r.status >= 500:
                            print("ERROR: ", r.status)
                            Page.connectionErrors += 1
                        self.valid = False
                    else:
                        self.pageText = await r.text(encoding='UTF-8')
                        self.valid = True
                    return 0
        except Exception as e:
            print("Error downloading page: ", self.baseUrl)
            print(e)
            if "payload" in str(e):
                print("Retrying")
                await self.createPageText(session)



    def makeDirs(self):
        if not os.path.exists(os.path.dirname(self.archiveUrl)):
            os.makedirs(os.path.dirname(self.archiveUrl))



    async def savePageText(self) -> None:
        async with aiofiles.open(self.archiveUrl, mode='w', encoding='utf-8') as f:
            await f.write(self.pageText)
        


    def __repr__(self) -> str:
        return self.archiveUrl + str(self.pageText is not None)
            


    


async def createArchive(id, prefix, recursive):
    status = 0
    try:
        Page.archivePrefix = 'archives/' + str(id)
        Resource.archivePrefix = 'archives/' + str(id)
        async with aiohttp.ClientSession() as session:
            currentPages: List[Page] = [Page(prefix)]

            while len(currentPages) > 0:

                print("\nLength of currentPages: ", len(currentPages))
                print("length of pages already downloaded: ", len(Page.alreadyDownloaded))
                print("length of resources already downloaded: ", len(Resource.alreadyDownloaded))

                #Creates page text from Page objects
                split = 1000
                listsOfCurrentPages = [currentPages[i:i+split] for i in range(0, len(currentPages), split)]
                currentPages = []
                tasks = []
                for listOfCurrentPages in listsOfCurrentPages:
                    for page in listOfCurrentPages:
                        task = asyncio.create_task(page.createPageText(session))
                        tasks.append(task)
                    currentPages.extend(listOfCurrentPages)
                    statusCodes = await asyncio.gather(*tasks)
                if -1 in statusCodes:
                    return "Too Many 500 Errors"
                print("Done creating page texts")

                if globals.event.is_set(): return "Killed"

                #Remove pages that could not be properly retrieved
                currentPages = [page for page in currentPages if page.valid]

                #Create soup for each page
                for page in currentPages:
                    page.createSoup()

                print("Done creating soups")

                if globals.event.is_set(): return "Killed"

                #Get hrefs from soup
                newPages: List[Page] = []
                newLinks: List[str] = []
                for page in currentPages:
                    for link in page.getLinksFromSoup():
                        if not tags.match(link) and not news.match(link) and not uploads.match(link) and link not in newLinks and link not in Page.alreadyDownloaded:
                            if prefix in link:
                                newPages.append(Page(link, page.mvnuUrl))
                                newLinks.append(link)


                print("Done getting hrefs")

                if globals.event.is_set(): return "Killed"

                #Saves the page text as html file
                for page in currentPages:
                    page.makeDirs()
                tasks = []
                for page in currentPages:
                    task = asyncio.create_task(page.savePageText())
                    tasks.append(task)
                await asyncio.gather(*tasks)
                print("Done saving pages")

                if globals.event.is_set(): return "Killed"
                #Find all resource links and create resource objects
                for page in currentPages:
                    page.createResourceLinks()


                #download all resources
                resources: List[Resource] = []
                for page in currentPages:
                    for resource in page.resources:
                        resources.append(resource)
                resources = list(set(resources))
                resources = [resource for resource in resources if resource not in Resource.alreadyDownloaded]
                print("Length of resources to download: ", len(resources))
                listsOfResources = [resources[i:i+split] for i in range(0, len(resources), split)]
                tasks = []
                for listOfResources in listsOfResources:
                    for resource in listOfResources:
                        #await asyncio.sleep(delay)
                        task = asyncio.create_task(resource.createBytes(session))
                        tasks.append(task)
                    statusCodes = await asyncio.gather(*tasks)
                    if -1 in statusCodes:
                        return "Too Many 500 errors"
                    print("Done downloading batch of resources")
                print("Done downloading resources")
                if globals.event.is_set(): return "Killed"

                #save all resources
                for page in currentPages:
                    for resource in page.resources:
                        resource.makeDirs()
                tasks = []
                for page in currentPages:
                    for resource in page.resources:
                        if resource.valid:
                            task = asyncio.create_task(resource.saveBytes())
                            tasks.append(task)
                await asyncio.gather(*tasks)
                print("Done saving resources")

                if globals.event.is_set(): return "Killed"
                #Change currentUrls to contain the new hrefs
                currentPages = newPages

                if not recursive:
                    return "SUCCESS"

            return "SUCCESS"

    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        print("Exception type: ", exception_type)
        print("File name: ", filename)
        print("Line number: ", line_number)
        return e
    


def run(id: int, prefix: str, recursive: bool):
    global limit
    Page.alreadyDownloaded = []
    Page.connectionErrors = 0
    Resource.alreadyDownloaded = []
    Resource.connectionErrors = 0
    limit = asyncio.Semaphore(30)
    status = asyncio.run(createArchive(id, prefix, recursive))
    print(status)
    return None



if __name__ == '__main__':
    start = time.time()
    if len(sys.argv) > 1:
        asyncio.run(createArchive(1, int(sys.argv[1])))
    else:
        asyncio.run(createArchive(1))
    end = time.time()
    print(end-start)
