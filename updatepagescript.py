import pywikibot
import pandas
import pywikibot.page
import requests
import os
from dotenv import load_dotenv
load_dotenv()

birds = pandas.read_csv('birdlist.csv')
site = pywikibot.Site('wikipedia:en')
S = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"

lgntokenreq = S.get(f"{URL}?action=query&meta=tokens&type=login&format=json").json()
lgntoken = lgntokenreq["query"]["tokens"]["logintoken"]

params1 = {
    "action": "login",
    "lgname": "IUCNStatusBot@IUCNStatusBot",
    "lgpassword": os.getenv("IUCNPASS"),
    "lgtoken": lgntoken,
    "format": "json"
}

R = S.post(URL, data=params1)


params2 = {
    "action": "query",
    "meta": "tokens",
    "format": "json"
}

csrf = S.get(url=URL, params=params2).json()
csrftoken = csrf['query']['tokens']['csrftoken']

statuscats = {"LC" : "IUCN Red List least concern species",
              "NT" : "IUCN Red List near threatened species",
              "VU" : "IUCN Red List vulnerable species",
              "EN" : "IUCN Red List endangered species",
              "CR" : "IUCN Red List critically endangered species",
              "EW" : "IUCN Red List extinct in the wild species",
              "EX" : "IUCN Red List extinct species",
              "DD" : "IUCN Red List data deficient species",
              }

for _,x in birds.iterrows():
    if str(x[4]) == 'nan':
        x[4] = ""
    statusfound = False
    reffound = False
    namefound = False
    page = pywikibot.Page(site, x[0])
    current = page.text
    while page.isRedirectPage():
        page = page.getRedirectTarget()
    pgtext = page.text
    pglist = pgtext.split('|')
    for i in range(len(pglist)):

        temp = pglist[i]
        temp = temp.replace(" ", "")
        temp = temp.replace("\t","")
        if temp.lower().startswith("status="): #Extract name
            pglist[i] = f" status = {x[6]}\n"
            statusfound = True
            break
    name = ""
    for i in range(len(pglist)):
        temp = pglist[i]
        temp = temp.replace(" ", "")
        temp = temp.replace("\t", "")
        if "<ref" in temp:
            reffound = True
            if "name=" in temp:
                name = temp[temp.index('name=')+5 : temp.index('>')]
                namefound = True
                #format Abroscopus albogularis,BirdLife International,2024,e.T22715451A264188832,10.2305/IUCN.UK.2024-2.RLTS.T22715451A264188832.en,7 February 2025,LC
                ref = f"""<ref name = {name}>{{{{cite iucn | author={x[1]} | date={x[2]}| title=''{x[0]}'' | volume={x[2]} | page={x[3]} | doi={x[4]} |access-date={x[5]}}}}}</ref>\n""" #Update reference, extracting original name
            else:
                ref = f"""<ref>{{{{cite iucn | author={x[1]} | date={x[2]}| title=''{x[0]}'' | volume={x[2]} | page={x[3]} | doi={x[4]} | access-date={x[5]}}}}}</ref>\n"""
            while '</ref>' not in temp:
                temp = pglist.pop(i+1)
            pglist.insert(i+1, ref)
            break                
    temp = ('|'.join(pglist))
    if statusfound == False:
        pglist = temp.split(r'{{')
        for i in range(len(pglist)): #Update status if it is not present
            if pglist[i].lower().startswith('speciesbox'):
                temp2 = pglist[i].split(r'}}')
                temp2.insert(1, f"|status = {x[6]}")
                pglist[i] = r'}}'.join(temp2)
        pglist = r'{{'.join(pglist)
    if reffound == False: #Update citation if it is not present
        pglist = temp.split(r'{{')
        for i in range(len(pglist)):
            if pglist[i].startswith('speciesbox'):
                temp2 = pglist[i].split(r'}}')
                temp2.insert(1, f"""<ref>{{{{cite iucn |author={x[1]} |date={x[2]}| title=''{x[0]}'' |volume={x[2]} |page={x[3]} |doi={x[4]} |access-date={x[5]}}}}}</ref>""")
                pglist[i] = r'}}'.join(temp2)
        pglist = r'{{'.join(pglist)
    temp = temp.split('[[Category:')
    temp = [t for t in temp if not any(t.startswith(a) for a in statuscats.values())] #remove Red List category tag
    temp.insert(1, f'{statuscats[x[6]]}]]\n')
    pgtext = '[[Category:'.join(temp)
    page.text = pgtext
    page.save("Automatic updating of status.", minor = True)
