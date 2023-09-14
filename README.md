
# Piso-Wifi

A python library for piso-wifi business that uses an Orange Pi One

![Logo](https://i.imgur.com/QZnfSx0.png)

## Requirements

#### Software
Omada Controller version **5.12.50** or latest

#### Hardware
`Orange Pi Zero2` `LCD 20x4`

## omada-api
Piso-Wifi app will be using the omada-api, a public http server that will automatically create **`vouchers`** in Omada

#### Create new voucher

```http
  POST https://omada-api.fly.dev/voucher
```
**Required** parameters
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `name` | `string` | unique string |
| `expirationTime` | `int` | Voucher expiration date in milliseconds |
| `duration` | `int` | Voucher usage time limit in minutes. |
| `unitPrice` | `int` | Price of the voucher |
| `username` | `string` | Hotspot operator username |
| `password` | `string` | Hotspot operator password |
| `cid` | `string` | Omada controller id |
| `siteId` | `string` | Site id |

**Optional** parameters
| Parameter | Type     | Description                | Default Value                |
| :-------- | :------- | :------------------------- | :------------------------- |
| `codeLength` | `int` | Voucher code length | 6 |
| `amount` | `int` | Number of vouchers that will be created | 1 |
| `type` | `int` | Voucher type. 0-Limited Usage Counts； 1-Limited Online Users； | 1 |
| `trafficLimitEnable` | `bool` | Enable traffic limit. | false |
| `trafficLimit` | `int` | Traffic limit in kilobytes | null |
| `durationType` | `int` | Type of voucher duration. 0 - fixed time upon use, 1 - by usage | 6 |
| `description` | `string` | Voucher description | null |
| `maxUsers` | `int` | How many online users can connect simultaneously | 1 |
| `currency` | `string` | Currency type | PHP |



## Piso-Wifi Installation

Run the following script to install Piso-Wifi app and all the requirements

```bash
  curl -fsSL https://omada-api.fly.dev/install | bash
```

#### Setup `voucher_config.json`
```bash
{
  "username": <Hotspot operator name>,
  "password": <Hotspot operator password>,
  "cid": <Omada controller Id>,
  "siteId": <Site id>,
  "rateLimitId": <Rate Limit Profile id>,
  "storeName": <Store name, will be displayed in the LCD>,
  "multiplier": <How many minutes per credit>
}
```

After setting up the `voucher_config.json`, restart the device.

Piso-Wifi app will run automatically at start
    