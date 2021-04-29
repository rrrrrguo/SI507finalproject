import sqlite3
import argparse
import plotly.graph_objects as go
from prettytable import PrettyTable

ABBR2PLATFORM={
    'ps4': "PlayStation 4",
    'ps5': "PlayStation 5",
    'switch': 'Switch',
    'xboxone': 'Xbox One',
    'xbox-series-x': 'Xbox Series X'
}

TARGET2FIELD={
    'games':['GameName','Platform','MetaScore','UserScore','Developer','NumOfOnlinePlayers','Ratings','Genres','LaunchDate'],
    'companies':['CompanyName','GameCount','AverageMetaScore','AverageUserScore'],
}

class MyArgumentParser(argparse.ArgumentParser):
    '''
        A wraper for argparser, will not exit the program if error detected in arugment
        from https://stackoverflow.com/questions/5943249/python-argparse-and-controlling-overriding-the-exit-status-code
    '''
    def __init__(self, *args, **kwargs):
        super(MyArgumentParser, self).__init__(*args, **kwargs)

        self.error_message = ''

    def error(self, message):
        self.error_message = message

    def parse_args(self, *args, **kwargs):
        # catch SystemExit exception to prevent closing the application
        result = None
        try:
            result = super().parse_args(*args, **kwargs)
        except SystemExit:
            pass
        return result


def get_argparser():
    '''Construct a Argument Parser

    Returns
    -------
    parser:
        argument parser
    '''
    parser = MyArgumentParser()
    parser.add_argument('--target','-t',type=str,
                        help='The target to list, games or companies')
    parser.add_argument('--platform','-p',default='none',type=str,
                        help='Platform of games, options=ps4|ps5|switch|xboxone|xbox-series-x')
    parser.add_argument('--launchdate','-d',default=None,nargs='+',type=str,
                        help='Filter with launch date range, if two dates are provided, will search in the range, format: yyyy-mm-dd')
    parser.add_argument('--mode','-m',default='none',type=str,
                        help='Mode of the game, options=none|online|offline')
    parser.add_argument('--ratings','-r',default=None,nargs='+',type=str,
                        help='Age Group of the game can input multiple options, options=E|E10+|T|M')
    parser.add_argument('--record','-rl',default=0,type=int,
                        help='Filter results with less than <recordlimit> number of reviews(games) or game counts(companies)')
    parser.add_argument('--sortby','-s',default='meta',type=str,
                        help='Whether to sort/aggregate, count are intended for companies, options=meta|user|count')
    parser.add_argument('--order','-o',default='top',type=str,
                        help='List results in descending(top) or ascending(bottom) order, options=top|bottom')
    parser.add_argument('--limit','-l',default=10,type=int,
                        help='Number of results to show')
    parser.add_argument('--bar',action='store_true',
                        help='whether to show a bar chart of the result')
    parser.add_argument('--linechart',action='store_true',
                        help='whether to draw a line chart of game count in each month, will override sort options')
    return parser

def query_db(query,db_path):
    '''Query the database

    Parameters
    ----------
    query: str
        the query SQL
    db_path: str
        the path to database
    Returns
    -------
    result: list[tuple]
        the returned query result
    '''
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    return result


def process_query_games(args,db_path):
    '''Process the query for games

    Parameters
    ----------
    args:
        parsed argument
    db_path:
        path to the database

    Returns
    -------
    result:
        A list of query result
    error_message:
        error message, if is empty, the query is successful
    '''
    if args.platform=='none':
        platform_filter=''
    elif args.platform in ABBR2PLATFORM:
        platform_filter=f'Platform="{ABBR2PLATFORM[args.platform]}"'
    else:
        return [],f"invalid arguments for: -p {args.platform}"

    if args.launchdate is None:
        date_filter=''
    elif isinstance(args.launchdate,list) and (len(args.launchdate)==1 or len(args.launchdate)==2):
        if len(args.launchdate)==1:
            date_filter=f'LaunchDate >= "{args.launchdate[0]}"'
        else:
            date_filter=f'LaunchDate BETWEEN "{args.launchdate[0]}" AND "{args.launchdate[1]}"'
    else:
        return [],f"invalid arguments for: -d {args.launchdate}"

    if args.mode=='none':
        mode_filter=''
    elif args.mode=='online':
        mode_filter='NumOfPlayers > 0'
    elif args.mode=='offline':
        mode_filter='NumOfPlayers = 0'
    else:
        return [],f"invalid arguments for: -m {args.mode}"


    if args.ratings is None:
        rating_filter=''
    else:
        rating_filters = []
        for rating in args.ratings:
            if rating in ['E','E10+','T','M']:
                rating_filters.append(f'Ratings = "{rating}"')
            else:
                return [],f"invalid arguments for: -r {args.ratings}"
        rating_filter='('+' OR '.join(rating_filters)+')'

    if args.sortby in ['none','meta']:
        sortby_arg='ORDER BY MetaScore'
    elif args.sortby=='user':
        sortby_arg='ORDER BY UserScore'
    else:
        return [],f"invalid arguments for: -s {args.sortby}"

    if args.record>=0:
        if args.sortby=='user':
            review_filter = f"UserTotal >={args.record}"
        else:
            review_filter=f"CriticTotal >={args.record}"
    else:
        return [],f"invalid arguments for: -rl {args.record}"


    if args.order=='top':
        order='DESC'
    elif args.order=='bottom':
        order='ASC'
    else:
        return [],f"invalid arguments for: -o {args.order}"

    if args.limit>0:
        limit= f"LIMIT {args.limit}"
    else:
        return [],f"invalid arguments for: -l {args.limit}"

    filters=[platform_filter,date_filter,mode_filter,rating_filter,review_filter]
    filters=[x for x in filters if x]
    if len(filters)==0:
        filters_arg=''
    else:
        filters_arg='WHERE '+' AND '.join(filters)

    query=f'''
    SELECT GameName,Platform,MetaScore,UserScore,Developer,NumOfPlayers,Ratings,Genres,LaunchDate 
    FROM Games
    {filters_arg}
    {sortby_arg} {order}
    {limit}
    '''
    return query_db(query,db_path),""


