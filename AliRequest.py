import os
import sys
import hashlib
import hmac
import base64
import urllib
import time
import uuid
import requests
import json


class AliRequest(object):

    def __init__(self, AccessKeyId, AccessKeySecret, RegionId):
        self.AccessKeyId = AccessKeyId
        self.AccessKeySecret = AccessKeySecret
        self.RegionId = RegionId
        self.Version = None

    def get_iso8601_time(self):
        TIME_ZONE = "GMT"
        FORMAT_ISO8601 = "%Y-%m-%dT%H:%M:%SZ"
        return time.strftime(FORMAT_ISO8601, time.gmtime())

    def get_uuid(self):
        return str(uuid.uuid4())

    def get_parameters(self, Action, user_param, Version):
        parameters = {}
        parameters['HTTPMethod'] = 'GET'
        parameters['AccessKeyId'] = self.AccessKeyId
        parameters['Format'] = 'json'
        parameters['Version'] = Version
        parameters['SignatureMethod'] = 'HMAC-SHA1'
        parameters['Timestamp'] = self.get_iso8601_time()
        parameters['SignatureVersion'] = '1.0'
        parameters['SignatureNonce'] = self.get_uuid()
        parameters['Action'] = Action
        for (k, v) in sorted(user_param.items()):
            parameters[k] = v
        return parameters

    def get_param(self, parameters):
        param_str = ''
        for (k, v) in sorted(parameters.items()):
            param_str += "&" + \
                urllib.parse.quote(k, safe='') + "=" + urllib.parse.quote(v, safe='')
        param_str = param_str[1:]
        return param_str

    def get_StringToSign(self, parameters, param_str):
        StringToSign = parameters['HTTPMethod'] + \
            "&%2F&" + urllib.parse.quote(param_str, safe='')
        return StringToSign

    def get_signature(self, StringToSign, AccessKeySecret):
        h = hmac.new(
            str.encode(AccessKeySecret),
            str.encode(StringToSign),
            hashlib.sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def _build_request(self, user_param, Action, request_url_type):
        if request_url_type == 'slb':
            Version = '2014-05-15'
            self.server_url = 'https://' + 'slb.' + self.RegionId + '.aliyuncs.com' + '/?'
        elif request_url_type == 'ecs':
            Version = '2014-05-26'
            self.server_url = 'https://' + 'ecs.' + self.RegionId + '.aliyuncs.com' + '/?'
        else:
            raise Exception('Error url type')
        parameters = self.get_parameters(Action, user_param, Version)
        param_str = self.get_param(parameters)
        StringToSign = self.get_StringToSign(parameters, param_str)
        signature = self.get_signature(
            StringToSign, self.AccessKeySecret + '&')
        Signature = "Signature=" + urllib.parse.quote(signature)
        param = param_str + "&" + Signature
        request_url = self.server_url + param
        response = requests.get(request_url)
        return response

    def DescribeInstances(self, InstanceName=None, InstanceId=None):
        result = {}
        Action = 'DescribeInstances'
        if InstanceName:
            user_param = {
                'RegionId': self.RegionId,
                'InstanceName': InstanceName}
        if InstanceId:
            user_param = {'RegionId': self.RegionId, 'InstanceIds': InstanceId}
        message = self._build_request(user_param, Action, 'ecs').json()
        return message

    def get_instanceid_by_instancename(self, name):
        message = self.DescribeInstances(InstanceName=name)
        instance_id = message['Instances']['Instance'][0]['InstanceId']
        ipv4 = message['Instances']['Instance'][0]['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]
        return(instance_id, ipv4)

    def get_instancename_by_instanceid(self, instanid):
        message = self.DescribeInstances(InstanceId=instanid)
        instance_name = message['Instances']['Instance'][0]['InstanceName']
        ipv4 = message['Instances']['Instance'][0]['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]
        return(instance_name, ipv4)

    def DescribeLoadBalancers(self, LoadBalancerId):
        result = {}
        Action = 'DescribeLoadBalancers'
        user_param = {
            'RegionId': self.RegionId,
            'LoadBalancerId': LoadBalancerId}
        message = self._build_request(user_param, Action, 'slb').json()
        for item in message['LoadBalancers']['LoadBalancer']:
            result[item['LoadBalancerId']] = {'LoadBalancerName': item['LoadBalancerName'],
                                              'Address': item['Address'], 'LoadBalancerStatus': item['LoadBalancerStatus'], }
        return result

    def DescribeLoadBalancerAttribute(self, LoadBalancerId):
        result = {}
        Action = 'DescribeLoadBalancerAttribute'
        user_param = {
            'RegionId': self.RegionId,
            'LoadBalancerId': LoadBalancerId}
        message = self._build_request(user_param, Action, 'slb').json()
        result['LoadBalancerName'] = message['LoadBalancerName']
        result['Address'] = message['Address']
        result['LoadBalancerStatus'] = message['LoadBalancerStatus']
        result['BackendServers'] = message['BackendServers']['BackendServer']
        return result

    def DescribeVServerGroups(self, LoadBalancerId):
        result = {}
        Action = 'DescribeVServerGroups'
        user_param = {
            'RegionId': self.RegionId,
            'LoadBalancerId': LoadBalancerId}
        message = self._build_request(user_param, Action, 'slb').json()
        result['VServerGroups'] = message['VServerGroups']
        return result

    def DescribeVServerGroupAttribute(self, VServerGroupId):
        Action = 'DescribeVServerGroupAttribute'
        user_param = {
            'RegionId': self.RegionId,
            'VServerGroupId': VServerGroupId}
        message = self._build_request(user_param, Action, 'slb').json()
        return message


    def SetBackendServers(self, LoadBalancerId, ServerId_with_Weight):
        is_seted = False
        Action = 'SetBackendServers'
        BackendServers = self.DescribeLoadBalancerAttribute(LoadBalancerId)[
            'BackendServers']
        _ = [item.pop('Type') for item in BackendServers]
        tran_serverid, tran_weight = ServerId_with_Weight

        # 判断是否存在ServerId
        for item in BackendServers:
            if item['ServerId'] == tran_serverid:
                item['Weight'] = tran_weight
                is_seted = True
                break
            else:
                continue

        if is_seted:
            user_param = {
                'RegionId': self.RegionId,
                'LoadBalancerId': LoadBalancerId,
                'BackendServers': str(BackendServers)}
            message = self._build_request(user_param, Action, 'slb').json()
            return message
        else:
            raise Exception(tran_serverid + " is not found")

    def SetVgroupBackendServers(self, Vgrupid, VbackendServer):
        Action = 'SetVServerGroupAttribute'
        ecs_name, port, setup_type = VbackendServer
        curr_vgroup_status = self.DescribeVServerGroupAttribute(Vgrupid)
        ecs_id, _ = self.get_instanceid_by_instancename(ecs_name)
        backend_server_list = curr_vgroup_status['BackendServers']['BackendServer']

        is_seted = False
        for item in backend_server_list:
            if port == item.get('Port') and ecs_id == item.get('ServerId'):
                if setup_type == 'online':
                    item['Weight'] = 100
                elif setup_type == 'offline':
                    item['Weight'] = 0
                else:
                    raise Exception('Error weight arg')
                is_seted = True
                break
            else:
                continue

        if is_seted:
            user_param = {
                'RegionId': self.RegionId,
                'VServerGroupId': Vgrupid,
                'BackendServers': str(backend_server_list)
            }
            message = self._build_request(user_param, Action, 'slb').json()
            return message
        else:
            raise Exception(ecs_name + " is not found")
