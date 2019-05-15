import requests
import os
import csv
from time import sleep
import json
from bs4 import BeautifulSoup

class Movie():
    def __init__(self):
        pass
    def set_movie_info(self, code, name, day, date):
        self.code = code
        self.name = name
        self.day = day
        self.date = date
    
    def set_movie_detail(self,name_kor,genre, pd, nation, openDate, watchGrade, duration):
        self.title = name_kor
        self.genre = genre
        self.pd = pd
        self.nation = nation
        self.openDate = openDate
        self.watchGrade = watchGrade
        self.duration = duration
    
    def set_naver_movie(self,thumb_url, link_url, user_rating):
        self.thumb_url = thumb_url
        self.link_url = link_url
        self.user_rating = user_rating
    
def getWeeklymovie(days, movie_key, WeekGb, movie):

    redundant = set()
    for i in range(len(days)):
        date = days[i]
        movie_url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json?key={}&targetDt={}&weekGb={}".format(movie_key, date, WeekGb)
        doc = requests.get(movie_url).json()
        #대표코드, 영화명, 해당일 누적 관객수, 해당일
        movie_code = [doc["boxOfficeResult"]["weeklyBoxOfficeList"][j]["movieCd"] for j in range(10)]
        movie_name = [doc["boxOfficeResult"]["weeklyBoxOfficeList"][j]["movieNm"] for j in range(10)]
        movie_day = [doc["boxOfficeResult"]["weeklyBoxOfficeList"][j]["audiAcc"] for j in range(10)]

        for k in range(10):
            if movie_code[k] in redundant:
                for z in movie:
                    if z.code == movie_code[k]:
                        z.set_movie_info(movie_code[k],movie_name[k],movie_day[k],date)
                    break
                continue
            m = Movie()
            m.set_movie_info(movie_code[k],movie_name[k],movie_day[k],date)
            movie.append(m)
        redundant = redundant.union(set(movie_code))
    return movie

def writeWeeklymovie(filename, movie):
    with open(filename, 'w', encoding='utf-8', newline="") as f:
        fieldnames = ['movie_code','title','audience','recorded_at']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for m in movie:
            w.writerow({'movie_code':m.code, 'title': m.name, 'audience': m.day, 'recorded_at': m.date})

def getMovieDetail(movie_key, movie):
    new_movie = []
    pk = 1
    for m in movie:
        movie_url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={}&movieCd={}".format(movie_key, m.code)
        doc = requests.get(movie_url).json()
        name_kor = doc["movieInfoResult"]["movieInfo"]["movieNm"]
        nation = doc["movieInfoResult"]["movieInfo"]["nations"][0]["nationNm"]
        openDate = doc["movieInfoResult"]["movieInfo"]["openDt"]
        watchGrade = doc["movieInfoResult"]["movieInfo"]['audits'][0]['watchGradeNm']
        duration = doc["movieInfoResult"]["movieInfo"]["showTm"]

        temp_genre = doc["movieInfoResult"]["movieInfo"]["genres"]
        genre = []
        for temp in temp_genre:
            if temp["genreNm"] not in genres:
                genres.append(temp["genreNm"])
            genre.append(genres.index(temp["genreNm"])+1)

        pd = doc["movieInfoResult"]["movieInfo"]["directors"][0]["peopleNm"]
        m.set_movie_detail(name_kor,genre, pd, nation, openDate, watchGrade, duration)
        new_movie.append({"pk":pk, "model":"movies.movie", 
        "fields":{"title":name_kor, "genre":genre, "director":pd, "nation":nation, "openDate": openDate,
        "watchGrade": watchGrade, "duration":duration}})
        pk+=1
    return new_movie
    
