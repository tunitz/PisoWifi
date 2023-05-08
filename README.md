
# Piso-Wifi

A library that for piso-wifi business that uses an Orange Pi One


## Setup `omada_config.cfg`

Configure the omada config with the correct values
```bash
    [omada]
    baseurl = https://aps1-api-omada-controller.tplinkcloud.com/
    omadacId = 11111111111
    site = Test Site
    verify = False
    warnings = False
    username = your_omada@username.com
    password = yourpassword
    operator_username = operatorusername
    operator_password = operatorpassword
```

`baseurl` = Required. Use `https://aps1-api-omada-controller.tplinkcloud.com/` if using Omada Cloud Controller. Otherwise, use the IP and Port of your omada controller

`omadacId` = Required only if using Omada cloud controller. You can find it on the contoller URL. Remove this if using local controller

`site` = Site name. Case sensitive

`verify` = Keep this as False

`warnings` = Keep this as False

`username` = Admin username. This is only required if using client_service.py

`password` = Admin password. This is only required if using client_service.py

`operator_username` = Required. Needs to create a hotspot operator first.

`operator_password` = Required. Needs to create a hotspot operator first.



## Installation

Run the following script to install all the requirements

```bash
  chmod +x install.sh
  ./install.sh
```
    