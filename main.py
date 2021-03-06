#main.py
from flask import Flask, request, render_template, jsonify, redirect, url_for
from random import sample
app = Flask(__name__)

import subprocess
import time
import pickle

#declare global subprocess variable
p1 = None
p2 = None


"""
Generate subprocess
Create twitter stream to file
Process sentiments to file
"""
def SubProcessTweets(query_id, query):
    args1 = ['SentweetmentProject/Streaming_to_CSV.py', str(query_id), query]
    p1 = subprocess.Popen(args1)
    time.sleep(5)
    args2 = ['SentweetmentProject/Batch_Processing.py', str(query_id)]
    p2 = subprocess.Popen(args2)
    return (p1, p2)


def TerminateSubProcess(p1, p2):
    p1.terminate()
    p2.terminate()
    
#list of queries
queries = []


"""
Render index.html
"""
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


"""
query id to access URL for graph data
"""
@app.route('/search/<int:query_id>')
def searchId(query_id):
    if (query_id < len(queries)):
        query=queries[query_id]
        return render_template('index.html', query=query, query_id=query_id)
    else:
        return redirect(url_for('index'))

    
"""
Handle POST request from user submitting query
intialise tweet streaming and processing
query given unique id
"""
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        if (query in queries):
            query_id = queries.index(query)
        else:
            global p1, p2 #set p1 and p2 to be global variable
            query_id = len(queries)
            queries.append(str(query))
            #terminate existing subprocess
            if p1 != None:
                p1.terminate()
            if p2 != None:
                p2.terminate()    
            #Initialise subprocess, 1sec delay
            (p1, p2) = SubProcessTweets(query_id, query)
        print('id: {}\nquery: {}'.format(query_id, query))
        return render_template('index.html', query=query, query_id=query_id)
    else:
        return redirect(url_for('index'))

    
"""
Collect data for graph
Requires query_id and timeline:frequency of graph updates
"""
@app.route('/search/<int:query_id>/data/<timeline>')
def data(query_id=0, timeline='sec'):
    try:
        if timeline == 'sec':
            print('Opening file')
            graph_data = open('{}_sec.txt'.format(query_id), 'r').read()
        elif timeline == 'min':
            graph_data = open('{}_min.txt'.format(query_id), 'r').read()
        elif timeline == 'hr':
            graph_data = open('{}_hr.txt'.format(query_id), 'r').read()
        elif timeline == 'day':
            graph_data = open('{}_day.txt'.format(query_id), 'r').read()
        else:
            print('Error: Invalid timeline')
    except(IOError):
        print('Error: No graph data found')
        return jsonify({'xs' : [], 'yi' : []})
    xs = []
    y1s = [] #positive average sentiment
    y2s = [] #negative average sentiment
    y3s = [] #average sentiment
    tb1 = [] #polarity
    tb2 = [] #prevalence
    tb3 = [] #influence
    tweet_data = [] #most subjective tweets
    try:
        f = open('{}_sec_tweets.pickle'.format(query_id), 'rb')
        tweet_data = pickle.load(f)
        print(tweet_data)
        f.close()
    except:
        pass
    
    lines = graph_data.split('\n')            
    for line in lines:
        if len(line) > 1:
            y1, y2, y3, polarity, prevalence, influence = line.split(',')[:6]
            tb1.append(int(polarity))
            tb2.append(int(prevalence))
            tb3.append(int(influence))
            if int(y2) != 0:
                y1s.append(int(y1))
            else:
                y1s.append(None)                
            if int(y2) != 0:
                y2s.append(int(y2))
            else:
                y2s.append(None)
            if int(y3) != 0:
                y3s.append(int(y3))
            else:
                y3s.append(None)
                
    return jsonify({'xs' : range(1,11),
                    'y1i' : y1s[-10:],
                    'y2i' : y2s[-10:],
                    'y3i' : y3s[-10:],                    
                    'tb1' : tb1[-10:],
                    'tb2' : tb2[-10:],
                    'tb3' : tb3[-10:],
                    'tweets' : tweet_data[-5:],
                })

"""
start server
"""
if __name__ == '__main__':
    #start the server
    app.run(debug=True)