def process_query_companies(args,db_path):
    '''Process the query for companies

    Parameters
    ----------
    args:
        parsed argument
    db_path:
        path to the database

    Returns
    -------
    result:
        A list of query result
    error_message:
        error message, if is empty, the query is successful
    '''
    if args.platform=='none':
        platform_filter=''
    elif args.platform in ABBR2PLATFORM:
        platform_filter=f'Games.Platform="{ABBR2PLATFORM[args.platform]}"'
    else:
        return [],f"invalid arguments for: -p {args.platform}"

    if args.launchdate is None:
        date_filter=''
    elif isinstance(args.launchdate,list) and (len(args.launchdate)==1 or len(args.launchdate)==2):
        if len(args.launchdate)==1:
            date_filter=f'Games.LaunchDate >= "{args.launchdate[0]}"'
        else:
            date_filter=f'Games.LaunchDate BETWEEN "{args.launchdate[0]}" AND "{args.launchdate[1]}"'
    else:
        return [],f"invalid arguments for: -d {args.launchdate}"

    if args.mode=='none':
        mode_filter=''
    elif args.mode=='online':
        mode_filter='Games.NumOfPlayers > 0'
    elif args.mode=='offline':
        mode_filter='Games.NumOfPlayers = 0'
    else:
        return [],f"invalid arguments for: -m {args.mode}"

    if args.ratings is None:
        rating_filter=''
    else:
        rating_filters = []
        for rating in args.ratings:
            if rating in ['E','E10+','T','M']:
                rating_filters.append(f'Games.Ratings = "{rating}"')
            else:
                return [],f"invalid arguments for: -r {args.ratings}"
        rating_filter='('+' OR '.join(rating_filters)+')'

    if args.sortby in ['none','meta']:
        sortby_arg='ORDER BY [AVG(MetaScore)]'
    elif args.sortby=='user':
        sortby_arg='ORDER BY [AVG(UserScore)]'
    elif args.sortby=='count':
        sortby_arg='ORDER BY [COUNT(*)]'
    else:
        return [],f"invalid arguments for: -s {args.sortby}"

    if args.record>=0:
        count_filter=f"[Count(*)] >={args.record}"
    else:
        return [],f"invalid arguments for: -rl {args.record}"


    if args.order=='top':
        order='DESC'
    elif args.order=='bottom':
        order='ASC'
    else:
        return [],f"invalid arguments for: -o {args.order}"

    if args.limit>0:
        limit= f"LIMIT {args.limit}"
    else:
        return [],f"invalid arguments for: -l {args.limit}"

    filters=[platform_filter,date_filter,mode_filter,rating_filter]
    filters=[x for x in filters if x]
    if len(filters)==0:
        filters_arg=''
    else:
        filters_arg='WHERE '+' AND '.join(filters)


    query=f'''
    SELECT CompanyName,[Count(*)],Round([AVG(MetaScore)],1), Round([AVG(UserScore)],1)
    From
        (SELECT Companies.CompanyName,Count(*),AVG(MetaScore), AVG(UserScore)
        FROM Game2Company
            JOIN (SELECT * FROM Games {filters_arg}) AS Games
                ON Game2Company.GameId=Games.Id
            JOIN Companies
                ON Game2Company.CompanyId=Companies.CompanyId
        GROUP BY Game2Company.CompanyId)
    WHERE {count_filter}
    {sortby_arg} {order}
    {limit}
    '''
    return query_db(query,db_path),""

