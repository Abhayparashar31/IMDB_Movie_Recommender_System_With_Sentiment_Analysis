import pickle
import streamlit as st
import requests
import imdb_scraper as imdb
import hydralit_components as hc
import time
import json
from streamlit_lottie import st_lottie

st.set_page_config(
    page_title = "IMDB Movies Recommender System",
    page_icon = "🎞️"
)

st.markdown(
    """
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    """,
    unsafe_allow_html=True,
)


### pip install streamlit_lotte
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_coding = load_lottiefile("data/home.json")

st_lottie(
    lottie_coding,
    speed=1,
    reverse=False,
    loop=True,
    quality="low",height=200
)



### Adding Title and Subtitle For Web App
st.markdown('''# **IMDB Movies Recommender System**''')


### Unpickling Pickled Data
df = pickle.load(open('df.pkl','rb'))
similarity = pickle.load(open('similarity_tf.pkl','rb'))


#### Dropdown input For Selecting a Movie
movie_name = st.selectbox('Choose The Latest Movie You Have Watched From The List.',df['title'].values)

def fetch_user_input_movie_details(movieName):

    ####### Information About The Movie User Selected
    #### ALL THE BASIC INFO (CAST,MOVIE_POSTER,DIRECTOR,GENRES,OVERVIEW,RELEASE_DATE,RUNTIME,RATINGS,BOXOFFICE,IMDBID)
    #### SOME RANDOM FACTS ABOUT THE MOVIE FROM IMDB (IF POSSIBLE)

    movie_index = df[df["title"].str.lower() == movieName.lower()].index[0]
    row = df.iloc[movie_index]
    
    #### MOVIE NAME
    movie_name = row["title"]

    #### MOVIE POSTER
    poster = fetch_movie_poster(row['id'])

    #### GENRES
    genre = row['genres']
    genre = ','.join(genre)

    #### CAST
    cast = row['cast']
    cast = ','.join(cast)

    #### OVERVIEW
    overview = row['overview']
    overview = overview[:200]

    #### Director
    director = row['Director']

    #### Runtime 
    minutes = row['runtime']
    runtime = "{:.2f}".format(minutes.astype(int)/60).split('.')[0]+' hr'+" "+"{:.2f}".format(minutes.astype(int)/60).split('.')[1]+" min"

    #### Release Date
    y_m_d = row['release_date']
    release_date = "-".join(y_m_d.split('-')[::-1])

    #### imdbRating, imdbID, Box Office
    imdb_rating,imdb_id,boxoffice = imdb.API(movie_name)

    #### Little Web Scraping For Fun Fact
    try:
        trivia = imdb.movie_trivia(imdb_id)
    except:
        trivia = [0]


    return movie_index,poster,movie_name,genre,cast,overview,director,minutes,runtime,release_date,imdb_rating,imdb_id,boxoffice,trivia
    

    ####  
    pass

#### Fetch Movie Poster Using TMDB API
def fetch_movie_poster(movieID):
    ### Preparing API URL
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movieID}?api_key=e56c4aba950e590a34561709774c5922')
    
    ### Retriving Data In The Form of JSON
    data = response.json()

    ### Extracting The Poster Path From JSON Data
    posterPath = "http://image.tmdb.org/t/p/w500" + data['poster_path']

    ### Returing The Poster Path To The recommend_movie Function
    return posterPath


def movie_providers(mid):
    res = requests.get(f'https://api.themoviedb.org/3/movie/{mid}/watch/providers?api_key=e56c4aba950e590a34561709774c5922')
    
    ### Retriving Data In The Form of JSON
    APIData = res.json()
    whole = APIData['results']
    try:
        countryIN = whole['IN']
    except:
        countryIN = whole['US']
    for key in countryIN.keys():
        if key=='flatrate':
            IN = countryIN['flatrate']
            break
        else:
            key = list(countryIN.keys())[1]
            IN = countryIN[key]
    providers = [provider['provider_name'] for provider in IN]
    return ", ".join(providers)

def convert_predictions(predictions):
    converted = ['Positive 😀' if x==1 else 'Negative 😞' for sentence in predictions for x in sentence]
    return [converted[i:i+5] for i in range(0, len(converted), 5)]   

