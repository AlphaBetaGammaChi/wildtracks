README

This data file is published by the Movebank Data Repository (www.datarepository.movebank.org). As of the time of publication, a version of the published animal tracking data set can be viewed on Movebank (www.movebank.org) in the study "MPIO white stork lifetime tracking data (2013-2014)". Individual attributes in the data files are defined below and in the Movebank Attribute Dictionary, available at www.movebank.org/node/2381.

This data package includes the original data, including missing fixes, and not interpolated records to replace missing fixes used for analysis as described in Flack et al. 2015.

This data package includes the following data files:
MPIO white stork lifetime tracking data (2013-2014)-acceleration-1of4.csv.zip
MPIO white stork lifetime tracking data (2013-2014)-acceleration-2of4.csv.zip
MPIO white stork lifetime tracking data (2013-2014)-acceleration-3of4.csv.zip
MPIO white stork lifetime tracking data (2013-2014)-acceleration-4of4.csv.zip
MPIO white stork lifetime tracking data (2013-2014)-gps.csv.zip
MPIO white stork lifetime tracking data (2013-2014)-reference-data.csv

These data are described in the following written publication:
Flack A, Fiedler W, Blas J, Pokrovski I, Kaatz M, Mitropolsky M, Aghababyan K, Fakriadis Y, Makrigianni E, Jerzak L, Shamina C, Azafzaf H, Rotics S, Nathan R, Wikelski M, in prep, Migration costs of eight Eurasian white stork populations.

These data make up a portion of the data shown in Figure 1c of this publication:
Kays R, Crofoot MC, Jetz W, Wikelski M (2015) Terrestrial animal tracking as an eye on life and planet. Science 348. doi:10.1126/science.aaa2478

Data package citation:
Flack A, Fiedler W, Blas J, Pokrovski I, Mitropolsky M, Kaatz M, Aghababyan K, Khachatryan A, Fakriadis Y, Makrigianni E, Jerzak L, Shamin M, Shamina C, Azafzaf H, Feltrup-Azafzaf C, Mokotjomela T, Wikelski M (2015) Data from: Migration costs of eight Eurasian white stork populations. Movebank Data Repository. doi:10.5441/001/1.78152p3q

-----------

Terms of Use
This data file is licensed by the Creative Commons Zero (CC0 1.0) license. The intent of this license is to facilitate the re-use of works. The Creative Commons Zero license is a "no rights reserved" license that allows copyright holders to opt out of copyright protections automatically extended by copyright and other laws, thus placing works in the public domain with as little legal restriction as possible. However, works published with this license must still be appropriately cited following professional and ethical standards for academic citation.

We highly recommend that you contact the data creator if possible if you will be re-using or re-analyzing data in this file. Researchers will likely be interested in learning about new uses of their data, might also have important insights about how to properly analyze and interpret their data, and/or might have additional data they would be willing to contribute to your project. Feel free to contact us at support@movebank.org if you need assistance contacting data owners.

See here for the full description of this license
http://creativecommons.org/publicdomain/zero/1.0

-----------

Data Attributes
These definitions come from the Movebank Attribute Dictionary, available at www.movebank.org/node/2381.

animal death comments: Comments about the death of the animal.
	example: hit by a car

animal ID: An individual identifier for the animal, provided by the data owner. This identifier can be a ring number, a name, the same as the associated tag ID, etc. If the data owner does not provide an Animal ID, an internal Movebank animal identifier may sometimes be shown.
	example: 91876A, Gary
	same as: individual-local-identifier

animal life stage: The age class or life stage of the animal at the beginning of the deployment. Can be years or months of age or terms such as "adult", "subadult" and "juvenile". Units should be defined in the values (e.g. "2 years").
	example: juvenile, adult
	units: Any units should be defined in the remarks.

animal mass: The mass of an the animal.
	example: 500
	units: grams

attachment type: The way a tag is attached to an animal. Values are chosen from a controlled list:
	collar: The tag is attached by a collar around the animal's neck.
	glue: The tag is attached to the animal using glue.
	harness: The tag is attached to the animal using a harness.
	implant: The tag is placed under the skin of the an animal.
	tape: The tag is attached to the animal using tape.
	other: user specified

