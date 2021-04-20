from cache_data import cache_result_by_platform
import os
from database_utils import query_db

CACHE_DIR="./cache/"
VALID_PLATFORM={'ps4','ps5','switch','xboxone','xbox-series-x'}



def check_database(path):
    if not os.path.isfile(path):
        print("Database not found")
        return -1
    response=query_db("SELECT COUNT(*),Platform From Games GROUP BY Platform",path)
    cached_platforms= [x[1] for x in response]
    game_count=[int(x[0]) for x in response]
    if len(cached_platforms)>0:
        print("Cached game platforms:",cached_platforms)
        print("Cached games:",game_count)
    return sum(game_count)

def load_help_text(path):
    '''Load help text
    Returns
    -------
    str, help text
    '''
    with open(path) as f:
        return f.read()


if __name__=='__main__':
    print("Hello!")
    print("Checking database")
    game_count=check_database(CACHE_DIR+'db.sqlite')
    state=0
    help_text_step1=load_help_text("help_step1.txt")
    help_text_step2=load_help_text("help_step2.txt")
    while True:
        if state==0:
            #caching data/delete/add more
            response=input("Type 'continue' to next step,'help' for help, or 'exit':")
            if response=='exit':
                break
            elif response=='continue':
                state=1
            elif response=='help':
                print(help_text_step1)
                continue
            elif response=='delete':
                #add new platforms
                confirm=input("Will delete the database, press y to confirm:")
                if confirm!='y':
                    continue
                if os.path.isfile(CACHE_DIR + 'db.sqlite'):
                    os.remove(CACHE_DIR + 'db.sqlite')
                game_count=-1
                print("Deleted the database")

            elif len(response.split(' '))==2 and response.split(' ')[0]=='add' and response.split(' ')[1] in VALID_PLATFORM:
                #add new platforms
                platform= response.split(' ')[1]
                print("Fetching data for",platform)
                cache_result_by_platform(platform,CACHE_DIR+f'cache_{platform}.json',CACHE_DIR + 'db.sqlite')
                game_count=check_database(CACHE_DIR + 'db.sqlite')
            else:
                print("Invalid input, please retry.")
                print("Supported platforms:",VALID_PLATFORM)
        else:
            #TODO: QUERY AND VISUALIZATION
            if game_count<=0:
                print("No data in database, go to step 1")
                state=0
                continue
            break