def writeMovieDetail(filename, movie):
    global i
    global image_model
    base_url = "https://openapi.naver.com/v1/search/movie?query="
    headers = {
        'X-Naver-Client-Id': naver_key,
        'X-Naver-Client-Secret': naver_secret
    }
    pk=0
    for m in movie:
        url = base_url + m['fields']['title']
        res = requests.get(url,headers=headers).json()
        # m['fields']['image']=res['items'][0]['image']
        m['fields']['naver_link']=res['items'][0]['link']
        naver_link = res['items'][0]['link']
        movie_code = naver_link[naver_link.index('=')+1:]
        # 이미지 가져오기
        naver_imgUrl = 'https://movie.naver.com/movie/bi/mi/photoViewPopup.nhn?movieCode='+movie_code
        doc = requests.get(naver_imgUrl).text
        doc = BeautifulSoup(doc, 'html.parser')
        temp_img = doc.select_one('#targetImage')['src']
        m['fields']['image'] = temp_img

        # 줄거리 가져오기
        doc = requests.get(naver_link).text
        doc = BeautifulSoup(doc, 'html.parser')
        
        temp_summary = doc.find('p',{'class':'con_tx'})
        if temp_summary:
            temp_summary = temp_summary.text
            temp_summary = temp_summary.replace('\r','')
            m['fields']['summary'] = temp_summary
        else:
            m['fields']['summary'] = ''
        
        # 누적 관객수 가져오기
        temp_audience = doc.find('p',{'class':'count'})
        if temp_audience:
            temp_audience = temp_audience.text
            ind = temp_audience.index('명')
            m['fields']['audience'] = temp_audience[:ind]
        else:
            m['fields']['audience'] = ''

        # 예매 링크
        temp_reserve = doc.select_one('#reserveBasic')
        if temp_reserve:
            m['fields']['reservation'] = 'https://movie.naver.com'+temp_reserve['href']
        else:
            m['fields']['reservation']=''

        # 관련 사진
        photo_url = 'https://movie.naver.com/movie/bi/mi/photoView.nhn?code='+movie_code
        doc = requests.get(photo_url).text
        doc = BeautifulSoup(doc, 'html.parser')
        photos = doc.findAll('li',{'class':'_list'})
        temp_photos = []

        for photo in photos:
            temp_i = photo['data-json'].index('886px')
            temp_end = photo['data-json'].index(',"viewCount"')
            temp_photos.append(photo['data-json'][temp_i+8:temp_end-1])
        # print(temp_photos)
        # print(m)
        for photo in temp_photos:
            image_model.append({"pk":i, "model":"movies.image", "fields":{"movie":m["pk"], "url":photo}})
            i+=1
        # m['fields']['otherimages'] = temp_photos

        # 유저 평점
        m['fields']['user_Rating']=res['items'][0]['userRating']
        sleep(1) #속도 제한 조건 때문에 설정
    print(movie)
    with open("movie.json","w", encoding="utf-8") as f:
        json.dump(movie, f, ensure_ascii=False)

    with open("image.json","w",encoding="utf-8") as f:
        json.dump(image_model, f, ensure_ascii=False)

    

def getNaverMovie(movie, base_url, headers):
    for m in movie:
        url = base_url + m.name_kor
        res = requests.get(url,headers=headers).json()
        m.set_naver_movie(res['items'][0]['image'],res['items'][0]['link'], res['items'][0]['userRating'])
        sleep(1) #속도 제한 조건 때문에 설정
    return movie

def writeNaverMovie(filename, movie):
    with open(filename, 'w', encoding='utf-8', newline="") as f:
        fieldnames = ['movie_code','thumb_url','link_url','user_rating']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for m in movie:
            w.writerow({'movie_code': m.code,'thumb_url': m.thumb_url,'link_url': m.link_url,'user_rating': m.user_rating})

def writeMovieImages(movie):
    for m in movie:
        img_data = requests.get(m.thumb_url).content
        with open('./images/'+m.code+'.jpg', 'wb') as handler:
            handler.write(img_data)

if __name__ == '__main__':
    i = 1
    genres = []
    movie = []
    image_model = []
    movie_key = '53cb2d2cf4ad6a79314fcaa91d0f977b'
    naver_key = 'hCvX9KPAqQcNFOw85TMe'
    naver_secret = 'QIXciwWY1b'
    days = ["20190310","20190317","20190324","20190331","20190407","20190414","20190421","20190428","20190505","20190512"]
    WeekGb = "0"
    naver_base_url = "https://openapi.naver.com/v1/search/movie?query="
    headers = {
        'X-Naver-Client-Id': naver_key,
        'X-Naver-Client-Secret': naver_secret
    }

    movie = getWeeklymovie(days, movie_key, WeekGb, movie ) # 10주간 박스오피스 정보를 담은 리스트 가져오기
    writeWeeklymovie('boxoffice.csv',movie)
    movie = getMovieDetail(movie_key, movie)
    writeMovieDetail('movie.csv', movie)
    print(genres)
    # movie = getNaverMovie(movie, naver_base_url, headers)
    # writeNaverMovie('movie_naver.csv',movie)
    # os.mkdir('./images/')
    # writeMovieImages(movie)