deploy off timestamp: The timestamp when the tag deployment ended.
	example: 2009-10-01 12:00:00.000
	format: yyyy-MM-dd HH:mm:ss.sss
	units: UTC (Coordinated Universal Time) or GPS time, which is a few leap seconds different from UTC
	same as: deploy off date

deploy on latitude: The geographic latitude of the location where the animal was released (intended primarily for instances in which the animal release and tag retrieval locations have higher accuracy than those derived from sensor data).
	example: 27.3516
	units: decimal degrees, WGS84 reference system

deploy on longitude: The geographic longitude of the location where the animal was released (intended primarily for instances in which the animal release and tag retrieval locations have higher accuracy than those derived from sensor data).
	example: -97.3321
	units: decimal degrees, WGS84 reference system

deploy on timestamp: The timestamp when the tag deployment started.
	example: 2008-08-30 18:00:00.000
	format: yyyy-MM-dd HH:mm:ss.sss
	units: UTC (Coordinated Universal Time) or GPS time, which is a few leap seconds different from UTC
	same as: deploy on date

deployment comments: Additional information about the tag deployment that is not described by other reference data terms.
	example: This deployment was excluded from analysis because the tag failed.

deployment end type: A categorical classification of the tag deployment end. Values are chosen from a controlled list:
	captured: The tag remained on the animal but the animal was captured or confined.
	dead: The deployment ended with the death of the animal that was carrying the tag.
	equipment failure: The tag stopped working.
	fall off: The attachment of the tag to the animal failed, and it fell of accidentally.
other
	released: The tag remained on the animal but the animal was released from captivity or confinement.
	removal: The tag was purposefully removed from the animal.
	unknown: The deployment ended by an unknown cause.

deployment ID: A unique identifier for the deployment of a tag on animal, provided by the data owner. If the data owner does not provide a Deployment ID, an internal Movebank deployment identifier may sometimes be shown.
	example: Jane-Tag42

duty cycle: Remarks associated with the duty cycle of a tag during the deployment, describing the times it is on/off and the frequency at which it transmits or records data.
	example: it turns off during the night
	units: Any units should be defined in the remarks.

e-obs acceleration axes: This tells you about the enabled ACC axes, like X and/or Y and/or Z (definition from "e-obs GPS-acceleration-tags application note: How to use the acceleration sensor, interpret, analyse its data and how to get values in m/s^2", 2011).
	example: XYZ
	units: none

e-obs acceleration sampling frequency per axis: This is the sampling frequency for one axis. Don't mix this up with the sampling frequency for all axes together. For example if you have three ACC axes enabled, then the sampling frequency for all axes together is three times the sampling frequency for one axis. The sampling frequency is measured in Hertz, which is the same as 1/second. For example a sampling frequency of 10 Hz means that you get 10 samples per second (definition from "e-obs GPS-acceleration-tags application note: How to use the acceleration sensor, interpret, analyse its data and how to get values in m/s^2", 2011).
	example: 5.93
	units: hertz (Hz)

e-obs accelerations raw: Acceleration along the X and or Y and or Z axes of the tag, depending on which axes were activated on the tag as described in the field e-obs acceleration axes. Measurements alternate one measurement for each active axis in alphabetical order. The values are digital readings between 0 and 4095 of the analogue digital converter on the tag, and can be converted to m/s^2 with proper calibration. These samples are made at the rate described by the field e-obs acceleration sampling frequency per axis starting with the first sample at the time described in the field e-obs start timestamp. Tags with numbers e-obs numbers 2242 and higher, which began being provided in spring 2012, have Y-axis values in the opposite direction from those in older tags (definition from "e-obs GPS-acceleration-tags application note: How to use the acceleration sensor, interpret, analyse its data and how to get values in m/s^2", 2011; Wolgang Heidrich, e-obs Digital Telemetry, personal communication, 2012).
	example: 1844 1889 1653 1845 1896 1653 1837 1897 1653 1842 1898 1650 1844 1899 1644 1840…
	units: none (values must be calibrated and converted)

