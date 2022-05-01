# Open Athena
![Carole Raddato - Statue of Athena wearing a Corinthian helmet - CC Share Alike license](athena_thumb.jpg)

Open Athena is a project to enable precision indirect fires that disrupt conventional combined arms warfare. This is accomplished by combining consumer rotary-wing aircraft (drones) sensor data with geospatial topography data

[Premise](https://github.com/mkrupczak3/OpenAthena#premise)
[![concept whiteboard diagram](concept_whiteboard_diagram.jpg)](https://github.com/mkrupczak3/OpenAthena#premise)

# Limitations of Indirect Fire in existing combined arms doctrine
While the [importance of indirect fire](causative_agents_blurb.md) (e.g. mortars, artillery, rockets) is well known to military historians, present-day soldiers, and others studied in methods of warfare, it remains an imprecise, blunt, and destructive tool relegated merely to a support role in current combined arms doctrine.

Mastery of combined arms through maneuver warfare and air superiority remain the determinate factors of supremacy in current doctrine, preventing the effective application of indirect fire. This is in large part due to the lack of precision and immediacy that are critical for its usage against a highly-mobile adversary.

As former U.S. Army Chief of Staff Gen. Mark A. Milley wrote in the forward to U.S. Army Training and Doctrine Command Pamphlet 525-3-1, [The U.S. Army in Multi-Domain Operations 2028](https://adminpubs.tradoc.army.mil/pamphlets/TP525-3-1.pdf): “emerging technologies” are “driving a fundamental change in the character of war.” They have “the potential to revolutionize battlefields unlike anything since the integration of machine guns, tanks, and aviation which began the era of combined arms warfare.”

# A new introduction to combined arms doctrine

Retired French army general and theory-crafter Guy Hubin writes in [_Perspectives tactiques_](https://warontherocks.com/2021/02/kill-the-homothetic-army-gen-guy-hubins-vision-of-the-future-battlefield/) that the possibility of precision indirect fires is one such fundamental change in the character of war driven by emerging technologies.

With recent advancements in consumer technology and publicly-available terrain datasets, the possibility arises of using inexpensive, low-altitude, un-manned fixed or rotary-wing aircraft to augment the capability of indirect fire. They can achieve this by improving indirect fire's accuracy in usage and providing precise, immediate information on targets to operators of a broad range of existing indirect fire weaponry.

# Proof of concept
Aerial forward artillery observation with small consumer aircraft, even if not employed specifically in this technique, has proven to be very effective in application during the 2022 war in Ukraine.

Examples:

In first-hand accounts (via Twitter user [@Jack_Watling](https://twitter.com/Jack_Watling)):
[shashj/status/1519041368672415747](https://twitter.com/shashj/status/1519041368672415747)


forward artillery observation for counter-battery fire: [Osinttechnical/status/1511867981596434434](https://twitter.com/Osinttechnical/status/1511867981596434434)
[alt video link](counter-battery-example.mp4)

forward artillery observation for indirect-fire adjustment: [Osinttechnical/status/1516473926150463494](https://twitter.com/Osinttechnical/status/1516473926150463494) [alt video link](fire-adjustment-example.mp4)

forward artillery observation for combined arms disruption: [UAWeapons/status/1509247556164935691](https://twitter.com/UAWeapons/status/1509247556164935691)
[alt video link](anti-combined-arms-example.mp4)

forward artillery observation for logistics disruption:
[Osinttechnical/status/1511683706511052808](https://twitter.com/Osinttechnical/status/1511683706511052808)
[alt video link](anti-logistics-example.mp4)

# An upset in combined arms doctrine

This project portends the possibility of one such upset to existing combined arms doctrine. Low cost remote-controlled consumer-grade aircraft are the instrument of such a change in the character of warfare. Such aircraft are easy to operate by infantry units and inexpensive to replace. Meanwhile, when used to guide indirect fire, such aircraft may provide an effective counter to concentrated infantry and armored units of an adversary accustomed to fighting under current combined arms doctrine.

Due to the low altitude operation and inexpensive nature of such aircraft, they can counter concentrated combined arms forces even when higher-altitude air supremacy is not held or may not be achieved against an adversary. In such a fashion, low altitude consumer-grade aircraft upset the role of high-altitude military aircraft as the only effective foil to ground-based combined arms. High-altitude air supremacy becomes less important, especially in situations where the adversary is unable to field enough military aircraft to enforce an airborne presence or provide close air support.

Additionally, the combination of existing combined arms with new precision indirect fire capabilities may allow a unit to move more rapidly and gain ground at frightening speeds using classic fire-and-movement tactics. The advantage provided by precision indirect fire is that it can supress a target from beyond line of sight, reducing the burden of infantry units to supress a target while a friendly unit is in motion. Well executed maneuvers under such conditions may outpace a conventional force's ability to react, resupply, and reposition its own defenses.

# Adapting to an upset

Low altitude air supremacy must be considered equally as essential as that of high altitude in existing combined arms doctrine.

Infantry and mechanized units must guard against artillery-observing aircraft. Specialized low-altitude anti-air or electronic countermeasures (ECM) must be developed. Such platforms should be able to deter such aircraft just as easily as they can be deployed

Effort should be made into producing inexpensive 'bird of prey' aircraft that can enforce low-altitude air supremacy and deny an adversary's aerial artillery observation

# Premise

![concept whiteboard diagram](concept_whiteboard_diagram.jpg)

Multi-copter rotary-wing aircraft (e.g. quadroters, drones, etc.) typically have an onboard 3D A-GPS sensor for position/alt., a magnetometer for compass heading/azimuth,  and a sensitive barometer (atmospheric pressure sensor) for accurate absolute altitude relative to sea level.

They also typically have an "accelerometer" which allows it to stay level with the ground while in flight, and a camera.

Ideally for this purpose, the camera would point at horizon level during normal operation, and could be aimed at an angle <= 90 deg downward from the horizon at a target (while giving a very specific measure of its angle of declanation).

Given that the lat/long and altitude of the rotary-wing aircraft is known, its azimuth is known, and it is possible to obtain accurate worldwide elevation data (within ~30m) from [this api](https://pypi.org/project/elevation/), it should be a very simple math problem to calculate the position and altitude of the object aimed at by the camera.

If an invisible, imaginary mathematical line was "paramaterized" from the aircraft's camera towards the ground at its angle of declanation, the point closest along this line to the aircraft yet reasonably near any geographic lat/long/alt data point is likely to be the target which the camera is aiming at. This would provide the aircraft operator with a rough latitude, longitude, and elevation of the target to which the camera is aiming in an extremely short period of time.

While untested, such a rapid positional resolution may prove ideal for use by precision indirect fire teams

# Install

All you need to do is run `pip3 install gdal matplotlib`, then run `playground/geotiff_play.py` with python3:
```bash
pip3 install gdal matplotlib
# if this fails, instead install the GDAL package with your package manager (i.e. apt, yum, brew, pacman, etc.)
git clone https://github.com/mkrupczak3/OpenAthena.git
cd OpenAthena/playground
python3 geotiff_play.py
```

"pip3" and "python3" may just be called "pip" and "python" depending on the configuration of your system

# Current status

### geotiff_play.py

Run python geotiff_play.py (while in the playground directory) for a demonstration of [geoTIFF](https://en.wikipedia.org/wiki/GeoTIFF) [DEM](https://en.wikipedia.org/wiki/Digital_elevation_model) parsing. The file `Rome-30m-DEM.tif` is provided in the `playground` directory as an example. A DEM covering a customized area can be [easily obtained](./playground/EIO_fetch_geotiff_example.md) using the python `elevation` API


(counterintuitively, the x and y axis are backwards in the standard notation of a position via [latitude , longitude])




```
user@mypc:~/projects/OpenAthena/playground$
python geotiff_play.py
```
![render of terrain around Rome](playground/render_cli_screenshot.png)

Then, exit the picture window that appears. You will now be prompted in the command line interface for a latitude and longitude, enter lat/long coordinates and the program will give you the approximate elevation using the nearest 4 data points


### getTarget.py


getTarget.py searches along the constructed line (emmitted from the camera center) for a terrain match


This functionality is not yet tested for correctness (should not be totally relied on)


running `geotiff_play` in a seprate terminal session before and while running `getTarget.py` is favorable because it allows yourself to view the terrain data visually while experimenting with terrain resolution matches


To start, `cd` into the `playground` directory, then run getTarget.py:

```bash
you@yourcomputer playground % python3 getTarget.py
```

You should then see the following prompt:
```bash
Hello World!
I'm getTarget.py
Which GeoTiff file would you like to read?
Enter the GeoTIFF filename:
```

You can clip [your own geoTIFF file](./playground/EIO_fetch_geotiff_example.md) from the [elevation API command line](http://elevation.bopen.eu/en/stable/quickstart.html#command-line-usage), or just use the provided example file `Rome-30m-DEM.tif` which contains the elevation data of the city of Rome, Italy and its outlying area


```bash
Hello World!
I'm getTarget.py
Which GeoTiff file would you like to read?
Enter the GeoTIFF filename: Rome-30m-DEM.tif
```


\[RETURN\]


```bash
The shape of the elevation data is:  (720, 1080)
The raw Elevation data is:
[[133 132 131 ... 126 131 134]
 [131 131 130 ... 120 122 127]
 [129 128 127 ... 110 114 119]
 ...
 [ 10  10  10 ... 221 223 225]
 [ 10  10  10 ... 226 230 232]
 [  9   9  10 ... 234 236 237]]
x0: 12.3499 dx: 0.000277778 ncols: 1080 x1: 12.6499
y0: 42.0001 dy: -0.000277778 nrows: 720 y1: 41.8001
Please enter aircraft latitude in (+/-) decimal form:
```


The preceeding numbers are provided for the user as debug information, but are not necessary during normal operation


Next, enter the latitude, then longitude, then altitude of the aircraft:


```bash
Please enter aircraft latitude in (+/-) decimal form: 41.801
Please enter aircraft longitude in (+/-) decimal form: 12.6483
Please enter altitude (meters from sea-level) in decimal form: 500
Please enter camera azimuth (0 is north) in decimal form (degrees):
```


Next, enter the heading of the aircraft (in degrees, 0 is north and increasing clock-wise) and the angle of declanation \[theta\] of the camera (in degrees, 0 is straight forward and increasing up to a maximum of 90 which is straight downwards)


The accuracy of the positional resolution is better at steep angles (high theta) when the camera is not close to parallel with the ground near the target


```bash
Please enter camera azimuth (0 is north) in decimal form (degrees): 315
Please enter angle of declanation (degrees down from forward) in decimal form: 20
direction is: 135.0
sum of squares is 1.0 : True
deltax is -0.6645
deltay is 0.6645
deltaz is -0.342
Approximate range to target: 1035.0253891233806
Target lat: 41.807184493793784
Target lon: 12.640003435982031
Approximate alt (constructed): 146.00915165793225
Approximate alt (terrain): 146.5
```


`direction` and `sum of squares` are debug output and can be ignored during normal operation


`deltax` is the factor of change in position East/West in meters per iteration


`deltay` is the factor of change in position North/South in meters per iteration


`deltaz` is the factor of change in position Skyward/Groundward (up/down) in meters per iteration. This value should always be negative


The distance of each iterative step, in meters, is defined by the `increment` variable in `getTarget.py`


The information in the following output lines represents the final positional resolution obtained by the approximate intersection of the constructed line emitted from the aircraft's camera and the ground as represented by the terrain data


While the resolution obtained will have many decimal places of information, much of this is due to [floating point imprecision](https://www.youtube.com/watch?v=9hdFG2GcNuA) and digits beyond three significant figures can be ignored. The values should also be tested for correctness and not relied upon in the current version of this program.


`Approximate range to target:` represents the direct-line distance in meters from the aircraft to the target. This may be useful for an operator to determine if the target match is in the expected place. To obtain the horizontal distance, multiply this number times the cosine of theta


`Target lat.` represents the latitude of the target to which the camera is likely aiming at.


`Target lon.` represents the longitude of the target to which the camera is likely aiming at.


`Approximate alt (constructed)` represents the aproximate altitude (in meters from sea level) of the target according to the altitude of the last iteration along the constructed line


`Approximate alt (terrain):` represents the aproximate altitude (in meters from sea level) of the target according to the average altitude of the 4 terrain data points closest to the final lat./lon. pair


The program `getTarget.py` will then exit


# Military Uses
Especially when employed with precision smart munitions (e.g. [artillery](https://asc.army.mil/web/portfolio-item/ammo-excalibur-xm982-m982-and-m982a1-precision-guided-extended-range-projectile/), aerial, etc.) this would greatly aid the safety and processes of the [forward artillery observer](https://en.wikipedia.org/wiki/Artillery_observer) using soley inexpensive consumer electronics, all while reducing the risk of operator error (mismeasurement, miscalculation, etc.) and subsequent risk of friendly-fire incidents and risk to civilian lives.

In addition, a passive optical-based approach to target identification does not trigger the active protection system(s) of targets, including armored vehicles. This can be highly beneficial depending on the usage environment.

# Civilian Uses

This technology can be used for search and rescue operations, wildfire detection and management, measuring and surveying for civic engineering, and many other commercial purposes.

# US Arms export control notice
This software falls under the [Dual Use Technology](https://en.wikipedia.org/wiki/Dual-use_technology#United_States) category under applicable U.S. arms export control laws. If you are using this software in a country that is under restriction from the United States under the Arms Export Control Act, you may only use this for civilian purposes and may not use this software in conflict. This author is not responsible for unauthorized usage of this open source project
