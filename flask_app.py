from flask import Flask, render_template, request
import sqlite3
from query import process_query_games, process_query_companies, get_argparser, draw_line_chart, draw_bar_chart

app = Flask(__name__)
DB_PATH='cache/db.sqlite'

def form_to_argument(form):
    argument = ''
    platform = form['platform']
    argument += f"-p {platform} "
    start_date = form['start_date']
    if start_date == '':
        start_date = '2000-01-01'
    end_date = form['end_date']
    argument += f"-d {start_date} {end_date} "
    argument += f"-m {form['mode']} "
    ratings = form.getlist('ratings')
    if len(ratings) > 0:
        argument += f"-r {' '.join(ratings)} "
    argument += f"-rl {form['record']} "
    argument += f"-s {form['sortby']} "
    argument += f"-o {form['order']} "
    argument += f"-l {form['limit']} "
    if form['plots'] == 'bar':
        argument += '--bar'
    elif form['plots'] == 'line':
        argument += '--linechart'
    # print(argument)
    return argument


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/games')
def games_search_page():
    return render_template("index_game.html")


@app.route('/companies')
def companies_search_page():
    return render_template("index_company.html")


@app.route('/results/games', methods=['POST'])
def result_games():
    argument = ("-t games " + form_to_argument(request.form).strip()).split(' ')
    parser = get_argparser()
    try:
        args = parser.parse_args(argument)
    except:
        return render_template("invalid.html")
    if parser.error_message:
        return render_template("invalid.html")
    results, error_message = process_query_games(args, DB_PATH)
    if error_message:
        return render_template("invalid.html")
    add_plot = False
    plot = None
    if args.bar:
        plot, _ = draw_bar_chart(results, args, True)
        add_plot = True
    return render_template('table_games.html', results=results, add_plot=add_plot, plot_div=plot)


@app.route('/results/companies', methods=['POST'])
def result_companies():
    argument = ("-t companies " + form_to_argument(request.form).strip()).split(' ')
    parser = get_argparser()
    try:
        args = parser.parse_args(argument)
    except:
        return render_template("invalid.html")
    if parser.error_message:
        return render_template("invalid.html")
    results, error_message = process_query_companies(args, DB_PATH)
    if error_message:
        return render_template("invalid.html")
    add_plot = False
    plot = None
    if args.bar:
        plot, _ = draw_bar_chart(results, args, True)
        add_plot = True
    return render_template('table_companies.html', results=results, add_plot=add_plot, plot_div=plot)


if __name__ == '__main__':
    app.run(debug=True)
