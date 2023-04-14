from html.parser import HTMLParser

class RunnerHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.page_tokens = []

    def handle_starttag(self, tag, attrs):
        self.page_tokens.append(["initial_tag", tag])
        # print("< " + tag + " >")

    def handle_endtag(self, tag):
        self.page_tokens.append(["terminal_tag", tag])
        # print("</" + tag + " >")

    def handle_data(self, data):
        data = data.strip().lower()
        if data:
            self.page_tokens.append(["data", data])
        # print(data)

    def clear_page_tokens(self):
        self.page_tokens = []


def get_iterator_string(iterator):
    
    str_iter = "( "

    for token in iterator:
        if token[0] == "initial_tag":
            str_iter += "".join(["<", token[1],">"])
        elif token[0] == "terminal_tag":
            str_iter += "".join(["</", token[1],">"]) 
        elif token[0] == "optional":
            str_iter += token[1]+""
        else:
            str_iter += token[1]
    
    str_iter += " )+\n"

    return str_iter


def get_optional_string(optional):
    
    str_opt = "( "

    for token in optional:
        if token[0] == "initial_tag":
            str_opt += "".join(["<", token[1],">"])
        elif token[0] == "terminal_tag":
            str_opt += "".join(["</", token[1],">"]) 
        elif token[0] == "optional":
            str_opt += token[1]+""
        else:
            str_opt += token[1]
    
    str_opt += " )?\n"

    return str_opt

def write_final_wrapper_as_ufre(wrapper):
    
    ufre = ""

    for token in wrapper:
        if token[0] == "initial_tag":
            ufre += "".join(["<", token[1],">\n"])
        elif token[0] == "terminal_tag":
            ufre += "".join(["</", token[1],">\n"]) 
        elif token[0] == "optional":
            ufre += token[1]+"\n"
        elif token[0] == "iterator":
            ufre += get_iterator_string(token[1])
        else:
            ufre += token[1]+"\n"

    return ufre


def matching_tokens(token_1, token_2):

    if token_1[0] == token_2[0] and token_1[1] == token_2[1]:
        return True
    elif token_1[0] == "optional" and  token_1[1][1:-2] == token_2[1]:
        print("OPTIONAL MATCHING - MIGHT REQUIRE ADDITIONAL ATTENTION")
        return True

    return False

def find_iterator_end(tokens, start_indx):

    end_tag_found = False
    i = start_indx

    while i < len(tokens):

        if tokens[i][0] == "terminal_tag" and tokens[i][1] == tokens[start_indx][1]:
            end_tag_found = True
            break
        
        i += 1
    
    return end_tag_found, i

def find_prev_iterator_start(tokens, start_indx):

    start_tag_found = False
    i = start_indx

    while i > 0:

        if tokens[i][0] == "initial_tag" and tokens[i][1] == tokens[start_indx][1]:
            start_tag_found = True
            break
        
        i -= 1
    
    return start_tag_found, i

def find_end_of_optional(tokens, start_indx, tag):

    i = start_indx
    found = False

    while i < len(tokens)-1:

        if tokens[i][0] == "terminal_tag" and tokens[i][1] == tag:
            found = True
            break
        
        i += 1
    
    return found, i


def clean_wrapper_iterators(wrapper, iterator_tag, internal_wrapper):

    i = len(wrapper)-1

    new_end = None

    while i > 0:
    
        while i > 0 and wrapper[i][0] == "optional":
            i -= 1

        if wrapper[i][0] == "terminal_tag" and wrapper[i][1] == iterator_tag:
            
            while i > 0:

                if wrapper[i][0] == "initial_tag" and wrapper[i][1] == iterator_tag:
                    new_end = i
                    i -= 1
                    break
                i -= 1
        else:
            break

    if new_end is None:
        return wrapper

    # we found new wrapper
    wrapper = wrapper[:new_end]
    new_iterator = ["iterator", internal_wrapper]
    wrapper.append(new_iterator)

    return wrapper

