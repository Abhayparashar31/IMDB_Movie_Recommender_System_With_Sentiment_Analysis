import requests
from bs4 import BeautifulSoup
import pickle
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import re



####### Loading Models For Sentiment Analysis
movie=pickle.load(open('movie.pkl','rb'))
moviecv=pickle.load(open('moviecv.pkl','rb'))



def movie_trivia(mid):
    url = f'https://www.imdb.com/title/{mid}/trivia'
    res = requests.get(url)
    soup = BeautifulSoup(res.text,'html.parser')
    trivia_text = soup.select('.sodatext')

    trivia = []
    for text in trivia_text:
        text = text.get_text()
        if len(text)<300:
            text = text.strip().replace('\n',"")
            trivia.append(text)
            if len(trivia)>7:
                break
    return trivia



def scrape_reviews(id):
    try:
        base_url = f'https://www.imdb.com/title/{id}/reviews'
        res = requests.get(base_url)
        soup = BeautifulSoup(res.text,'html.parser')
        review_list = []
        reviews = soup.select('.text')
        for review in reviews:
            review = review.get_text()
            review_list.append(review)

        #### Scraping Multiple Pages
        PAGE_LIMIT = 2                                               ### CHANGE PAGE LIMIT TO A BIGGER NUMBER TO SCRAPE REVIEWS FROM MORE PAGES
        current_page = 0
        try:
            while current_page<PAGE_LIMIT:
                data_key = soup.select('.load-more-data')
                key = data_key[0].attrs.get("data-key")
                url = f'https://www.imdb.com/title/{id}/reviews/_ajax?ref_=undefined&paginationKey={key}'
                res = requests.get(url)
                soup = BeautifulSoup(res.text,'html.parser')
                reviews = soup.select('.text')
                for review in reviews:
                    review = review.get_text()
                    review_list.append(review)
                current_page+=1
                print(f'Reviews Page {current_page} Scraped')

            return review_list
        except:
            ### Return Review List if Someting went wrong
            return review_list
    except:
        review_list = []
        return review_list


def clean(new_review):
    new_review = re.sub('[^a-zA-Z]', ' ', new_review)
    new_review = re.sub('<.*?>'," ",new_review)
    new_review = new_review.lower()
    new_review = new_review.split()
    ps = PorterStemmer()
    all_stopwords = stopwords.words('english')
    all_stopwords.remove('not')
    new_review = [ps.stem(word) for word in new_review if not word in set(all_stopwords)]
    new_review = ' '.join(new_review)
    new_corpus = [new_review] 
    return new_corpus 

def sentiment_analysis(reviews):
    predictions = []
    for review in reviews:
        corpus = clean(review)
        test_review = moviecv.transform(corpus).toarray()
        pred = movie.predict(test_review)
        predictions.append(pred[0])
    return predictions

def generate_percentage(predictions):
    from collections import Counter
    data = Counter(predictions).most_common()
    dictt ={}
    dictt[data[0][0]] = round((data[0][1]/(data[0][1]+data[1][1]))*100)
    dictt[data[1][0]] = round((data[1][1]/(data[0][1]+data[1][1]))*100)
    print(dictt)

    return f'Overall {dictt[1]}% People Liked This Movie'



### API To Retrive Information From IMBD Based On A Movie Name
def API(movieName):
    url = f'https://omdbapi.com/?t={movieName}&apikey=cb28b445'
    res = requests.get(url)

    data = res.json()
    try:
        imdb_rating = data['imdbRating']
    except:
        imdb_rating = ""
        
    imdb_id = data["imdbID"]
    boxoffice = data['BoxOffice']
    return imdb_rating,imdb_id,boxoffice


def imdb_data(movie_name):
    print(movie_name)

    imdb_rating,imdb_id,boxoffice = API(movie_name)
    #print(imdb_rating,imdb_id,boxoffice)
    
    reviews = scrape_reviews(imdb_id)

    # ### Dumping Reviews For Deployment Purpose
    with open("reviews.txt", "a",encoding="utf-8") as f:
        for review in reviews:
            f.write(review +"\n")


    predictions = sentiment_analysis(reviews)
    print(predictions)
    verdict = generate_percentage(predictions)
    print(verdict)
    return imdb_rating, boxoffice, imdb_id, verdict,reviews[:5],predictions[:5]


# #### Reading txt file
# reviews = []
# with open("reviews.txt", "r",encoding="utf-8") as f:
#   for line in f:
#     reviews.append(line.strip())
