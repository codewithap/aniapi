from requests import get
from bs4 import BeautifulSoup
import json

class mal:
  def __init__(self):
    self.BaseUrl = "https://myanimelist.net"
  
  def getAnimeById(self,id): ## Anime info by ID ##
    data = get(self.BaseUrl + f"/anime/{id}")
    soup = BeautifulSoup(data.text, "html.parser")

    songs = soup.select(".js-theme-songs")
    try:
      opening = songs[0].select("table")[1].select("tr")
      openingSongs = [{"name" : x.select("td")[1].text, 
                      "spotify": x.select("td")[1].select("input")[0]["value"],
                      "youtube": x.select("td")[1].select("input")[3]["value"]} 
                    for x in opening]
    except: 
      openingSongs = []

    try:
      ending = songs[1].select("table")[0].select("tr")
      endingSongs = [{"name" : x.select("td")[1].text, 
                      "spotify": x.select("td")[1].select("input")[0]["value"],
                      "youtube": x.select("td")[1].select("input")[3]["value"]} 
                    for x in ending]
    except: 
      endingSongs = []

    related_animes = soup.select(".related-entries .entries-tile .entry")
    related_animes_json = [{"type": x.select_one(".relation").text,
                            "img": x.select_one(".image img")["data-src"],
                            "link": x.select_one(".image a")["href"],
                            "name": x.select_one(".title").text}
                          for x in related_animes if x.select_one(".relation") != None]

    jsonData = { 
      "mal_id" : int(id),
      "title": soup.select(".title-name")[0].text,
      # "title_eng": soup.select(".title-english")[0].text,
      "url" : f"{self.BaseUrl}/anime/{id}",
      "imgs": {
            "jpg":{
              "medium": soup.select(".borderClass img.ac")[0]["data-src"],
              "large": soup.select(".borderClass img.ac")[0]["data-src"].replace(".jpg", "l.jpg")
            },
            "webp": {
              "medium": soup.select(".borderClass img.ac")[0]["data-src"].replace(".jpg", ".webp"),
              "large": soup.select(".borderClass img.ac")[0]["data-src"].replace(".jpg", "l.webp")
            }
          },
      "rank": soup.select(".stats-block .ranked strong")[0].text,
      "popularity": soup.select(".stats-block .popularity strong")[0].text,
      "score": soup.select(".stats-block .score")[0].text,
      "description": soup.findAll("p", {"itemprop" : "description"})[0].text, 
      "info": {x.select(".dark_text")[0].text.replace(":","").strip().lower() : x.text.replace(x.select('.dark_text')[0].text,"").strip() for x in soup.select(".borderClass .leftside .spaceit_pad")},
      "external_links": [{"name": x.text.strip().lower(), "data" : x["href"]} for x in soup.select(".external_links a")],
      "related_animes": related_animes_json,
      "theme_songs": {
        "opening": openingSongs,
        "ending": endingSongs
      }
    }
    return json.dumps(jsonData)
  

  ## offset = 100, 200
  def episInfo(self, id, offset):
    url= f"{self.BaseUrl}/anime/{id}/name/episode?offset={offset}"
    data = get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    epis = soup.select(".js-watch-episode-list tbody tr")

    epis_info_json = [{"epNo": int(x.select(".episode-number")[0].text),
                       "title": x.select(".episode-title a")[0].text,
                       "aired": x.select(".episode-aired")[0].text,
                       "link": x.select(".episode-title a")[0]["href"],
                       "isFiller": True if len(x.select(".icon-episode-type-bg")) != 0 else False
                       }
                      for x in epis]

    return json.dumps(epis_info_json)


  def animeCharacters(self, malid):
    data = get(f"{self.BaseUrl}/anime/{malid}/animeName/characters")
    soup = BeautifulSoup(data.text, "lxml")
    charactersList = soup.select(".anime-character-container table tr")
    x = []

    for character in charactersList:
        cName = character.select(".js-chara-roll-and-name")
        if cName:
            voice_actorInfo = character.select(".js-anime-character-va .js-anime-character-va-lang")
            voice_actor_json = {}
            if voice_actorInfo:
                voice_actor_json = {
                    "name": voice_actorInfo[0].select_one('td .spaceit_pad').text.strip(),
                    "img": voice_actorInfo[0].select_one('td img')['data-srcset'].split(", ")[1].replace(" 2x", "").split("?s=")[0].replace("https://cdn.myanimelist.net/r/84x124/images/", ""),
                    "lang": voice_actorInfo[0].select_one('.js-anime-character-language').text.strip()
                }

            cINfoJson = {
                "name": cName[0].text.strip().split("_")[1],
                "img": character.select_one(".ac img")["data-srcset"].split(" 1x, ")[1].replace(" 2x", "").split("?s=")[0].replace("https://cdn.myanimelist.net/r/84x124/images", ""),
                "type": "main" if cName[0].text.strip().split("_")[0] == "m" else "supporting",
                "voice_actors": voice_actor_json
            }
            x.append(cINfoJson)

    charactersInfo = {
        "mal_id": malid,
        "name": soup.select_one(".title-name").text,
        "data": x
    }
    return json.dumps(charactersInfo)


  def search(self,q,page):## Search Anime BY Name ##
    url = f"{self.BaseUrl}/anime.php?q={q}&cat=anime&&show={(page-1)*50}"
    data = get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    last_page = 20 
    animes = soup.select("#content div.list table tr")
    del animes[0]
    dataDict = {
      "pagination":{
        "next_page": True if page < last_page else False,
        "prev_page": True if page > 1 else False,
        "page": page
      },
      "items": [{
          "title": anime.select(".title a")[0].text,
          "mal_id": int(anime.select(".picSurround a")[0]["href"].replace("https://myanimelist.net/anime/","").split("/")[0]),
          "type": anime.select(".ac")[0].text.strip(" \n"),
          "url": anime.select(".picSurround a")[0]["href"],
          "imgs": {
            "jpg":{
              "small": (anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x",""),
              "medium": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0],
              "large": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", "l.jpg")
            },
            "webp": {
              "medium": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", ".webp"),
              "large": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", "l.webp")
            }
          },
          "score": (anime.select(".ac")[2].text.strip(" \n"))
        } for anime in animes]}
    return json.dumps(dataDict)
     
  def ajaxSearch(self, q): 
    url = f"{self.BaseUrl}/anime.php?q={q}&cat=anime"
    data = get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    animes = soup.select("#content div.list table tr")
    del animes[0]
    dataDict = [{
          "title": anime.select(".title a")[0].text,
          "type": anime.select(".ac")[0].text.strip(" \n"),
          "url": anime.select(".picSurround a")[0]["href"],
          "img": anime.select(".picSurround img")[0]["data-srcset"].split(" 1x, ")[1].replace(" 2x",""),
        } for anime in animes]
    return json.dumps(dataDict)