def roadrunner(wrapper_tokens, sample_tokens, indx_w, indx_s, wrapper):

    
    if indx_w == len(wrapper_tokens) and indx_s == len(sample_tokens):
        # successful matching
        return wrapper

    wrap_token = wrapper_tokens[indx_w]
    smpl_token = sample_tokens[indx_s]

    # IF MATCHING TOKENS, SIMPLY APPEND TO THE WRAPPER
    if matching_tokens(wrap_token, smpl_token):
        wrapper.append(wrap_token)
        return roadrunner(wrapper_tokens, sample_tokens, indx_w+1, indx_s+1, wrapper)
    else:
        # handle string mismatch:
        if wrap_token[0] == "data" and smpl_token[0] == "data":
            wrapper.append(["data", "#PCDATA"])
            return roadrunner(wrapper_tokens, sample_tokens, indx_w+1, indx_s+1, wrapper)
        # tag mismatch - either an optional or an iterative
        else:
            iterative = True
            
            # check for iterative
            prev_wrap_token = wrapper_tokens[indx_w-1]
            prev_smpl_token = sample_tokens[indx_s-1]
            
            
            # iterator discovered on wrapper side
            if prev_wrap_token[0] == "terminal_tag" and wrap_token[0] == "initial_tag" and  prev_wrap_token[1] == wrap_token[1]:
                # confirm existance of equal terminal tag
                iter_found, iter_end_indx = find_iterator_end(wrapper_tokens, indx_w)
                
                if iter_found:

                    prev_iter_found, prev_iter_start_indx = find_prev_iterator_start(wrapper_tokens, indx_w-1)
                    
                    if prev_iter_found:
                        
                        prev_square = wrapper_tokens[prev_iter_start_indx:indx_w]
                        square = wrapper_tokens[indx_w:iter_end_indx+1]

                        internal_wrapper = roadrunner(prev_square, square, 0, 0, [])

                        if internal_wrapper is not None:
                            new_wrapper = clean_wrapper_iterators(wrapper, wrap_token[1], internal_wrapper)
                            return roadrunner(wrapper_tokens, sample_tokens, indx_w, iter_end_indx+1, new_wrapper)

                        else:
                            iterative = False
                    else:
                        iterative = False
                
                else:
                    iterative = False

            # iterator discovered on sample side
            elif prev_smpl_token[0] == "terminal_tag" and smpl_token[0] == "initial_tag" and  prev_smpl_token[1] == smpl_token[1]:
                # confirm existance of equal terminal tag
                iter_found, iter_end_indx = find_iterator_end(sample_tokens, indx_s)
                
                if iter_found:

                    prev_iter_found, prev_iter_start_indx = find_prev_iterator_start(sample_tokens, indx_s-1)
                    
                    if prev_iter_found:
                        
                        prev_square = sample_tokens[prev_iter_start_indx:indx_s]
                        square = sample_tokens[indx_s:iter_end_indx+1]

                        internal_wrapper = roadrunner(prev_square, square, 0, 0, [])

                        if internal_wrapper is not None:
                            wrapper = clean_wrapper_iterators(wrapper, smpl_token[1], internal_wrapper)
                            return roadrunner(wrapper_tokens, sample_tokens, indx_w, iter_end_indx+1, wrapper)

                        else:
                            iterative = False
                            
                    else:
                        iterative = False
                
                else:
                    iterative = False
            else:
                iterative = False


            # check for optional
            if not iterative:
                # option is present on wrapper
                if matching_tokens(wrapper_tokens[indx_w+1], smpl_token):
                    optional = ["optional", " ".join(["(", wrap_token[1],")?"])]
                    wrapper.append(optional)
                    return roadrunner(wrapper_tokens, sample_tokens, indx_w+1, indx_s, wrapper)
               
                elif matching_tokens(wrap_token, sample_tokens[indx_s+1]):
                    optional = ["optional", " ".join(["(", smpl_token[1],")?"])]
                    wrapper.append(optional)
                    return roadrunner(wrapper_tokens, sample_tokens, indx_w, indx_s+1, wrapper)
                else:
                    # print(": >>>> ", wrap_token, " vs ", smpl_token)
                    # print(": >>>> ", wrapper_tokens[indx_w+1], " vs ", smpl_token)
                    # print(": >>>> ", wrap_token, " vs ", sample_tokens[indx_s+1])
                    # print("ERROR MATCHING OPTIONAL !!! ")
                    return None


import requests
from bs4 import BeautifulSoup
from imdb import IMDb

def get_urls_from_top_movies():
    # Create an instance of the IMDb class
    imdb = IMDb()

    # Search for the top 1000 movies on IMDb
    movies = imdb.get_top250_movies()

    # Retrieve the IDs of the movies
    movie_ids = [movie.getID() for movie in movies[:250]]

    # print(len(movie_ids))
    # # Print the first 10 IDs
    # print(movie_ids[:10])
    movie_urls = []
    for movie_id in movie_ids:
        movie_urls.append(f'https://www.imdb.com/title/tt{movie_id}/')
        # print(movie_url)

    return movie_urls


