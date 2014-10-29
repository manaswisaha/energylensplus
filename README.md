EnergyLens+: A complete personal energy consumption monitoring system
==============
_Defining a novel way to personalize your energy consumption in your smart home_

EnergyLens+ is the advanced version of [EnergyLens](http://dl.acm.org/citation.cfm?id=2602058). It monitors the home's energy-consuming activities, attributes them to the appropriate occupant, monitors for any energy wastage and informs the occupants in real-time whenever wastage is detected. The users can view their personal energy usage/wastage, identify the most energy consuming activity and view the actual power consumption in real-time using an eco-feedback Android app.

###About the repository:
The repository contains the server side code of the EnergyLens+ system. It is a real-time inference engine that analyzes the data received from the smart meter and the smartphones. Primarily, it does the following:
* Monitors electrical activity in the home in real-time
* Identifies and attributes activities to the corresponding occupant as they do their day-to-day activities
* Infers energy wastage i.e. detects when the room is unoccupied and an electrical fixture is being used.
* Provides real-time feedback to the user about their usage/wastage