def draw_line_chart(args,data_base_path,return_html=False):
    '''Draw the line chart according to the argument

    Parameters
    ----------
    args:
        parsed argument
    data_base_path:
        path to the database
    return_html:
        if true, will return the html of the graph, if false, will display the graph
    Returns
    -------
    html:
        html of the plot, used for flask
    error_message:
        error message, if is empty, the query is successful
    '''
    if args.platform=='none':
        platform_filter=''
    elif args.platform in ABBR2PLATFORM:
        platform_filter=f'Platform="{ABBR2PLATFORM[args.platform]}"'
    else:
        return f"invalid arguments for: -p {args.platform}"

    if args.launchdate is None:
        date_filter=''
    elif isinstance(args.launchdate,list) and (len(args.launchdate)==1 or len(args.launchdate)==2):
        if len(args.launchdate)==1:
            date_filter=f'LaunchDate >= "{args.launchdate[0]}"'
        else:
            date_filter=f'LaunchDate BETWEEN "{args.launchdate[0]}" AND "{args.launchdate[1]}"'
    else:
        return f"invalid arguments for: -d {args.launchdate}"

    if args.mode=='none':
        mode_filter=''
    elif args.mode=='online':
        mode_filter='NumOfPlayers > 0'
    elif args.mode=='offline':
        mode_filter='NumOfPlayers = 0'
    else:
        return f"invalid arguments for: -m {args.mode}"

    if args.ratings is None:
        rating_filter=''
    else:
        rating_filters = []
        for rating in args.ratings:
            if rating in ['E','E10+','T','M']:
                rating_filters.append(f'Games.Ratings = "{rating}"')
            else:
                return [],f"invalid arguments for: -r {args.ratings}"
        rating_filter='('+' OR '.join(rating_filters)+')'


    if args.record>=0:
        if args.sortby=='user':
            review_filter = f"UserTotal >={args.record}"
        else:
            review_filter=f"CriticTotal >={args.record}"
    else:
        return f"invalid arguments for: -rl {args.record}"
    filters=[platform_filter,date_filter,mode_filter,rating_filter,review_filter]
    filters=[x for x in filters if x]
    if len(filters)==0:
        filters_arg=''
    else:
        filters_arg='WHERE '+' AND '.join(filters)

    query=f'''
    SELECT SUBSTR(LaunchDate,1,7),COUNT(*)
    FROM
        (SELECT *
        FROM Games
        {filters_arg})
    GROUP BY SUBSTR(LaunchDate,1,7)
    '''
    results=query_db(query, data_base_path)
    x_data=[x[0] for x in results]
    y_data=[x[1] for x in results]
    bar_data = go.Scatter(x=x_data, y=y_data)
    basic_layout = go.Layout()
    fig = go.Figure(data=bar_data, layout=basic_layout)
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="GameCount",
    )
    if return_html:
        return fig.to_html(full_html=False),""
    fig.show()
    return ""


def process_query(args,db_path):
    '''Process the query for companies

    Parameters
    ----------
    args:
        parsed argument
    db_path:
        path to the database

    Returns
    -------
    result:
        A list of query result
    error_message:
        error message, if is empty, the query is successful
    '''
    if args.target=='games':
        return process_query_games(args,db_path)
    elif args.target=='companies':
        return process_query_companies(args,db_path)
    else:
        return [],f"invalid arguments: -t {args.target}"

def print_results(results,args):
    '''Pretty print query result

    Parameters
    ----------
    results:
        A list of query result
    args:
        parsed argument

    Returns
    -------
    None
    '''
    table=PrettyTable(field_names=TARGET2FIELD[args.target])
    table.add_rows(results)
    table.float_format='.1'
    print(table)

def draw_bar_chart(query_result,args,return_html=False):
    '''Draw the bar chart for query result

    Parameters
    ----------
    query_result:
        A list of query result
    args:
        parsed argument
    return_html:
        if true, will return the html of the graph, if false, will display the graph

    Returns
    -------
    html:
        html of the plot, used for flask
    error_message:
        error message, if is empty, the query is successful
    '''
    sort_key=args.sortby
    if args.target=='games':
        if sort_key=='user':
            y_idx=3
        else:
            y_idx=2
    else:
        if sort_key=='user':
            y_idx=3
        elif sort_key=='meta':
            y_idx=2
        else:
            y_idx=1
    if args.target=='games':
        x_data=[x[0]+' ('+x[1]+')' for x in query_result]
    else:
        x_data=[x[0] for x in query_result]
    y_data=[x[y_idx] for x in query_result]
    bar_data = go.Bar(x=x_data, y=y_data)
    basic_layout = go.Layout()
    fig = go.Figure(data=bar_data, layout=basic_layout)
    if sort_key=='user':
        y_title="UserScore"
    elif sort_key=='media' or sort_key=='none':
        y_title="MetaScore"
    else:
        y_title="GameCount"
    fig.update_layout(
        xaxis_title=args.target,
        yaxis_title=y_title,)
    if return_html:
        return fig.to_html(full_html=False),""
    fig.show()
    return ""