def url_to_html_string(url):
    # Set the headers to simulate a web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    # Send a GET request to the URL and get the response
    response = requests.get(url, headers=headers)
    
    # Raise an exception if the response is not successful (status code 200-299)
    response.raise_for_status()
    
    # Parse the HTML content of the response using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Convert the soup object to a string and return it
    return str(soup)

import os
def read_file(filename):
    # directory containing the HTML files
    dir_path = "./test_pages/"
    with open(os.path.join(dir_path, filename + '.html'), "r") as f:
        return f.read()


def main():

    #Can't find a wrapper for imdb movies
    # urls = get_urls_from_top_movies()

    #Wrapper too generic for amazong listings, everything hides between a single PCDATA occurence (<script>#PCDATA</script)
    # urls = ['https://www.amazon.com/VIZIO-Chromecast-Mirroring-Streaming-Channels/dp/B092Q1TRJC/ref=sr_1_3?crid=2KLCABMWFNIO4&keywords=tv&qid=1681421080&sprefix=t%2Caps%2C300&sr=8-3&th=1',
    #         'https://www.amazon.com/Hisense-65-Inch-Vision-Compatibility-65R6G/dp/B08PDTM9ZD/ref=sr_1_4?crid=2KLCABMWFNIO4&keywords=tv&qid=1681421080&sprefix=t%2Caps%2C300&sr=8-4&th=1',
    #         'https://www.amazon.com/Hisense-55-Inch-Virtual-Chromecast-55A6H/dp/B09WQC4XJQ/ref=sr_1_5?crid=2KLCABMWFNIO4&keywords=tv&qid=1681421080&sprefix=t%2Caps%2C300&sr=8-5&th=1',
    #         'https://www.amazon.com/Westinghouse-24-720p-2022-Model/dp/B09RD8R983/ref=sr_1_21?crid=VQPSP8KDZRNS&keywords=tv&qid=1681472440&sprefix=%2Caps%2C139&sr=8-21&th=1']

    #Wrapper too generic
    # urls = ['https://www.linkedin.com/in/alexis-georgiou-3739bb1a0/',
    #         'https://www.linkedin.com/in/rolandbaz/']


    #Can't find a wrapper for wikipedia football clubs
    # urls = ['https://en.wikipedia.org/wiki/Chelsea_F.C.',
    #         'https://en.wikipedia.org/wiki/Arsenal_F.C.']

    #Can't find a wrapper for wikipedia nations
    # urls = ['https://en.wikipedia.org/wiki/Greece',
    #         'https://en.wikipedia.org/wiki/Lebanon']
    

    #Can't find a wrapper for yelp reviews
    # urls = ['https://www.yelp.fr/biz/le-ruisseau-burger-joint-paris',
    #         'https://www.yelp.fr/biz/blend-paris-26']
    

    """ READ INPUT FILES """
    #Use these two lines for using url
    # wrapper_page = url_to_html_string(urls[0])
    # sample_pages = [url_to_html_string(url) for url in urls[1:]]

    #Use these lines to use HTML files in "./test_pages/" path
    test_files = ['wrapper_page', 'sample_page1', 'sample_page2'] #Good UFRE for toy examples
    # test_files = ['Greece', 'Lebanon'] #Can't find a wrapper
    wrapper_page = read_file(test_files[0])
    sample_pages = [read_file(sample_page) for sample_page in test_files[1:]]


    """ INITIALIZE PARSERS """
    r_parser = RunnerHTMLParser()

    """ TOKENIZE HTML PAGES """
    r_parser.feed(wrapper_page)
    wrapper_tokens = r_parser.page_tokens
    # print(wrapper_tokens)
    # for t in wrapper_tokens:
    #     print(t)
    r_parser.clear_page_tokens()

    # r_parser.feed(sample_page)
    # sample_tokens = r_parser.page_tokens
    # for t in sample_tokens:
    #     print(t)

    """ RUN ROADRUNNER FOR EVERY SAMPLE PAGE"""
    for sample_page in sample_pages:
        r_parser.feed(sample_page)
        sample_tokens = r_parser.page_tokens
        wrapper = roadrunner(wrapper_tokens, sample_tokens, 0, 0, [])
        
        wrapper_tokens = r_parser.page_tokens
        # print(wrapper_tokens)
        # for t in wrapper_tokens:
        #     print(t)
        r_parser.clear_page_tokens()  


    ufre = write_final_wrapper_as_ufre(wrapper)
    print(ufre)

if __name__ == "__main__":
    main()