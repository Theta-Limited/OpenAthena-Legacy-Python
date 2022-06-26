// from https://gis.stackexchange.com/a/418152/205005 user Nickname Nick:
public double[] WGS84ToSK42Meters(double latWgs84, double longWgs84, double heightWgs84)
        {
//Часть 1: Перевод Wgs84 географических координат(долготы и широты в градусах) в СК42 географические координаты (долготу и широту в градусах)//Part 1: Converting Wgs84 geographical coordinates(longitude and latitude in degrees) to SK42 geographical coordinates(longitude and latitude in degrees)
            double ro = 206264.8062;//Число угловых секунд в радиане//The number of angular seconds in radians
            double aP = 6378245; // Большая полуось//Large semi - axis
            double alP = 1 / 298.3; // Сжатие//Compression
            double e2P = 2 * alP - Math.pow(alP,2); // Квадрат эксцентриситета//Eccentricity square

            // Эллипсоид WGS84 (GRS80, эти два эллипсоида сходны по большинству параметров)//Ellipsoid WGS84 (GRS80, these two ellipsoids are similar in most parameters)
            double aW = 6378137; // Большая полуось//Large semi - axis
            double alW = 1 / 298.257223563; // Сжатие//Compression
            double e2W = 2 * alW - Math.pow(alW, 2); // Квадрат эксцентриситета//Eccentricity square

            // Вспомогательные значения для преобразования эллипсоидов
//Auxiliary values for converting ellipsoids
            double a1 = (aP + aW) / 2;
            double e21 = (e2P + e2W) / 2;
            double da = aW - aP;
            double de2 = e2W - e2P;

            // Линейные элементы трансформирования, в метрах//Linear transformation elements, in meters
            double dx = 23.92;
            double dy = -141.27;
            double dz = -80.9;

            // Угловые элементы трансформирования, в секундах//Angular transformation elements, in seconds
            double wx = 0;
            double wy = 0;
            double wz = 0;

            // Дифференциальное различие масштабов//Differential difference of scales
            double ms = 0;

            double B, L, M11, N1;
            B = latWgs84 * Math.PI / 180;
            L = longWgs84 * Math.PI / 180;
            M11 = a1 * (1 - e21) / Math.pow((1 - e21 * Math.pow(Math.sin(B),2)),1.5);
            N1 = a1 * Math.pow((1 - e21 * Math.pow(Math.sin(B),2)),-0.5);
            double dB = ro / (M11 + heightWgs84) * (N1 / a1 * e21 * Math.sin(B) * Math.cos(B) * da + (Math.pow(N1,2) / Math.pow(a1,2) + 1) * N1 * Math.sin(B) * Math.cos(B) * de2 / 2 - (dx * Math.cos(L) + dy * Math.sin(L)) * Math.sin(B) + dz * Math.cos(B)) - wx * Math.sin(L) * (1 + e21 * Math.cos(2 * B)) + wy * Math.cos(L) * (1 + e21 * Math.cos(2 * B)) - ro * ms * e21 * Math.sin(B) * Math.cos(B);

            double SK42_LatDegrees = latWgs84 - dB / 3600;//широта в ск42 в градусах//latitude in sk42 in degrees

            B = latWgs84 * Math.PI / 180;
            L = longWgs84 * Math.PI / 180;
            N1 = a1 * Math.pow((1 - e21 * Math.pow(Math.sin(B),2)), -0.5);
            double dL = ro / ((N1 + heightWgs84) * Math.cos(B)) * (-dx * Math.sin(L) + dy * Math.cos(L)) + Math.tan(B) * (1 - e21) * (wx * Math.cos(L) + wy * Math.sin(L)) - wz;

            double SK42_LongDegrees = longWgs84 - dL / 3600;//долгота в ск42 в градусах//longitude in sk42 in degrees

// Часть 2: Перевод СК42 географических координат (широты и долготы в градусах) в СК42 прямоугольные координаты (северное и восточное смещения в метрах)//Part 2: Converting of SK42 geographical coordinates (latitude and longitude in degrees) into SK42 rectangular coordinates(easting and northing in meters)
            // Номер зоны Гаусса-Крюгера//Number of the Gauss-Kruger zone
            int zone =  (int) (SK42_LongDegrees/6.0+1);

            // Параметры эллипсоида Красовского//Parameters of the Krasovsky ellipsoid
            double a = 6378245.0;          // Большая (экваториальная) полуось//Large (equatorial) semi-axis
            double b = 6356863.019;        // Малая (полярная) полуось//Small (polar) semi-axis
            double e2 = (Math.pow(a,2)-Math.pow(b,2))/Math.pow(a,2);  // Эксцентриситет//Eccentricity
            double n = (a-b)/(a+b);        // Приплюснутость//Flatness


            // Параметры зоны Гаусса-Крюгера//Parameters of the Gauss-Kruger zone
            double F = 1.0;                   // Масштабный коэффициент//Scale factor
            double Lat0 = 0.0;                // Начальная параллель (в радианах)//Initial parallel (in radians)
            double Lon0 = (zone*6-3)* Math.PI/180;  // Центральный меридиан (в радианах)//Central Meridian (in radians)
            double N0 = 0.0;                  // Условное северное смещение для начальной параллели//Conditional north offset for the initial parallel
            double E0 = zone*1e6+500000.0;    // Условное восточное смещение для центрального меридиана//Conditional eastern offset for the central meridian

            // Перевод широты и долготы в радианы//Converting latitude and longitude to radians
            double Lat = SK42_LatDegrees*Math.PI/180.0;
            double Lon = SK42_LongDegrees*Math.PI/180.0;

            // Вычисление переменных для преобразования//Calculating variables for conversion
            double sinLat = Math.sin(Lat);
            double cosLat = Math.cos(Lat);
            double tanLat = Math.tan(Lat);

            double v = a * F * Math.pow(1-e2* Math.pow(sinLat,2),-0.5);
            double p = a*F*(1-e2) * Math.pow(1-e2*Math.pow(sinLat,2),-1.5);
            double n2 = v/p-1;
            double M1 = (1+n+5.0/4.0* Math.pow(n,2) +5.0/4.0* Math.pow(n,3)) * (Lat-Lat0);
            double M2 = (3*n+3* Math.pow(n,2) +21.0/8.0* Math.pow(n,3)) * Math.sin(Lat - Lat0) * Math.cos(Lat + Lat0);
            double M3 = (15.0/8.0* Math.pow(n,2) +15.0/8.0* Math.pow(n,3))*Math.sin(2 * (Lat - Lat0))*Math.cos(2 * (Lat + Lat0));
            double M4 = 35.0/24.0* Math.pow(n,3) *Math.sin(3 * (Lat - Lat0)) * Math.cos(3 * (Lat + Lat0));
            double M = b*F*(M1-M2+M3-M4);
            double I = M+N0;
            double II = v/2 * sinLat * cosLat;
            double III = v/24 * sinLat * Math.pow(cosLat,3) * (5-Math.pow(tanLat,2)+9*n2);
            double IIIA = v/720 * sinLat * Math.pow(cosLat,5) * (61-58*Math.pow(tanLat,2)+Math.pow(tanLat,4));
            double IV = v * cosLat;
            double V = v/6 * Math.pow(cosLat,3) * (v/p-Math.pow(tanLat,2));
            double VI = v/120 * Math.pow(cosLat,5) * (5-18*Math.pow(tanLat,2)+Math.pow(tanLat,4)+14*n2-58*Math.pow(tanLat,2)*n2);

            // Вычисление северного и восточного смещения (в метрах)//Calculation of the north and east offset (in meters)
            double N = I+II* Math.pow(Lon-Lon0,2)+III* Math.pow(Lon-Lon0,4)+IIIA* Math.pow(Lon-Lon0,6);
            double E = E0+IV*(Lon-Lon0)+V* Math.pow(Lon-Lon0,3)+VI* Math.pow(Lon-Lon0,5);

            return new double[] {N, E};
        }