#### Recommedn Movie Function To Recommend Movie and Return Poster Path
def recommend_movies(movie_name):
    ### Empty Lists For Storing Movies and Posters
    recommended_movies = []
    movies_poster = []
    cast = []
    director = []
    genres = []
    overview = []
    release_date = []
    runtime = []
    ratings = [] 
    boxoffices = []
    imdbids = [] 
    providers = []
    verdicts = []
    reviews = []
    predictions = []

    # Get Index of given Movie
    movie_index = df[df["title"].str.lower() == movie_name.lower()].index[0]

    ### Movie Similary Distance
    listofMovies = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x:x[1])[1:6]            ### CHANGE 4 TO A BIGGER NUMBER TO RECOMMENDED MORE MOVIES
    listofMovies = sorted(listofMovies,key=lambda x:df["popularity"][x[0]],reverse=True)

    
    for i in listofMovies[:5]:
        ### Extracting Movie Name
        recommended_movies.append(df.iloc[i[0]]["title"])

        ### Extracting Movie ID using the Index and Passing it to the API
        movies_poster.append(fetch_movie_poster(df.iloc[i[0]]["id"]) )
        
        ### Extract Cast
        cast.append(", ".join(df.iloc[i[0]]['cast']))

        ### Extract Director
        director.append(df.iloc[i[0]]['Director'])

        ### Extract Genres
        genres.append(", ".join(df.iloc[i[0]]['genres']))

        ### Extract Overvoew
        overview.append(df.iloc[i[0]]['overview'][:100]+'....')                    ##### CHANGE THE VALUE 100 TO A BIGGER VALUE FOR A BIG OVERVIEW TEXT

        ### Extract Release Date
        y_m_d = df.iloc[i[0]]['release_date']
        d_m_y = "-".join(y_m_d.split('-')[::-1])
        release_date.append(d_m_y)

        ### Extract Runtime
        minutes = df.iloc[i[0]]['runtime']
        hr_min = "{:.2f}".format(minutes.astype(int)/60).split('.')[0]+' hr'+" "+"{:.2f}".format(minutes.astype(int)/60).split('.')[1]+" min"
        runtime.append(hr_min)   

        ### Extract Popularity and IMDB Rating, Box Office Collection and IMDB Movie ID
        recommend_movie_name = df.iloc[i[0]]["title"]
        
        rating, boxoffice, imdbid, verdict,review,prediction = imdb.imdb_data(recommend_movie_name)
        
        ratings.append(rating)
        boxoffices.append(boxoffice)
        imdbids.append(imdbid)
        verdicts.append(verdict)
        reviews.append(review)
        predictions.append(prediction)

        ### Providers
        providers.append(movie_providers(df.iloc[i[0]]["id"]))
        

    predictions = convert_predictions(predictions)
    print(predictions)
    #### Renaming Prediction


    ### Returning The Recommended Movie and Posters    
    return recommended_movies, movies_poster,cast,director,genres,overview,release_date,runtime,ratings, boxoffices, imdbids, verdicts,providers,reviews,predictions



######### USER CHOICE MOVIE DETAILS ##########
movie_index,poster,movie_name,genre,cast,overview,director,minutes,runtime,release_date,imdb_rating,imdb_id,boxoffice,trivia = fetch_user_input_movie_details(movie_name)
colA,colB = st.columns(2)
with colA:
    st.markdown("""――――――――――――――――――――――――――――――――――――――――――――――――――――""")
    st.image(poster)
    st.markdown("""<hr style="height:25px; border:2px solid white; color:#ffffff; background-color:#ffffff;" /> """, unsafe_allow_html=True)
with colB:
    st.subheader(movie_name)
    st.write('IMDB ID: ',imdb_id)
    st.write(''' **Overview**:''',overview)
    st.write('**Release Date**:',release_date)
    st.write('''**IMDB Rating**: ''',imdb_rating,"/10")
    st.write(''' **Director**: ''',director[0])
    st.write(''' **Star Cast**: ''',cast)
    st.write(''' **Genres**: ''',genre)
    st.write(''' **Box Office Collection**: ''',boxoffice)
    st.write('Runtime: ',runtime)

    st.write('\n')

if len(trivia)>1:
    st.subheader('Did You Know? 😲')
    st.write(f'*{trivia[0]}*')
    st.write(f'*{trivia[1]}*')
    st.write(f'*{trivia[2]}*')
    st.write(f'*{trivia[3]}*')
    st.write(f'*{trivia[4]}*')
    st.write(f'*{trivia[5]}*')
    st.write(f'*{trivia[6]}*')

st.write('\n')
recommend = st.button('Recommend Movies')
st.write('\n')


