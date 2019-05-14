import requests
import os
import csv
from time import sleep
import json

class Movie():
    def __init__(self):
        pass
    def set_movie_info(self, code, name, day, date):
        self.code = code
        self.name = name
        self.day = day
        self.date = date
    
    def set_movie_detail(self,name_kor,genre, pd):
        self.title = name_kor
        self.genre = genre
        self.pd = pd
    
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
        temp_genre = doc["movieInfoResult"]["movieInfo"]["genres"]
        genre = []
        for temp in temp_genre:
            if temp["genreNm"] not in genres:
                genres.append(temp["genreNm"])
            genre.append(genres.index(temp["genreNm"])+1)

        pd = doc["movieInfoResult"]["movieInfo"]["directors"][0]["peopleNm"]
        m.set_movie_detail(name_kor,genre, pd)
        new_movie.append({"pk":pk, "model":"movies.movie", "fields":{"title":name_kor, "genre":genre, "director":pd}})
        pk+=1
    return new_movie
    
def writeMovieDetail(filename, movie):
    # with open('movie.csv', 'w', encoding='utf-8', newline="") as f:
    #     fieldnames = ['title','genres','directors']
    #     w = csv.DictWriter(f, fieldnames=fieldnames)
    #     w.writeheader()
    #     for m in movie:
    #         w.writerow({'title': m.name_kor,''genres': m.genre,'directors': m.pd,'watch_grade_nm': m.level,'actor1': m.actor1,'actor2': m.actor2,'actor3': m.actor3})
    base_url = "https://openapi.naver.com/v1/search/movie?query="
    headers = {
        'X-Naver-Client-Id': naver_key,
        'X-Naver-Client-Secret': naver_secret
    }
    pk=0
    for m in movie:
        url = base_url + m['fields']['title']
        res = requests.get(url,headers=headers).json()
        m['fields']['image']=res['items'][0]['image']
        m['fields']['naver_link']=res['items'][0]['link']
        m['fields']['user_Rating']=res['items'][0]['userRating']
        sleep(1) #속도 제한 조건 때문에 설정
    with open("movie.json","w", encoding="utf-8") as f:
        json.dump(movie, f, ensure_ascii=False)

def getNaverMovie(movie, base_url, headers):
    for m in movie:
        url = base_url + m.name_kor
        res = requests.get(url,headers=headers).json()
        #print(res)
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
    genres = []
    movie = []
    movie_key = '57c567fe90e0a70ffd32f569562e1a40'
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
