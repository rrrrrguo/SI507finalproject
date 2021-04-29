from cache_data import cache_result_by_platform
import os
from database_utils import query_db
from query import get_argparser, process_query, draw_bar_chart, print_results, draw_line_chart
import argparse
from flask_app import app

CACHE_DIR = "./cache/"
VALID_PLATFORM = {'ps4', 'ps5', 'switch', 'xboxone', 'xbox-series-x'}
ABBR2PLATFORM = {
    'ps4': "PlayStation 4",
    'ps5': "PlayStation 5",
    'switch': 'Switch',
    'xboxone': 'Xbox One',
    'xbox-series-x': 'Xbox Series X'
}


def check_database(path):
    ''' Check the database
    Parameters
    ----------
    path: str
        path of the database

    Returns
    -------
    cached_platforms: list
        cached platform in this database
    game_count: list
        game count in each cached platform
    '''
    if not os.path.isfile(path):
        print("Database not found")
        return [], []
    response = query_db("SELECT COUNT(*),Platform From Games GROUP BY Platform", path)
    cached_platforms = [x[1] for x in response]
    game_count = [int(x[0]) for x in response]
    return cached_platforms, game_count


def load_help_text(path):
    '''Load help text

    Parameters
    ----------
    path: str
        path to help text

    Returns
    -------
    str
        help text
    '''
    with open(path) as f:
        return f.read()


if __name__ == '__main__':
    print("Hello!")
    print("Checking database")
    cached_platforms, game_platform_count = check_database(CACHE_DIR + 'db.sqlite')
    if len(cached_platforms) > 0:
        print("Cached game platforms:", cached_platforms)
        print("Cached games:", game_platform_count)
    game_count = sum(game_platform_count)
    state = 0
    help_text_step1 = load_help_text("help_step1.txt")
    data_base_path = CACHE_DIR + 'db.sqlite'
    parser = get_argparser()
    while True:
        if state == 0:
            # caching data/delete/add more
            response = input(
                "Type 'continue' to next step,'status' for current database status,'help' for help, or 'exit':")
            response = response.strip()
            if response == 'exit':
                break
            elif response == 'continue':
                state = 1
            elif response == 'help':
                print(help_text_step1)
            elif response == 'delete':
                # add new platforms
                confirm = input("Will delete the database, press y to confirm:")
                if confirm != 'y':
                    continue
                if os.path.isfile(CACHE_DIR + 'db.sqlite'):
                    os.remove(CACHE_DIR + 'db.sqlite')
                game_count = -1
                print("Deleted the database")
            elif response == 'status':
                cached_platforms, game_platform_count = check_database(CACHE_DIR + 'db.sqlite')
                if len(cached_platforms) > 0:
                    print("Cached game platforms:", cached_platforms)
                    print("Cached games:", game_platform_count)
                game_count = sum(game_platform_count)
            elif len(response.split(' ')) == 2 and response.split(' ')[0] == 'add' and response.split(' ')[
                1] in VALID_PLATFORM:
                # add new platforms
                platform = response.split(' ')[1]
                print("Fetching data for", platform)
                cache_result_by_platform(platform, CACHE_DIR + f'cache_{platform}.json', CACHE_DIR + 'db.sqlite')
                cached_platforms, game_platform_count = check_database(CACHE_DIR + 'db.sqlite')
                if len(cached_platforms) > 0:
                    print("Cached game platforms:", cached_platforms)
                    print("Cached games:", game_platform_count)
                game_count = sum(game_platform_count)
            else:
                print("Invalid input, please retry.")
                print("Supported platforms:", VALID_PLATFORM)
        else:
            if game_count <= 0:
                print("No data in database, go to step 1")
                state = 0
                continue
            response = input("Type 'back' to last step,'help' for help,'flask' to launch a flask app, or 'exit':")
            response = response.strip()
            if response == 'exit':
                break
            elif response == 'back':
                state = 0
                continue
            elif response == 'help':
                try:
                    parser.parse_args(['--help'])
                except SystemExit:
                    continue
            elif response == 'flask':
                app.run(debug=False)
            else:
                try:
                    args = parser.parse_args(response.split(' '))
                except:
                    print("invalid input detected please retry")
                    continue
                if parser.error_message:
                    print(parser.error_message)
                    parser.error_message = ''
                    continue
                if args.linechart:
                    draw_line_chart(args, data_base_path)
                else:
                    result, error = process_query(args, data_base_path)
                    if error:
                        print(error)
                        continue
                    if args.bar:
                        draw_bar_chart(result, args)
                    else:
                        if len(result) > 0:
                            print_results(result, args)
                        else:
                            print("No records found")
    print("Bye!")