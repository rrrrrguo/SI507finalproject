## Instruction for Running the code
### 1. Prepare a cache dir to save the cache files, or copy the uploaded cache an db file to folder. 
```
mkdir cache
```
Make sure ```db.sqlite``` is in the cache directory, if you want to use the collect data.
### 2. Run the program
```
python main.py
```
The program includes two modes, database management mode and query mode.  

On the start of the program, the program is in the database management mode. You can go to the query mode by type
in ```continue```, or ```status``` to check the cached games. To manage the database, you can use ```add <platform_name>```
to fetch game data for new platforms, or ```delete``` to delete the current database.  
  
In the query mode, you have two options, commandline prompt or a flask app.  
For commandline prompt, use ```help``` for more details. You can select to query for games or companies(developers) through
```-t games|companies```, there are a lot of options to filter the result. Sample commands include:  
```-t games -r E T M -d 2015-01-01 2019-12-31 -p ps4 -s meta -o top ```  
Search for games with age group E/T/M, launch between 2015 and 2019 on PlayStation 4, sort by meta score by descending order  
```-t companies -p switch -s count -m online```  
Sort companies by number of online games on Switch  
You can also add ```--bar``` to see a bar plot of the query results and use ```-linechart``` to see a line chart of 
selected games launched in each month.  
  
To launch the flask app, use ```flask```. The program will provide a user interface to select those filtering options