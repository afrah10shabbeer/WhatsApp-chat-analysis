#!/usr/bin/env python
# coding: utf-8



import regex
import re
import pandas as pd
import numpy as np
from collections import Counter
import plotly.express as px

from wordcloud import STOPWORDS,WordCloud
import matplotlib.pyplot as plt



# Function to extract emojis if present in a line
def split_count(text):
    emoji_list = []
    emoji_pattern = re.compile("["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        u"\U00002702-\U000027B0"  # dingbats
                        u"\U000024C2-\U0001F251" 
                        "]+", flags=re.UNICODE)
    
    emoji_list = emoji_pattern.findall(text)
    return emoji_list



# Function to check if the message is a new message by checking data and time
def has_date_and_time(str):
    
    pattern = pattern = r'^(\d{2})/(\d{2})/(\d{2}), (\d{1,2}):(\d{2})\s?([ap]m)'
    
    pattern_match = regex.match(pattern,str)
    return pattern_match
    


# Function to extract details like date,time person name and message
def extract_details(line):

    splitLine = line.split('-')
    dateTimeLine = splitLine[0].split(',')
    
    date = dateTimeLine[0]
    time = dateTimeLine[1]
    
    personMessageLine = splitLine[1]
    
    colon_index = personMessageLine.find(':')
    
    if colon_index != -1:
        person_name = personMessageLine[:colon_index].strip()
        message = personMessageLine[colon_index+1:].strip()
    else:
        person_name = None
        message = personMessageLine.strip()
    
    # Removing any escape sequence characters if there are any
    # using regular expression
    
    pattern = r'\\[uUxX][a-fA-F0-9]+'
    
    date = re.sub(pattern,"",date)
    time = re.sub(pattern,"",time)
    person_name = re.sub(pattern,"",person_name)
    message = re.sub(pattern,"",message)
    
    return date, time, person_name, message
    