event ID: An identifier for the set of information associated with each record or event in a data set. A unique event ID is assigned to every time-location or other time-measurement record in Movebank.
	example: 6340565
	units: none

latitude (decimal degree): The geographic longitude of a location along an animal track as estimated by the processed sensor data. Positive values are east of the Greenwich Meridian, negative values are west of it.
	example: -121.1761111
	units: decimal degrees, WGS84 reference system
	same as: location lat

location accuracy comments: Comments about the location error estimate values provided using location error text and/or location error numerical. The percentile uncertainty can be provided using location error percentile.
	example: 1 standard deviation errors, assuming normal distribution, provided by the GPS unit

longitude (decimal degree): The geographic longitude of a location along an animal track as estimated by the processed sensor data. Positive values are east of the Greenwich Meridian, negative values are west of it.
	example: -121.1761111
	units: decimal degrees, WGS84 reference system
	same as: location long

manipulation type: The way in which the animal was manipulated during the deployment. Additional details about the manipulation can be provided using manipulation comments. Values are chosen from a controlled list:
	confined: The animal's movement was restricted to within a defined area.
	none: The animal received no treatment other than the tag attachment.
	relocated: The animal was released from a site other than the one at which it was captured.
	manipulated other: The animal was manipulated in some other way, such as a physiological manipulation.

ring ID: A number or color scheme for a band or ring attached to the animal.
	example: 26225
	units: none
	same as: animal ring id

sensor type: The type of sensor with which data were collected. Values are chosen from a controlled list:
	acceleration: The sensor collects acceleration data.
	accessory measurements: The sensor collects accessory measurements, such as battery voltage.
	Argos Doppler Shift: The sensor is using Argos Doppler shift for determining position.
	bird ring: The animal is identified by a ring that has a unique ID.
	GPS: The sensor uses GPS to find location and stores these.
	natural mark: The animal is identified by a natural marking.
	radio transmitter: The sensor is a classical radio transmitter.
	solar geolocator: The sensor collects light levels, which are used to determine position (for processed locations).
	solar geolocator raw: The sensor collects light levels, which are used to determine position (for raw light-level measurements).

study: The name of the study in Movebank in which data are stored.

study site: The name of the deployment site, for example a field station or colony.
	example: Pickerel Island North

study-specific measurement: Values for a study-specific attribute.
	units: undefined
THIS DATASET: Values describe the tracking project through which the record was collected.

tag ID: A unique identifier for the tag, provided by the data owner. If the data owner does not provide a tag ID, an internal Movebank tag identifier may sometimes be shown.
	example: 2342, ptt_4532
	same as: tag local identifier

tag manufacturer name: The company or person that produced the tag.
	example: Holohil
	same as: manufacturer

tag mass: The mass of the tag.
	example: 24
	units: grams

tag readout method: The way the data are received from the tag. Values are chosen from a controlled list:
	satellite: Data are transferred via satellite.
	phone network: Data are transferred via a phone network, such as GSM or AMPS.
	other wireless: Data are transferred via another form of wireless data transfer, such as a VHF radio transmitter/receiver.
	tag retrieval: The tag must be physically retrieved in order to obtain the data.

taxon: The scientific name of the species on which the tag was deployed, as defined by the Integrated Taxonomic Information System (ITIS, www.itis.gov). If the species name can not be provided, this should be the lowest level taxonomic rank that can be determined and that is used in the ITIS taxonomy. Additional information can be provided using the term taxon detail.
	example: Buteo swainsoni
	same as: species, animal taxon, individual taxon canonical name

timestamp: The date and time a sensor measurement was taken.
	example: 2008-08-14 18:31:00.000
	format: yyyy-MM-dd HH:mm:ss.sss
	units: UTC (Coordinated Universal Time) or GPS time, which is a few leap seconds different from UTC

visible: Determines whether an event is visible on the Movebank Search map. Values are calculated automatically, with FALSE indicating that the event has been marked as an outlier by manually marked outlier or algorithm marked outlier. Allowed values are TRUE or FALSE.

-----------

More Information
For more information about this repository, see www.movebank.org/node/15294, the FAQ at www.movebank.org/node/2220, or contact us at support@movebank.org.