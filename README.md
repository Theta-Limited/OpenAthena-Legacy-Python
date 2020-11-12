# OpenAerialForwardArtilleryObservation
Learning python API's by making a simple line of sight geography calculator

# Premise
So, multi-copter rotary-wing aircraft (e.g. quadroters, drones, etc.) typically have an onboard 3D A-GPS/GLONASS/whatever for position/alt. and a sensitive barometer (atmospheric pressure sensor) for absolute altitude relative to sea level. 

They also typically have an "accelerometer" which allows it to stay (very?) level with the ground while in flight, and a camera. 

Ideally for this purpose, the camera would point at horizon level during normal operation, and could be aimed at an angle <= 90 deg downward from the horizon at a target (while giving a very specific measure of its angle of declanation). 