# ---------------------------- Main class -----------------------------------
class WhatsAppChatAnalyzer:

    def __init__(self,conversation_file):

        self.__conversation_file = conversation_file
        self.__chat_df = None
        self.__media_messages_df = None
        self.__messages_df = None
        self.__first_date = None
        self.__last_date = None


    def preprocess_chat_data(self):

        data_list = []
        is_first_date = True


        # conversation_file = "WhatsApp Chat with Feroz.txt"
        with open(self.__conversation_file,encoding="utf-8") as fp:
            
            fp.readline()
            messageBuffer = []

            data, time, person_name = None, None, None
            while True:

                line = fp.readline()

                # Represents End of line
                if not line: 
                    break
                
                line = line.strip()
                
                if has_date_and_time(line): 

                    # New message has began, append the old message to data_list
                    if len(messageBuffer) > 0:
                        data_list.append([date,time,person_name,' '.join(messageBuffer)])
                    
                    messageBuffer.clear()
                
                    date, time, person_name, message = extract_details(line)

                    # Capturing the starting date of conversation
                    if is_first_date == True:
                        self.__first_date = date
                        is_first_date = False

                    # Capturing the last date of conversation
                    self.__last_date = date

                    messageBuffer.append(message)

                else:
                    messageBuffer.append(line)


        self.__chat_df = pd.DataFrame(data_list,columns = ["Date","Time","Author","Message"])
        self.__chat_df["Emojis"] = self.__chat_df["Message"].apply(split_count)
        
        URL_PATTERN = r'(https?://\S+)'    
        self.__chat_df['url_count'] = self.__chat_df["Message"].apply(lambda x:regex.findall(URL_PATTERN,x)).str.len()

        self.__media_messages_df = self.__chat_df[self.__chat_df["Message"] == "<Media omitted>"] # Only media files messages df
        self.__messages_df = self.__chat_df.drop(self.__media_messages_df.index) # Only textual message df

        self.__messages_df["Letter_count"] = self.__messages_df["Message"].apply(lambda s:len(s)) # Count length of each message
        self.__messages_df["Word_count"] = self.__messages_df["Message"].apply(lambda s:len(s.split(' '))) # Count number of words
        self.__messages_df["Message_count"] = 1

            
    # ================================ Get author names (Util) ======================================= 
    def get_author_names_list(self):

        author_names_list = self.__chat_df["Author"].unique()
        return author_names_list

    # ======================= Get beginning and ending date of the conversation (Util) =========================
    def get_first_and_last_date(self):
        return self.__first_date,self.__last_date
    


    # ================================ Total messages =========================================
    def get_total_messages(self):

        total_messages = self.__chat_df.shape[0]
        return total_messages
    
        
    # ======================= Total media messages(images,videos etc) ===============================
    def get_total_media_messages(self):

        media_messages = self.__chat_df[self.__chat_df["Message"] == '<Media omitted>'].shape[0]
        return media_messages
    


    # ============================== Total emojis present =========================================
    def get_total_emojis(self):

        emoji_count = sum(self.__chat_df["Emojis"].str.len())

        return emoji_count


    # ========================= Total number of URLs present ===============================
    def get_url_count(self):

        

        links_count = np.sum(self.__chat_df["url_count"])

        return links_count


    # =============================== Detailed Analysis ====================================

    def print_detail_stats(self,author_name):

        print(f"\n============================= Detail stats of {author_name} ==============================")
        # Filtering out messages of particular user
        req_person_df = self.__messages_df[self.__messages_df["Author"] == author_name]
        
        # Number of rows(Messages sent)
        total_messages_sent = req_person_df.shape[0]
        print(f"Messages sent: {total_messages_sent}")
        
        # Average words per message
        words_per_message = (np.sum(req_person_df["Word_count"]))/total_messages_sent
        print(f"Average words per message: {words_per_message}")
        
        # Total media messages
        total_media_messages = self.__media_messages_df[self.__media_messages_df["Author"] == author_name].shape[0] 
        print(f"Total media messages: {total_media_messages}")
        
        # Total emojis sent
        total_emojis = sum(req_person_df["Emojis"].str.len())
        print(f"Total emojis sent: {total_emojis}")
        
        # Total number of links
        total_links = sum(req_person_df["url_count"])
        print(f"Total Link sent: {total_links}")
        
        print("\n")
        
    
    # ================================== Visualisation of Emojis =================================
    def show_emoji_visualisation(self,author_name):

        print(f"\n============================= Emoji stats of {author_name} ==============================")
        # Filtering out messages of particular user
        req_person_df = self.__messages_df[self.__messages_df["Author"] == author_name]
        
        # ---------- Counting total number of unique emojis used by both the authors -----------
        unique_emoji_list = list(set([emoji for emoji_list in req_person_df["Emojis"] for emoji in emoji_list]))
        unique_emojis_count = len(unique_emoji_list)
        print(f"Unique emoji count:{unique_emojis_count}")

        # ------------- lists out all the emojis used by both the authors -------------------
        emoji_list = [emoji for emoji_list in req_person_df["Emojis"] for emoji in emoji_list]

        split_emoji_list = []
        for emojis in emoji_list:
            for e in emojis:
                split_emoji_list.append(e)


        # ----------- This counts the occurrences of each unique emoji in the total_emojis_list --------------
        emoji_freq_dict = dict(Counter(split_emoji_list))

        # ------------- Sorts the dictionary based on frequency in decreasing order -------------
        emoji_freq_dict = sorted(emoji_freq_dict.items(), key=lambda x: x[1], reverse=True)

        emoji_df = pd.DataFrame(emoji_freq_dict, columns = ["Emoji","Count"])
        

        figure = px.pie(emoji_df,values = "Count", names = "Emoji")
        figure.update_traces(textposition = "inside", textinfo = "percent+label")
        
        # Update the title
        figure.update_layout(title=f"Emoji visualisation of {author_name}")
        figure.show()

        
        
    # ===================== Most frequent words used by a particular user =========================

    def show_frequent_word_cloud(self,author_name):

        temp_df = self.__messages_df[self.__messages_df["Author"] == author_name]
        
        # Most used words by particular author
        text = " ".join(review for review in temp_df["Message"])
        words = len(text.split(' '))

        # print(f"There are {words} words in all the messages")
        stopwords = set(STOPWORDS)

        # Generate a word cloud image
        wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)

        # Display the generated image:
        # the matplotlib way:
        plt.figure(figsize=(10,5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.title(f"Most frequent words used by {author_name}")
        plt.axis("off")
        plt.show()

    
    
def main():

    # Main logic of the program goes here

    chat_file_path = "WhatsApp_chat_analysis/WhatsApp Chat with Bob.txt"
    object = WhatsAppChatAnalyzer(chat_file_path)

    object.preprocess_chat_data()
    author = object.get_author_names_list()
    date = object.get_first_and_last_date()


    print(f" ==================== Stats count of {author[0]} and {author[1]} from {date[0]} to {date[1]} ===================")

    print(f"Messages: {object.get_total_messages()}")
    print(f"Media messages: {object.get_total_media_messages()}")
    print(f"Emojis: {object.get_total_emojis()}")
    print(f"URLS count: {object.get_url_count()}")
    
    object.print_detail_stats(author[0])
    object.print_detail_stats(author[1])

    object.show_emoji_visualisation(author[0])
    object.show_emoji_visualisation(author[1])

    object.show_frequent_word_cloud(author[0])
    object.show_frequent_word_cloud(author[1])



# Check if the current module is the main module
if __name__ == "__main__":
    main()



