import os
import json
import configparser
import AliRequest
from functools import wraps
from flask import Flask, request, jsonify

conf_file = os.path.join(os.getenv('HOME'), '.lbm/lbm.conf')
cf = configparser.ConfigParser()
cf.read(conf_file)

WhiteList = cf.get('whitelist', 'ips').split(',')
AccessKeyId = cf.get('ali_key', 'AccessKeyId')
AccessKeySecret = cf.get('ali_key', 'AccessKeySecret')
RegionId = cf.get('ali_key', 'RegionId')
LbId = cf.get('slb_instanceid', 'id')


def check_white_list(origin_func):
    @wraps(origin_func)
    def wrapper(*args, **kwargs):
        ipaddr = request.remote_addr
        if ipaddr not in WhiteList:
            return jsonify({'error': 'true', 'msg': 'forbidden'})
        json_data = origin_func(*args, **kwargs)
        return json_data
    return wrapper


def ali_reqest():
    return AliRequest.AliRequest(AccessKeyId, AccessKeySecret, RegionId)


app = Flask(__name__)

ali_req = ali_reqest()


@app.route('/api/display', methods=['GET'])
@check_white_list
def display():
    response = ali_req.DescribeLoadBalancers(LbId)
    return jsonify(response)

@app.route('/api/detail', methods=['GET'])
@check_white_list
def detail():
    slb_id = request.args.get('id')
    if slb_id is None or len(slb_id) != 24 or not slb_id.startswith('lb-'):
        return jsonify({'error': 'True', 'msg': 'Wrong slb id'})
    response = ali_req.DescribeLoadBalancerAttribute(slb_id)
    for item in response['BackendServers']:
        ServerId = item['ServerId']
        ServerName,ipv4 = ali_req.get_instancename_by_instanceid(str([ServerId]))
        item['ServerName'] = ServerName
        item['ipaddr'] = ipv4
    if len(response['BackendServers']) == 0:
        return jsonify(ali_req.DescribeVServerGroups(slb_id))
    return jsonify(response)

@app.route('/api/detail_vgroup', methods=['GET'])
@check_white_list
def detail_with_vgroup():
    vgroup_id = request.args.get('vgid')
    if vgroup_id is None or len(vgroup_id) != 17:
        return jsonify({'error': 'True', 'msg': 'Wrong vgroup id'})
    ali_req.DescribeVServerGroupAttribute(vgroup_id)
    response = ali_req.DescribeVServerGroupAttribute(vgroup_id)
    for item in response['BackendServers']['BackendServer']:
        ServerId = item['ServerId']
        ServerName,ipv4 = ali_req.get_instancename_by_instanceid(str([ServerId]))
        item['ServerName'] = ServerName
        item['ipaddr'] = ipv4
    return jsonify(response)

@app.route('/api/set_slb_offline_or_online', methods=['GET'])
@check_white_list
def set_slb_offline_or_online():
    slb_id = request.args.get('id')
    ecs_name = request.args.get('name')
    setup_type = request.args.get('setup_type')
    if not all([slb_id, ecs_name, setup_type]):
        return jsonify({'error': 'True', 'msg': 'Wrong args'})
    if setup_type == 'online':
        weight = 100
    elif setup_type == 'offline':
        weight = 0
    else:
        return jsonify({'error': 'True', 'msg': 'Wrong setup type'})
    instance_id, ipv4 = ali_req.get_instanceid_by_instancename(ecs_name)
    if len(slb_id) == 24 and slb_id.startswith('lb-'):
        result = ali_req.SetBackendServers(slb_id, (instance_id, weight))
        return jsonify(result)
    else:
        return jsonify({'error': 'True', 'msg': 'Wrong slb instance id'})

@app.route('/api/set_vgroup_offline_or_online', methods=['GET'])
@check_white_list
def set_vgroup_offline_or_online():
    vgroup_id = request.args.get('vgid')
    ecs_name = request.args.get('name')
    setup_type = request.args.get('setup_type')
    port = request.args.get('port')
    if not all([vgroup_id, ecs_name, setup_type, port, ]):
        return jsonify({'error': 'True', 'msg': 'Wrong args'})
    if len(vgroup_id) != 17:
        return jsonify({'error': 'True', 'msg': 'Wrong vgroup id'})
    args = (ecs_name, int(port), setup_type)
    response = ali_req.SetVgroupBackendServers(vgroup_id, args)
    return jsonify(response)


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=20000
    )
