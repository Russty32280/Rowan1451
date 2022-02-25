# Stand Alone Python Based NCAP

## Dependencies
- Paho MQTT client

# NCAP ID
The NCAP ID for this Stand Alone NCAP is randomly generated at initialization. This value is printed to the terminal, but will also be broadcast to the topic "RUSMARTLAB/Heartbeat" every 10 seconds. This is meant to emulate the NCAP broadcasting that it is available to be connected to.

# MQTT Topics
Since communication needs to be established between the Application and the NCAP (both of which are MQTT Clients on the same broker), the NCAP will automatically subscribe itself to the topic "RUSMARTLAB/NCAP_ID", where the NCAP_ID is the value generated at initialization. This is the topic where you can send commands.
## Application --> NCAP
RUSMARTLAB/NCAP_ID
Once your NCAP is connected to the MQTT Broker, it will broadcast its NCAP_ID and status to the general Heartbeat topic.
## Heartbeat
RUSMARTLAB/Heartbeat

For the time being, the NCAP will reply back to a topic called "RUSMARTLAB/APPL_ID", where the APPL_ID is the string "APPL" concatenated with the randomly generated index from the initialization. For example, if your NCAP assumed the NCAP_ID of "SA_NCAP123", the APPL_ID it will associate with by default is "APPL123".

## NCAP --> Application
RUSMARTLAB/APPL_ID

For future implementations, the NCAP will parse out what APPL_ID is sending the command and then respond back to the correct Topic.

# Commands
## Heartbeat
This is automatically published every 10 seconds and does not require a command to be sent.

## NCAP Discover
Discover details about the NCAP including the NCAP Name, IP Address, and number of TIMs connected to it.

_Payload_: 1,3,1,8,1,1

## TIM Discover
Discover specific details about a TIM connected to the specified NCAP including the TIM ID and Number of Transducer Channels.

_Payload_: 1,5,1,16,1,1

## Transducer Discover
Discover the types of transducers connected to a specific TIM.

_Payload_: 1,6,1,16,1,1

## Read Transducer Channel
Request a sample reading of a single transducer connected to a particular NCAP.

_Payload_: 2,1,1,27,1,1,1,10,1

# Typical Testing Procedure
## 1. Connecting with an online MQTT Client
Using an online client such as (http://tools.emqx.io/) or your own client on your phone or other device, you will need to connect to the MQTT broker in order to get started talking to your NCAP. The broker information used by default is:
- Broker: broker.emqx.io
- Port: 8083
- Username: N/A
- Password: N/A

## 2. Subscribing to the Heartbeat to find your NCAP 
To listen to the Heartbeats of the NCAPs connected to the broker in our network, you will want to subscribe to the topic: "RUSMARTLAB/Heartbeat".

## Subscribing to your  


# Using EMQX Online Broker for Testing
*coming soon*
