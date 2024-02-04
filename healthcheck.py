from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import tomllib
import os
import subprocess
import platform
import socket

def format_as_parameters(dictionary):
    param_string = ''
    for key,value in dictionary.items():
        param_string += (key + '=' + value + '&')
    return param_string[:-1]
    
def do_logincheck(healthcheck):
    headers={
        'Content-Type': 'application/x-www-form-urlencoded'
        }
    s = requests.Session()
    r = s.get(healthcheck['url'])
    logincheck_payload = {healthcheck['payload']['username']: healthcheck['username'],
                          healthcheck['payload']['password']: healthcheck['password']}
    soup = BeautifulSoup(r.content, 'html.parser')
    form_tag = soup.find_all('input', {'name': healthcheck['payload']['csrf_element']}, type='hidden')[0] # assume we find only one
    logincheck_payload[form_tag.attrs['name']] = form_tag.attrs['value']
    r = s.post(healthcheck['url'], data=format_as_parameters(logincheck_payload), headers=headers, allow_redirects=False)
    if r.status_code == healthcheck['success']:
        return 'success'
    else:
        return 'failed'
    
def do_pingcheck(healthcheck):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', healthcheck['ip_addr']]
    result = subprocess.call(command)
    if result == 0:
        return 'success'
    else:
        return 'failed'

def do_tcppingcheck(healthcheck):
    timeout = healthcheck.get('timeout', 3) # get from config or set a default timeout value
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((healthcheck['ip_addr'], healthcheck['port']))
    except OSError as error:
        return 'failed'
    else:
        s.close()
        return 'success'
 
# initialise array of healthchecks
healthchecks = []
id = 0
directory = "./conf.d"
for filename in os.listdir(directory):
    with open(os.path.join(directory, filename), "rb") as f:
        data = tomllib.load(f)
        data['id'] = id
        id += 1
        healthchecks.append(data)

app = Flask(__name__)

@app.route('/healthcheck/api/v1.0/checks', methods=['GET'])
def get_checks():
    response = []
    for healthcheck in healthchecks:
        response.append(
            {'id': healthcheck['id'],
             'name': healthcheck['name'],
             'type': healthcheck['type']
             }
            )
    return jsonify({'checks': response})

@app.route('/healthcheck/api/v1.0/check/<id>', methods=['GET'])
def get_check(id):
    healthcheck = next((healthcheck for  healthcheck in healthchecks if healthcheck['id'] == int(id)), None)
    if not healthcheck:
        return jsonify({'name': "Healthcheck not found", 'result': "error"})
    else:
        if healthcheck['type'] == 'login_check':
            response = do_logincheck(healthcheck)
        elif healthcheck['type'] == 'ping_check':
            response = do_pingcheck(healthcheck)
        elif healthcheck['type'] == 'tcpping_check':
            response = do_tcppingcheck(healthcheck)
        return jsonify({'name': healthcheck['name'], 'result': response})

if __name__ == '__main__':
    app.run(debug=False)