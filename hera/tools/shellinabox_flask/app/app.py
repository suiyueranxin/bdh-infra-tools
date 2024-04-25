import json
import subprocess
import eventlet
from eventlet import wsgi
from flask import Flask, request, render_template
from flask import Response
from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

eventlet.monkey_patch()

@app.route('/')
def hello():
    return "Hello World!"

@app.route('/form')
def my_form():
    return render_template('form.html')

@app.route('/debug', methods=['POST'])
def start_infrabox_debug():
    raw_json_test = request.form['raw_json']
    json_obj = json.loads(raw_json_test)
    image = json_obj['image']
    command = json_obj['command']
    # generate shellinabox command
    cmd = ('''/shellinabox/shellinaboxd -t --cgi=7000-7100 -s /:root:root:HOME:"docker run -it %s %s"'''
           % (command, image))
    proc = subprocess.Popen([ cmd ], stdout=subprocess.PIPE, shell=True)
    response = proc.stdout.read()
    index = response.find('\r\n\r\n')
    print str(index)
    headers_str = response[:index+2]
    response_str = response[index+4:]
    resp = Response(response_str)
    headers_arr = headers_str.split('\r\n')
    for header_str in headers_arr:
        index = header_str.find(': ')
        if index > 0:
            header_name = header_str[0:index]
            header_value = header_str[index+2:]
            resp.headers[header_name] = header_value
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = "Access-Control-Allow-Headers, Origin,Accept," \
                                                       " Authorization, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers"
    if request.method == 'PATCH' or request.method == 'OPTIONS' or request.method == 'DELETE':
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, PATCH, DELETE'
    return response


if __name__ == '__main__':
    wsgi.server(eventlet.listen(('0.0.0.0', 80)), app)

