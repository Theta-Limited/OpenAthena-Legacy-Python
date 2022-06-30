# coding=utf=8
#!/usr/bin/env python

# Code adapted from https://gis.stackexchange.com/a/418152/205005 user Nickname Nick
#     converted to Python by mkrupczak3
import math
import numpy as np

from WGS84_SK42_Translator import Translator as Translator # rafasaurus' SK42 coord translator

class Projector(object):

    # Параметры эллипсоида Красовского #Parameters of the Krasovsky ellipsoid
    a = Translator.aP                                # Большая (экваториальная) полуось # Large (equatorial) semi-axis
    b = np.float64(6356863.019)                      # Малая (полярная) полуось # Small (polar) semi-axis
    e2 = (math.pow(a,2)-math.pow(b,2))/math.pow(a,2) # Эксцентриситет # Eccentricity
    n = (a-b)/(a+b)                                  # Приплюснутость # Flatness

    # Параметры зоны Гаусса-Крюгера # Parameters of the Gauss-Kruger zone
    F = np.float64(1.0)             # Масштабный коэффициент # Scale factor
    Lat0 = np.float64(0.0)          # Начальная параллель (в радианах) # Initial parallel (in radians)

    @classmethod
    def SK42_Gauss_Kruger(cls, SK42_LatDegrees, SK42_LongDegrees):
        if SK42_LongDegrees < 0:
            SK42_LongDegrees = 360 + SK42_LongDegrees
        zone = int(SK42_LongDegrees/6.0 + 1)

        Lon0 = (zone*6-3)* math.pi/180  # Центральный меридиан (в радианах) # Central Meridian (in radians)
        N0 = np.float64(0.0)            # Условное северное смещение для начальной параллели # Conditional north offset for the initial parallel
        E0 = zone*1e6+500000.0;         # Условное восточное смещение для центрального меридиана#Conditional eastern offset for the central meridian

        # Перевод широты и долготы в радианы # Converting latitude and longitude to radians
        Lat = SK42_LatDegrees*math.pi/180.0
        Lon = SK42_LongDegrees*math.pi/180.0

        # Вычисление переменных для преобразования # Calculating variables for conversion
        sinLat = math.sin(Lat)
        cosLat = math.cos(Lat)
        tanLat = math.tan(Lat)

        v = cls.a * cls.F * math.pow(1-cls.e2* math.pow(sinLat,2),-0.5)
        p = cls.a*cls.F*(1-cls.e2) * math.pow(1-cls.e2*math.pow(sinLat,2),-1.5)
        n2 = v/p-1
        M1 = (1+cls.n+5.0/4.0* math.pow(cls.n,2) +5.0/4.0* math.pow(cls.n,3)) * (Lat-cls.Lat0)
        M2 = (3*cls.n+3* math.pow(cls.n,2) +21.0/8.0* math.pow(cls.n,3)) * math.sin(Lat - cls.Lat0) * math.cos(Lat + cls.Lat0)
        M3 = (15.0/8.0* math.pow(cls.n,2) +15.0/8.0* math.pow(cls.n,3))*math.sin(2 * (Lat - cls.Lat0))*math.cos(2 * (Lat + cls.Lat0))
        M4 = 35.0/24.0* math.pow(cls.n,3) *math.sin(3 * (Lat - cls.Lat0)) * math.cos(3 * (Lat + cls.Lat0))
        M = cls.b*cls.F*(M1-M2+M3-M4)
        I = M+N0
        II = v/2 * sinLat * cosLat
        III = v/24 * sinLat * math.pow(cosLat,3) * (5-math.pow(tanLat,2)+9*n2)
        IIIA = v/720 * sinLat * math.pow(cosLat,5) * (61-58*math.pow(tanLat,2)+math.pow(tanLat,4))
        IV = v * cosLat
        V = v/6 * math.pow(cosLat,3) * (v/p-math.pow(tanLat,2))
        VI = v/120 * math.pow(cosLat,5) * (5-18*math.pow(tanLat,2)+math.pow(tanLat,4)+14*n2-58*math.pow(tanLat,2)*n2)

        # Вычисление северного и восточного смещения (в метрах) # Calculation of the north and east offset (in meters)
        N = I+II* math.pow(Lon-Lon0,2)+III* math.pow(Lon-Lon0,4)+IIIA* math.pow(Lon-Lon0,6)
        E = E0+IV*(Lon-Lon0)+V* math.pow(Lon-Lon0,3)+VI* math.pow(Lon-Lon0,5)

        E -= zone * 1e6 # subtract the zone number back out from the Easting reference

        return(zone, N, E)

    # end def SK42_Gauss_Kruger