##   type "", "airing", "upcoming", "tv", "movie", "ova", "ona", "special", "bypopularity", "favorite"  
##  url  https://myanimelist.net/topanime.php
  def topAnime(self, type, page):
    url = f"{self.BaseUrl}/topanime.php?type={type}&limit={50*(int(page) - 1)}"
    data = get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    next = soup.select(".pagination .next")
    prev = soup.select(".pagination .prev")
    pagination = {
      "next_page": (False if len(next) == 0 else True),
      "prev_page": (False if len(prev) == 0 else True),
      "page": int(page)
    }
    animes = soup.select(".ranking-list")
    data_dict = {
      "pagination" : pagination,
      "items": [
        {
          "title": anime.select(".anime_ranking_h3")[0].text,
          "mal_id": anime.select("a")[0]["href"].replace("https://myanimelist.net/","").split("/")[1],
          "type": anime.select("a")[0]["href"].replace("https://myanimelist.net/","").split("/")[0],
          "url": anime.select("a")[0]["href"],
          "imgs": {
            "jpg":{
              "small": (anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x",""),
              "medium": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0],
              "large": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", "l.jpg")
            },
            "webp": {
              "medium": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", ".webp"),
              "large": "".join((anime.select("img")[0]["data-srcset"].split(", ")[1]).replace(" 2x","").split("r/100x140/")).split("?s=")[0].replace(".jpg", "l.webp")
            }
          },
          "rank": anime.select(".top-anime-rank-text")[0].text,
          "score": anime.select("td.score.ac.fs14 > div > span")[0].text,
          "otherInfo": anime.select(".information")[0].text.strip()
        } for anime in animes
      ]
    }
    return json.dumps(data_dict)
  


  def relatedAnime(self, url):   ## get related animes ##
    data = get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    relatedAnilist = soup.select("#relations_direct")
    return soup   ##  ** 403 Forbidden **  ##
  

if __name__ == "__main__":
  print(mal().relatedAnime("https://anidb.net/anime/4880"))

##relations_direct