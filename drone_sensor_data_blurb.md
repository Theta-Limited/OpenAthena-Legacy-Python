# Getting sensor data

The consumer models of some drones do not display their position, altitude, camera heading, and camera declanation during flight, but do store this data in the [EXIF](https://en.wikipedia.org/wiki/Exif) and [XMP](https://en.wikipedia.org/wiki/Extensible_Metadata_Platform) metadata of their still image captures


One tool to view EXIF and XMP metadata on Mac, Linux, and Windows is Phil Harvey's (not affiliated with this project) [exiftool](https://exiftool.org/)


A future version will allow for extraction and use of EXIF/XMP sensor information from drone photos automatically


An equivalent command line tool available on Mac and Linux is [exiv2](https://exiv2.org/) (also not affiliated)


The following is an example of a command to show the sensor metadata of an image taken from a particular DJI drone:
```bash
exiv2 -P kt DJI_1234.JPG | grep -i "gimbal\|latitude\|longitude\|alt"
```


`drone-dji.GimbalYawDegree` is the direction of the aircraft, from -180 (exclusive) to +180. 0 degrees is North, 90 is East, etc. Internally this number is converted to an `azimuth` for use by OpenAthena
`drone-dji.GimbalPitchDegree` is the amount of pitch of the camera's gimbal. While the DJI displays this number as negative, Internally the absolute value of this number `theta` is used for OpenAthena