if recommend:
    
    with hc.HyLoader('Loading Recommended Movies 📽️.. ',hc.Loaders.pacman):
        movie_names,movie_posters,cast,director,genres,overview,release_date,runtime,rating, boxoffice, imdbid, verdict,providers,reviews,predictions = recommend_movies(movie_name)

    st.header('Top 5 Recommended Movies 📽️')
    for i in range(0,5):
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("""---""")
            st.image(movie_posters[i])
            st.markdown("""---""")

        with col2:
            st.subheader(movie_names[i])
            st.write('IMDB ID: ',imdbid[i])
            st.write(''' **Overview**:''',overview[i])
            st.write('**Release Date**:',release_date[i])
            st.write('''**IMDB Rating**: ''',rating[i],"/10")
            st.write(''' **Director**: ''',director[i][0])
            st.write(''' **Star Cast**: ''',cast[i])
            st.write(''' **Genres**: ''',genres[i])
            st.write(''' **Box Office Collection**: ''',boxoffice[i])
            st.write('Runtime: ',runtime[i])
            st.write('''##### Verdict:''',verdict[i])
            st.write(''' **Providers**: ''',providers[i])
            st.write('\n')

        st.write(''' ##### **Some Reviews From Other Users About The Movie** 🎞️ ''')
        r1,r2,r3,r4,r5 = st.columns(5)
        
        with r1:
            st.write('''**Review 1**''')
            st.write(reviews[i][0][:150])    ### First Review of i th movie (First 200 words)
            st.write('\n**Kind**:',predictions[i][0])
        with r2:
            st.write('''**Review 2**''')
            st.write(reviews[i][1][:150])    ### First Review of i th movie
            st.write('\n**Kind**:',predictions[i][1])
        with r3:
            st.write('''**Review 3**''')
            st.write(reviews[i][2][:150])    ### First Review of i th movie
            st.write('\n**Kind**:',predictions[i][2])
        with r4:
            st.write('''**Review 4**''')
            st.write(reviews[i][3][:150])    ### First Review of i th movie
            st.write('\n**Kind**:',predictions[i][3])
        with r5:
            st.write('''**Review 5**''')
            st.write(reviews[i][4][:150])    ### First Review of i th movie
            st.write('\n**Kind**:',predictions[i][4])
        st.write(' --- \n')

############ LAST FIVE ##########

    def last_five(movie_name):
        movie_index = df[df["title"].str.lower() == movie_name.lower()].index[0]
        movies_six_to_ten = []
        movies_poster_six_to_ten = []
        ### Movie Similary Distance
        listofMovies = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x:x[1])[6:11]

        for i in listofMovies:
            movies_six_to_ten.append(df.iloc[i[0]]["title"])
            ### Extracting Movie ID using the Index and Passing it to the API
            movies_poster_six_to_ten.append(fetch_movie_poster(df.iloc[i[0]]["id"]) )

        return movies_six_to_ten,movies_poster_six_to_ten

    movies_sex_to_ten,movies_posters_six_to_ten = last_five(movie_name)
    st.subheader('OTHERS RECOMMENDED MOVIES YOU MIGHT LIKE 👍')
    st.markdown("""---""")
    cola,colb,colc,cold,cole = st.columns(5)
    with cola:
        st.image(movies_posters_six_to_ten[0])
        st.text(movies_sex_to_ten[0])
    with colb:
        st.image(movies_posters_six_to_ten[1])
        st.text(movies_sex_to_ten[1])
    with colc:
        st.image(movies_posters_six_to_ten[2])
        st.text(movies_sex_to_ten[2])
    with cold:
        st.image(movies_posters_six_to_ten[3])
        st.text(movies_sex_to_ten[3])
    with cole:
        st.image(movies_posters_six_to_ten[4])
        st.text(movies_sex_to_ten[4])  
    st.markdown("""---""") 


with st.expander("Know About The Creator"):
    st.write(''' ***Streamlit App Developed By Abhay Parashar***  ''') 
    st.write(''' **Find Him On**''')
    st.write(''' [**Medium**](https://abhayparashar31.medium.com/) | [**LinkedIN**](https://www.linkedin.com/in/abhayparashar31/) | [**GitHub**](https://github.com/abhayparashar31/)''')
    st.write('Sayonara !!!')



################################# FUTURE WORK #######################
######## DONE 1. GET THE IMDB RATING FOR RECOMMENDED MOVIE  [https://omdbapi.com/?t=Skyfall&apikey=cb28b445]   [IMDB ID, IMDB RATINGS, BOX OFFICE]
######## DONE 2. PERFORM SENTIMENT ANALYSIS ON REVIEWS AND GIVE A PROB LIKE USERS LIKE IT OR NOT (76% Users Like It)  [USING IMDB RATING]
######## DONE 3. Give Link To Avalible OTT Platforms of The Movie                 [USING IMDB RATING WITH AN API]
######## DONE 4. Provide Basic Info About USER SELECTED MOVIE
######## DONE 5. DID YOU KNOW? (ABOUT THE USER SELECTED MOVIE (SOME AMAZING TRIVIA FACTS))
######## 6. Provide Remaning 6-10 Movies Bottom Of the Page



############ OTHER 5 MOVIES WITH ONLY MOVIE NAME AND POSTER ###########


# score = []
# with open("file.txt", "r") as f:
#   for line in f:
#     score.append(int(line.strip()))
# print(score)


