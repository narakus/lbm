

##### 查看阿里负载均衡器实例ID，虚拟组可获取虚拟组ID

```shell
curl -sL 'http://127.0.0.1:20000/api/display' | python -m json.tool
```

&nbsp;


### 默认组操作：

&nbsp;
##### 查看详细信息，可获取实例名称

```shell
curl -sL 'http://127.0.0.1:20000/api/detail?id=实例ID' | python -m json.tool
```
&nbsp;


##### 设置离线

```shell
curl -sL 'http://127.0.0.1:20000/api/set_slb_offline_or_online?id=实例ID&name=实例名称&setup_type=offline' | python -m json.tool
```

&nbsp;

##### 设置在线

```shell
curl -sL 'http://127.0.0.1:20000/api/set_slb_offline_or_online?id=实例ID&name=实例名称&setup_type=online' | python -m json.tool
```
&nbsp;

*** 
&nbsp;

### 虚拟组操作：
&nbsp;


##### 查看虚拟组下详细信息，可获取实例名称，服务端口号

```shell
curl -sL 'http://127.0.0.1:20000/api/detail_vgroup?vgid=虚拟组ID' | python -m json.tool
```

&nbsp;

##### 设置离线

```shell
curl -sL 'http://127.0.0.1:20000/api/set_vgroup_offline_or_online?vgid=虚拟组ID&name=实例名称&setup_type=offline&port=服务端口号' | python -m json.tool
```

&nbsp;

##### 设置在线

```shell
curl -sL 'http://127.0.0.1:20000/api/set_vgroup_offline_or_online?vgid=虚拟组ID&name=实例名称&setup_type=online&port=服务端口号' | python -m json.tool
```

&nbsp;

***
&nbsp;

##### 配置文件在$HOME/.lbm/lbm.conf

```conf
[whitelist]
ips=192.168.1.1,127.0.0.1

[ali_key]
AccessKeyId=
AccessKeySecret=
RegionId=

[slb_instanceid]
id=负载均衡器实例ID，多个以逗号隔开

```

&nbsp;
