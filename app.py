from flask import Flask, render_template, request
import map

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():

    try:
        loc_name = request.form['nm']
    except Exception as e:
        loc_name = None
        # print(e)

    try:
        dist = int(request.form['dist'])
        metric = int(request.form['metric'])
    except Exception as e:
        dist = None
        metric = None
        # print(e)

    try:
        refresh_map = bool(request.form['refresh_map'])
    except Exception as e:
        refresh_map = False
        # print(e)

    if request.method == "POST":
        if loc_name:
            print('adding point')
            map.new_point(request.form['nm'])
        elif refresh_map is True:
            print('making new map')
            map.clear_set()
            map.new_map()
        elif dist:
            print("Clustering Points")
            if metric == 1:
                pass
            elif metric == 2:
                pass

            # todo: this is temporary
            # code or something

    # return different paths for the index template
    else:
        map.new_map()

    return render_template('index.html', value=map.map_._repr_html_())


if __name__ == '__main__':
    app.run(debug=True)