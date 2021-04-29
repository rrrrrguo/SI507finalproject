import sqlite3


def create_tables(filename):
    '''Create table in the database

    Parameters
    ----------
    filename: str
        File name of the database

    Returns
    -------
    None
    '''
    connection = sqlite3.connect(filename)
    cur = connection.cursor()
    create_games_table = '''
    CREATE TABLE IF NOT EXISTS "Games" (
        "Id"	INTEGER NOT NULL UNIQUE,
        "GameName"	TEXT NOT NULL,
        "LaunchDate"	TEXT,
        "Platform"	TEXT,
        "MetaScore"	REAL,
        "UserScore"	REAL,
        "Developer"	TEXT,
        "NumOfPlayers"	INTEGER,
        "Ratings"	TEXT,
        "CriticTotal"	INTEGER,
        "CriticPositive"	REAL,
        "UserTotal"	INTEGER,
        "UserPositive"	REAL,
        "Genres" TEXT,
        PRIMARY KEY("Id" AUTOINCREMENT)
    );
    '''
    create_genre_table = '''
    CREATE TABLE IF NOT EXISTS "Genres" (
        "GameId"	INTEGER NOT NULL,
        "Genre"	    TEXT NOT NULL,
        FOREIGN KEY("GameId") REFERENCES "Games"("Id")
    );
    '''

    create_company_table = '''
    CREATE TABLE IF NOT EXISTS "Companies" (
        "CompanyId"	INTEGER NOT NULL UNIQUE,
        "CompanyName" TEXT NOT NULL UNIQUE,
        "URL"	    TEXT,
        "TotalGames" INTEGER,
        PRIMARY KEY("CompanyId" AUTOINCREMENT)
    );
    '''

    create_game2company_table = '''
    CREATE TABLE IF NOT EXISTS "Game2Company" (
        "GameId" INTEGER NOT NULL,
        "CompanyId" INTEGER NOT NULL,
        FOREIGN KEY("GameId") REFERENCES "Games"("Id"),
        FOREIGN KEY("CompanyId") REFERENCES "Companies"("CompanyId")
    );
    '''
    cur.execute(create_games_table)
    cur.execute(create_genre_table)
    cur.execute(create_company_table)
    cur.execute(create_game2company_table)
    connection.commit()
    connection.close()


def write_to_data_base(company_infos, game_infos,company2id,filename):
    '''Write records to the database

    Parameters
    ----------
    company_infos: list
        list of company info
    game_infos: list
        list of game info
    company2id: dict
        new company to save and their ids
    filename: str
        path to the database

    Returns
    -------
    None
    '''
    connection = sqlite3.connect(filename)
    cur = connection.cursor()
    #write company record
    for row in company_infos:
        insert_command = '''
            INSERT INTO Companies
            VALUES (NULL, ?, ?, ?)
        '''
        cur.execute(insert_command, row)

    #write game record
    for row in game_infos:
        genres = row[-1]
        developers=row[5]
        row[-1]=', '.join(genres)
        row[5]=', '.join(developers)
        insert_command = '''
            INSERT INTO Games
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cur.execute(insert_command, row)
        last_id = cur.lastrowid
        for g in genres:
            insert_command = f'''
                INSERT INTO Genres
                VALUES ({last_id}, "{g}")
            '''
            cur.execute(insert_command)

        for dev in developers:
            dev_id=company2id[dev]
            insert_command= f'''
                INSERT INTO Game2Company
                VALUES ({last_id}, {dev_id})
            '''
            cur.execute(insert_command)
    connection.commit()
    connection.close()

def query_db(query,file_name):
    '''Query the database

    Parameters
    ----------
    query: str
        the query SQL
    file_name: str
        database filename
    Returns
    -------
    result: list[tuple]
        the returned query result
    '''
    connection = sqlite3.connect(file_name)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()
    return result