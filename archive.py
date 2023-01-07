import time
from bs4 import BeautifulSoup as bs
import re
import os
import datetime
import asyncio
import aiohttp
import aiofiles
from typing import List



#Regex to match resource links
uploads = re.compile(r'[\'\"\(\/\s](uploads[^\.]+?\.[a-zA-Z0-9]{2,5})[\'\"\)\s]')
assets =  re.compile(r'[\'\"\(\/\s](assets[^\.]+?\.[a-zA-Z0-9]{2,5})[\'\"\)\s]')
stylesheets = re.compile(r'/stylesheets.*?\.css')


#Regex to match links to ignore
tags = re.compile(r'^/tags')
news = re.compile(r'/news')





class Resource:

    alreadyDownloaded: List[str] = []
    mvnuPrefix: str = 'https://mvnu.edu'

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
        async with session.get(self.mvnuUrl) as r:
            if not r.ok:
                #print("ERROR:" + str(r.status))
                #print("link: " + self.mvnuUrl)
                #print("From: " + self.origin)
                if r.status >= 500:
                    print("ERROR: ", r.status)
                self.valid = False
            else:
                self.bytes = await r.read()
                self.valid = True

    async def saveBytes(self):
        if not self.valid:
            return
        async with aiofiles.open(self.archiveUrl, mode='wb') as f:
            await f.write(self.bytes)
            Resource.alreadyDownloaded.append(self.baseLink)


    def makeDirs(self):
        if not self.valid:
            return
        if not os.path.exists(os.path.dirname(self.archiveUrl)):
            os.makedirs(os.path.dirname(self.archiveUrl))




class Page:

    alreadyDownloaded: List[str] = []
    archivePrefix: str = None
    mvnuPrefix: str = 'https://mvnu.edu'


    def __init__ (self, baseUrl: str) -> None:

        self.baseUrl: str = None
        self.archiveUrl: str = None
        self.mvnuUrl: str = None
        self.soup: bs = None
        self.pageText: str = None
        self.resources: List[Resource] = []
        self.valid: bool = None

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

        for link in links:
            if link not in Resource.alreadyDownloaded:
                self.resources.append(Resource(link, self.mvnuUrl))


    def createSoup(self):
        if self.valid:
            self.soup = bs(self.pageText, 'html.parser')
        else:
            print("Error: Page text is None")

    

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
                if a['href'].startswith('/') and '.' not in a['href']:
                    a['href'] = (a['href'].split('?')[0]) #Removes parameter portion of url
                    if a['href'] == '/':
                        a['href'] = '/index.html'
                    else:
                        a['href'] += '.html'
                        hrefs.append(a['href'])
            self.pageText = str(self.soup)
            return hrefs



    async def createPageText(self, session: aiohttp.ClientSession):
        try:
            async with session.get(self.mvnuUrl) as r:
                if not r.ok:
                    #print("ERROR:" + str(r.status))
                    #print("Link: " + self.mvnuUrl)
                    if r.status >= 500:
                        print("ERROR: ", r.status)
                    self.valid = False
                else:
                    self.pageText = await r.text(encoding='UTF-8')
                    self.valid = True
        except Exception as e:
            print("Caught exception")
            print(e)
            print("End of exception")



    def makeDirs(self):
        if not self.valid:
            return
        if not os.path.exists(os.path.dirname(self.archiveUrl)):
            os.makedirs(os.path.dirname(self.archiveUrl))



    async def savePageText(self) -> None:
        if not self.valid:
            return
        async with aiofiles.open(self.archiveUrl, mode='w') as f:
            await f.write(self.pageText)
        Page.alreadyDownloaded.append(self.baseUrl)


    def __repr__(self) -> str:
        return self.archiveUrl + str(self.pageText is not None)
            


    


async def run():
    delay = 0.1
    async with aiohttp.ClientSession() as session:

        #Converts list of url strings into page objects
        currentUrls: List[str] = ['']

        limit = 100
        current = 0
        while len(currentUrls) > 0:
            current += 1
            if current > limit:
                return
            
            currentPages: List[Page] = []
            for url in currentUrls:
                if url not in Page.alreadyDownloaded:
                    currentPages.append(Page(url))

            print("\nLength of currentPages: ", len(currentPages))
            print("length of pages already downloaded: ", len(Page.alreadyDownloaded))
            print("length of resources already downloaded: ", len(Resource.alreadyDownloaded))

            #Creates page text from Page objects
            split = 1000
            listsOfCurrentPages = [currentPages[i:i+split] for i in range(0, len(currentPages), split)]
            #print("Length of listsOfCurrentPages: ", len(listsOfCurrentPages))
            currentPages = []
            tasks = []
            for listOfCurrentPages in listsOfCurrentPages:
                for page in listOfCurrentPages:
                    await asyncio.sleep(delay)
                    task = asyncio.create_task(page.createPageText(session))
                    tasks.append(task)
                currentPages.extend(listOfCurrentPages)
                await asyncio.gather(*tasks)
            #    print("Done downloading batch")
            #print("Length of current Pages after split: ", len(currentPages))
            #print("Done creating page texts")


            #Remove pages that could not be properly retrieved
            currentPages = [page for page in currentPages if page.valid]

            #Create soup for each page
            for page in currentPages:
                page.createSoup()

            #Get hrefs from soup
            hrefs = []
            for page in currentPages:
                hrefs.extend(page.getLinksFromSoup())
            hrefs = [href for href in hrefs if not tags.match(href) and not news.match(href) and not uploads.match(href)]
            hrefs = list(set(hrefs))

            #Saves the page text as html file
            for page in currentPages:
                page.makeDirs()
            tasks = []
            for page in currentPages:
                task = asyncio.create_task(page.savePageText())
                tasks.append(task)
            await asyncio.gather(*tasks)

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
                    await asyncio.sleep(delay)
                    task = asyncio.create_task(resource.createBytes(session))
                    tasks.append(task)
                await asyncio.gather(*tasks)
                #print("Done downloading batch")
            #print("Done downloading resources")

            #save all resources
            for page in currentPages:
                for resource in page.resources:
                    resource.makeDirs()
            tasks = []
            for page in currentPages:
                for resource in page.resources:
                    task = asyncio.create_task(resource.saveBytes())
                    tasks.append(task)
            await asyncio.gather(*tasks)

            #Change currentUrls to contain the new hrefs
            currentUrls = hrefs

        


if __name__ == '__main__':
    now = datetime.datetime.now().strftime('%d%m%y%H%M%S')
    Page.archivePrefix = 'archives/' + now
    Resource.archivePrefix = 'archives/' + now

    start = time.time()
    try:
        asyncio.run(run())
    except Exception as e:
        print(e)
    end = time.time()
    print(end-start)




#Split changes based on internet connection?