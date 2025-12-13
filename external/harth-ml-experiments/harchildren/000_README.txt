
This README file was generated on [2024-08-28] (YYYY-MM-DD) by [Marte Fossflaten Tørring].
Last updated: [2024-08-28].


-------------------
GENERAL INFORMATION
-------------------
// Title of Dataset: NTNU-HARChildren for the Validation of HAR-models for typically developing children and children with Cerebral Palsy.
// DOI: 10.18710/EPCXCC
// Contact Information

     // Name: Marte Fossflaten Torring 
     // Institution: Norwegian University of Science and Technology, Department of Neuromedicine and Movement Science 
     // Email: marte.f.torring@ntnu.no
     // ORCID:0000-0002-7029-226X

     // Name: Aleksej Logacjov
     // Institution: Norwegian University of Science and Technology, Department of Computer Science
     // Email: aleksej.logacjov@ntnu.no
     // ORCID: 0000-0002-8834-1744

     // Name: Ellen Marie Bardal 
     // Institution: Norwegian University of Science and Technology, Department of Neuromedicine and Movement Science
     // Email: ellen.bardal@ntnu.no
     // ORCID: 


// Contributors: See metadata field Contributor.
// Data Type: Sensor data with aligned annotations as .csv files.
// Date of data collection/generation: The data collection started 19.10.2016 and ended 16.08.2019
// Geographic location: Trondheim, Norway.
// Funding sources: Norwegian University of Science and Technology (NTNU) 

// Description of dataset:
The NTNU-HARChildren dataset contains accelerationfiles from 16 children with Cerebral Palsy(CP), Gross Motor Function Classification Scale (GMFCS) I and II and 63 typically developing (TD) children wearing two accelerometers, one at the thigh and one on the lower back, together with the corresponding annotations (sitting, stanidng, walking, shuffling, stair ascending/decending, lying down, sit cycling, stand cycling, running, bending, jumping, transition). The annotation were created using video recordings. The study protocol was approved by the Regional Committee for Medical and Health research ethics (reference no:2016/707/REK nord) and the Norwegian Center for Research Data (reference no:50683). All participants and guardians signed a written informed consent before being enrolled in the study. The NTNU-HARChildren data set was used for machine learning experiments in our published paper: "Validation of two novel human activity recognition models for typically developing children and children with Cerebral Palsy." 
--------------------------
METHODOLOGICAL INFORMATION
--------------------------
// Description of sources and methods used for collection/generation of data:
The study included 63 TD children (35 male, 28 female) with mean (standard deviation) age of 10.5 (2.6) years (range 6-15) and 16 CP children (8 male, 8 female) with mean(standard deviation) age of 11.4 (2.2) years (range 8-17). The CP children were recruited through the outpatient clinic and habilitation unit at St. Olavs University Hospital, Trondheim, Norway. The TD children were recruited through a local primary or junior high school.The study protocol was approved by the Regional Committee for Medical and Health research ethics (reference no. nr:2016/707/REK nord) and the Norwegian Center for Research Data (NSD-nr:50683). All participants and guardians signed a written informed consent before being enrolled in the study. 
The accelerometer and video recordings were performed in a laboratory or gymnasium, as well as outdoors, and both indivdual and in groups of children. The children wore two three-axial AX3 accelerometers (Axivity Ltd., Newcastle, UK). The accelerometers were attached to the skin at the participants lower back, approximately at the third lumbar vertebra, and the upper thigh, approximately 10 cm above the upper border of the patella. Body accelerations were recorded with a sampling rate of 100 Hz 200 Hz and later downsampled to 50 Hz. The video recordings were manually annotated using Anvil video annotation tool (version 6). These downsampled accelerometer signals was syncronized with the annotation files. 

// Methods for processing the data:
The recordings are given in 50Hz. The data is provided for each subject as a separate file with syncronized accelerometer signal and annotation. Since the files are .csv files, they can easily be read using data analysis tools.

// Facility-, instrument- or software-specific information needed to interpret the data:
The data can be read using any data analysis tool that can read .csv files.


--------------------
DATA & FILE OVERVIEW
--------------------
The files named 001-120 is individuals with CP, and the files named PM01-16 and TD01-48 is typically developing children.

// File List:
Each subject is stored as a separate file with the subject ID being the filename. Each file contains the following columns: 
- timestamp: Timestamp of the recorded sample in the format
- back_x: Acceleration in x-direction at the lower back in the unit g
- back_y: Acceleration in y-direction at the lower back in the unit g
- back_z: Acceleration in z-direction at the lower back in the unit g
- thigh_x: Acceleration in x-direction at the thigh in the unit g
- thigh_y: Acceleration in y-direction at the thigh in the unit g
- thigh_z: Acceleration in z-direction at the thigh in the unit g
- label: Activity code 

The labels are coded as follows:
    % 1=walking
    % 2=running
    % 3=shuffling
    % 4=stairs (ascending)
    % 5=stairs (descending)
    % 6=standing
    % 7=sitting
    % 8=lying
    % 9=transition
    % 10=bending
    % 13=cycling (sit)
    % 14=cycling (stand)
    % 20=jumping


--------------------------
SHARING/ACCESS INFORMATION
--------------------------
// Licenses/Restrictions: See Terms tab.
// Data sources: See metadata field Data Sources.
// Recommended citation: See citation generated by repository.
