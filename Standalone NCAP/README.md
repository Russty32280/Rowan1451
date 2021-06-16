# Stand Alone Python Based NCAP

## Dependencies
- Paho MQTT client

# NCAP ID
There are two options for you to pick for your NCAP ID. You can provide an NCAP ID or you can allow a random ID to be generated.

# MQTT Topics
## Heartbeat
RUSMARTLAB/Heartbeat
## Application --> NCAP
RUSMARTLAB/NCAP_ID
## NCAP --> Application
RUSMARTLAB/APPL_ID

# Commands
## NCAP Discover
Payload: 1,3,1,8,1,1

## TIM Discover
Payload: 1,5,1,16,1,1

## Transducer Discover
Payload: 1,6,1,16,1,1

## Read Transducer Channel
Payload: 2,1,1,27,1,1,1,10,1

# Using EMQX Online Broker for Testing
*coming soon*
