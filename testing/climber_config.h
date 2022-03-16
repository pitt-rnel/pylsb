#ifndef _CLIMBER_CONFIG_
#define _CLIMBER_CONFIG_

#ifndef _RTMA_TYPES_H_
#include "../../rtma/include/RTMA_types.h"
#endif //_RTMA_TYPES_H_

#include "mjvr_types.h"

// Default address of the message manager
#define DEFAULT_MM_IP "localhost:7111"

#define MAX_SPIKE_SOURCES 2
#define MAX_SPIKE_SOURCES_N256 1 // single 256 neuroport used in Chicago
#define MAX_SPIKE_CHANS_PER_SOURCE 128
#define MAX_SPIKE_CHANS_PER_SOURCE_N256 256 // 256 neuroport used in Chicago
#define MAX_COINCIDENT_SPIKES 45			// threshold for coincidence detection (>= MAX_COINCIDENT_SPIKES with same timestamp are ignored)
#define MAX_ANALOG_CHANS 16
#define MAX_UNITS_PER_CHAN 5 // Units 1..5 are sorted, Unit 0 is unsorted threshold crossings (not including the sorted units)
#define MAX_TOTAL_SPIKE_CHANS_PER_SOURCE (MAX_SPIKE_CHANS_PER_SOURCE * MAX_UNITS_PER_CHAN)
#define MAX_TOTAL_SPIKE_CHANS_PER_SOURCE_N256 (MAX_SPIKE_CHANS_PER_SOURCE_N256 * MAX_UNITS_PER_CHAN)
#define MAX_TOTAL_SPIKE_CHANS (MAX_SPIKE_SOURCES * MAX_TOTAL_SPIKE_CHANS_PER_SOURCE)
#define MAX_TOTAL_SPIKE_CHANS_N256 (MAX_SPIKE_SOURCES_N256 * MAX_TOTAL_SPIKE_CHANS_PER_SOURCE_N256) // should equal MAX_TOTAL_SPIKE_CHANS
#define LFPSAMPLES_PER_HEARTBEAT 10																	//LFP sampled at 1kHz, heartbeats at 10ms==100Hz therefore 10 samples agregated
#define ANALOGSAMPLES_PER_HEARTBEAT 10
#define RAW_COUNTS_PER_SAMPLE 2						 // MAJOR CHANGE FROM HST1: CHANGING FROM 3 TO 2 TO INCREASE SAMPLE FREQ FROM 33Hz TO 50 Hz
#define SAMPLE_LENGTH (0.01 * RAW_COUNTS_PER_SAMPLE) // seconds
#define SNIPPETS_PER_MESSAGE 25
#define SAMPLES_PER_SNIPPET 48 //from Blackrock Setting
#define MAX_DIG_PER_SAMPLE 10
#define MAX_DATAGLOVE_SENSORS 18
#define NUM_DOMAINS 6
#define MAX_COMMAND_DIMS 30
#define MPL_RAW_PERCEPT_DIMS 54
// STIM DEFINES
#define NUM_STIM_CHANS 64
#define SHAM_STIM_CHANS 32 // bank C
#define MAX_STIM_CHANS_ON 12
#define PULSE_TRAIN_SIZE 101 //probably want to make this so it isn't hardcoded
#define MAX_CS_CONFIGS 16
#define NUM_SPIKES_PER_STIM_MSG 26 //Even number for byte balancing

// Grapevine defines
#define MAX_XIPP_EEG_HEADSTAGES 2
#define MAX_XIPP_CHANS 32 * MAX_XIPP_EEG_HEADSTAGES
#define MAX_XIPP_ANALOG_CHANS 32
#define XIPP_SAMPLES_PER_MSG 20
#define MAX_MYO_EMG_CHANS 8
#define MYO_SAMPLES_PER_MSG 4

#define GRIP_DIMS_R 1 //how many of the ROC grasps to use simultaneously.
#define GRIP_DIMS_L 1 //how many of the ROC grasps to use simultaneously.
#define MAX_GRIP_DIMS 9
#define MAX_GRIPPER_DIMS 1		   // 1, 5 for Prensilia
#define MAX_GRIPPER_JOINT_ANGLES 5 // joint angles for gripper tasks, TBD
#define MAX_GRIPPER_FORCES 5	   // 2, 6 for Prensilia
#define MJ_MAX_MOTOR MAX_GRIPPER_DIMS
#define MJ_MAX_JOINT MAX_GRIPPER_JOINT_ANGLES
#define MJ_MAX_CONTACT MAX_GRIPPER_FORCES

// MujocoVR Defines
// moved to mjvr_types.h

//ResultCodes: (Should be arranged as binary style flags to be added together)
#define NoResult -1 //not to be combined with other codes
#define SuccessfulTrial 1
#define BadTrial 2
#define ManualProceed 4
#define ManualFail 8

//Deka Hand Constants
#define HX_DEKA_LUKE_CONTACT_COUNT 13
#define HX_LUKE_MOTOR_COUNT 6

//Right Hand Robotics
#define NUM_FINGERS 3
#define NUM_SENSORS_PER_FINGER 9
#define NUM_SENSORS_PALM 11
#define NUM_TAKKTILE (NUM_FINGERS * NUM_SENSORS_PER_FINGER + NUM_SENSORS_PALM)
#define NUM_ENCODERS NUM_FINGERS
#define NUM_SERVOS 4
#define NUM_DYNAMIXEL NUM_SERVOS

//
// Module ID-s PLEASE KEEP MIDs IN ASCENDING ORDER, DO NOT DUPLICATE, AND STAY WITHIN RANGE 10-99!
//
#define MID_JSTICK_COMMAND 10
#define MID_COMBINER 11
#define MID_CEREBUS 12 //DO NOT ADD ANYTHING BETWEEN 12 and 20! the cerebus module adds nsp_index to this to maintain unique numbers

#define MID_INPUT_TRANSFORM 20
#define MID_RPPL_RECORD 21
#define MID_CENTRAL 22 //DO NOT ADD ANYTHING BETWEEN 22 and 30! the NSPCentralControl module adds nsp_index to this to maintain unique numbers

#define MID_EXTRACTION 30 // retired MID_LFPEEXTRACTION (31), MID_CREATEBUFFER (35)
#define MID_MYO 31

#define MID_MPL_CONTROL 40
#define MID_GRIP_CONTROL 41

//DEKA MIDS
#define MID_DEKA_CAN_MODULE 42
#define MID_DEKA_ACI_RESPONSE 43
#define MID_DEKA_DISPLAY 44 // previously: 47
// NREC WAM IDS (RETIRED, CAN REUSE)
//#define MID_NREC_WAM_RECV	    	44
// #define MID_NREC_WAM_SEND		45
#define MID_PSYCHTLBX 46
//2018-08-23 Royston: working on PsychoPy-RTMA integration, added a module for testing
#define MID_STIM_PRESENT 48

#define MID_ACTIVE_ASSIST 50
// KUKA MIDS
#define MID_KUKA_DISPLAY 51
#define MID_ROBOTICS_FEEDBACK_INTEGRATOR 52
#define MID_KUKA_INTERFACE_MODULE	53
#define MID_KUKA_JOINT_COMMAND_DISPLAY   54
#define MID_KUKA_DIAGNOSTICS		55
#define MID_TASKA_DRIVER            56
//
#define MID_FORCE_PLATFORM 58
#define MID_FORCE_PLATFORM_DISPLAY 59

#define MID_MPL_FEEDBACK 60
//#define MID_MUJOCO_VR_MODULE      61 // MujocoVR C++ Module // def moved to mjvr_types.h
#define MID_AJA_CONTROL 65	// python module to control Aja Ki Pro Mini video recorder
#define MID_SEAIOCONTROL 66 // module to send digital high/low from SeaIO card in stim computer

#define MID_EXECUTIVE 70
#define MID_COMMENT_MANAGER 71

#define MID_FLIP_THAT_BUCKET_MESSENGER 74

#define MID_VOLTAGE_MONITOR_GUI 76
#define MID_VOLTAGE_MONITOR 77
#define MID_ATIsensor 78

// RETIRED MID_GENERIC (80) REPLACED WITH DYNAMIC MID 0. Also retired MID_VISUALATION (82), MID_VIDEO_LOGGER (83), MID_AUDIO_LOGGER (84), MID_DATAGLOVE_CONTROL (85)
#define MID_MESSAGERATES 81 // Diagnostic module (USED BY LOADER)
#define MID_VISUAL_GRATING 85
#define MID_BIASMODULE 86
#define MID_CURSOR 87
// RIGHT HAND GRIPPER Modules
#define MID_RHR_COMMAND_MODULE 88
#define MID_RHR_SENSOR_MODULE 89

#define MID_SOUNDPLAYER 90 // retired MID_KNOB_FEEDBACK (94), MID_APLSENDER (98), MID_APLRECEIVER (99)
#define MID_RFDISPLAY 91
#define MID_RFACTIVITY 92
#define MID_ImageDisplayer 93

// Predict movement intent
#define MID_FLIP_THAT_BUCKET 94

// Stim MIDs
#define MID_STIM_SAFETY_MODULE 95
#define MID_SENSOR_STIM_TRANS_MODULE 96
#define MID_CERESTIM_CONTROL 97
#define MID_SENSE_TOUCH_INTERFACE 98
#define MID_SENSOR_STIM_TRANSFORM_PY 99

// Module ID
#define MID_MECH_STIM_MODULE 0

//
// Message ID-s THERE IS NO REASON THESE NEED TO START AT 1700, values > 99 are allowed
//
#define MT_FINISHED_COMMAND 1700
#define MT_CONTROL_SPACE_FEEDBACK 1701
#define MT_CONTROL_SPACE_COMMAND 1702
#define MT_MPL_RAW_PERCEPT 1703
#define MT_BIAS_COMMAND 1704
#define MT_MPL_REBIASED_SENSORDATA 1705
#define MT_CONTROL_SPACE_FEEDBACK_RHR_GRIPPER 1706
#define MT_CONTROL_SPACE_POS_COMMAND 1710
#define MT_MPL_SEGMENT_PERCEPTS 1711
#define MT_WAM_FEEDBACK 1712
#define MT_IMPEDANCE_COMMAND 1713
#define MT_EXECUTIVE_CTRL 1714

#define MT_CURSOR_FEEDBACK 1720
#define MT_VISUAL_GRATING_BUILD 1721
#define MT_VISUAL_GRATING_RESPONSE 1722

#define MT_GRIP_COMMAND 1730
#define MT_GRIP_FINISHED_COMMAND 1731
#define MT_GRIPPER_FEEDBACK 1732
#define MT_MUJOCO_SENSOR 1733
#define MT_MUJOCO_CMD 1734
#define MT_MUJOCO_MOVE 1735
#define MT_MUJOCO_MSG 1736
#define MT_MUJOCO_GHOST_COLOR 1737
#define MT_MUJOCO_OBJMOVE 1738
#define MT_OPENHAND_CMD 1740
#define MT_OPENHAND_SENS 1741
#define MT_PRENSILIA_SENS 1742
#define MT_PRENSILIA_CMD 1743
#define MT_TABLE_LOAD_CELLS 1744
#define MT_REZERO_GRIPPER_SENSORS 1745

#define MT_SINGLETACT_DATA 1760

#define MT_RAW_SPIKECOUNT 1800
#define MT_SPM_SPIKECOUNT 1801
#define MT_SPIKE_SNIPPET 1802
#define MT_RAW_CTSDATA 1803
#define MT_SPM_CTSDATA 1804
#define MT_REJECTED_SNIPPET 1805
#define MT_RAW_DIGITAL_EVENT 1806
#define MT_SPM_DIGITAL_EVENT 1807
#define MT_STIM_SYNC_EVENT 1808 // special type of digital event
#define MT_STIM_UPDATE_EVENT 1809
#define MT_CENTRALRECORD 1810
#define MT_RAW_ANALOGDATA 1811
#define MT_SPM_ANALOGDATA 1812
#define MT_RAW_SPIKECOUNT_N256 1815
#define MT_RAW_CTSDATA_N256 1816
#define MT_SAMPLE_GENERATED 1820
#define MT_XIPP_EMG_DATA_RAW 1830
#define MT_MYO_EMG_DATA 1831 // myo band emg
#define MT_MYO_KIN_DATA 1832 // myo band kinematics

#define MT_INPUT_DOF_DATA 1850
#define MT_DATAGLOVE 1860
#define MT_OPTITRACK_RIGID_BODY 1861

#define MT_TASK_STATE_CONFIG 1900
#define MT_PHASE_RESULT 1901
#define MT_EXTRACTION_RESPONSE 1902
#define MT_NORMALIZATION_FACTOR 1903
#define MT_TRIAL_METADATA 1904
#define MT_EXTRACTION_REQUEST 1905 // signal to request an extraction response
#define MT_UPDATE_UNIT_STATE 1906
#define MT_DISABLED_UNITS 1907
#define MT_TRIAL_END 1910			  // signal at end of trial_num
#define MT_REP_START 1911			  // msg at beginning of rep w/ rep num (added for communication between open-loop stim and touch interface)
#define MT_REP_END 1912				  // signal at rep end
#define MT_EXEC_SCORE 1913			  // success/failure
#define MT_FLIP_THAT_BUCKET_DATA 1914 // communicate stimulus updates and participant responses within the Flip That Bucket game

#define MT_EM_ADAPT_NOW 2000
#define MT_EM_CONFIGURATION 2001
#define MT_TDMS_CREATE 2002
#define MT_RF_REPORT 2003
#define MT_PICDISPLAY 2004
#define MT_STIMDATA 2005
//#define MT_KNOB_FEEDBACK 		  2006
#define MT_SEAIO_OUT 2007
#define MT_ATIforcesensor 2008
#define MT_TACTOR_CMD 2009 // signal to trigger vibrotactor(s)
#define MT_HSTLOG 3000
//#define MT_TFD					  3001 //Time-Frequency Data for visualization (so that processing can still be done in Extraction Module)

#define MT_PLAYSOUND 3100
#define MT_PLAYVIDEO 3102
#define MT_START_TIMED_RECORDING 3101

#define MT_AJA_CONFIG 3200
#define MT_AJA_TIMECODE 3201
#define MT_AJA_STATUS 3202
#define MT_AJA_STATUS_REQUEST 3203

// FLIGHT SIM
//#define MT_APLC			 	  3500

// stim message IDs
#define MT_CERESTIM_CONFIG_MODULE 4000
#define MT_CERESTIM_CONFIG_CHAN_PRESAFETY 4001
#define MT_CERESTIM_CONFIG_CHAN 4002
#define MT_CERESTIM_ERROR 4003
#define MT_CERESTIM_ALIVE 4004
#define MT_CS_TRAIN_END 4005							 // sent when an (open-loop) pulse-train has ended
#define MT_CERESTIM_CONFIG_CHAN_PRESAFETY_ARBITRARY 4006 //NEW MESSAGE TYPE FOR ARBITRARY PULSE TIMINGS
#define MT_CERESTIM_CONFIG_CHAN_ARBITRARY 4007			 //NEW MESSAGE TYPE FOR ARBITRARY PULSE TIMINGS
#define MT_CS_ARBITRARY_CLOSE 4008						 //for closing arbitrary pulse timings when config is wrong
#define MT_STIM_VOLTAGE_MONITOR_DATA 4009
#define MT_STIM_VOLTAGE_MONITOR_DIGITAL_DATA 4010
#define MT_VOLTAGE_MONITOR_STATUS 4011
#define MT_STIM_DUTYCYCLE_TIME 4012
#define	MT_STIM_TRIAL_DURATION 4013

// stim touch interface IDs
// USER RESPONSES:  ACN 2/10
// quality
#define MT_NATURAL_RESPONSE 4050
#define MT_DEPTH_RESPONSE 4051
#define MT_PAIN_RESPONSE 4052
// modality
#define MT_MODALITY_TOGGLE 4053
#define MT_MECH_RESPONSE 4054
#define MT_MECH_INTENSITY_RESPONSE 4055
#define MT_MOVE_RESPONSE 4056
#define MT_MOVE_INTENSITY_RESPONSE 4057
#define MT_TINGLE_RESPONSE 4058
#define MT_TINGLE_INTENSITY_RESPONSE 4059
#define MT_TEMP_RESPONSE 4060
#define MT_DIR_PIXEL_COORDS 4061
#define MT_PIXEL_COORDS 4063  // canvas drawing
#define MT_CLEAR_LINE 4064	  // clear current sensation
#define MT_ADD_SENSATION 4065 // add sensation
#define MT_SLIDER_DATA 4066	  //From palette sliders

// realtime control of stimulation parameters
#define MT_USER_DEFINED_STIM 4067
#define MT_USER_BEHAVIOUR 4068
#define MT_STOP_STIM 4069
#define MT_PAUSE_TRIAL 4070

// misc messages IDs
#define MT_CST_LAMBDA 4100 // message to log lambda value in cst task
#define MT_CST_SETTINGS 4101

//  toolbox IDs
#define MT_STIM_PRES_CONFIG 4150
#define MT_STIM_PRES_PHASE_END 4151
#define MT_STIM_PRESENT 4152
#define MT_STIM_PRES_STATUS 4153
#define MT_STIM_CONFIG_TYPE 4154

//Deka SC Arm Messages
#define MT_DEKA_ACI_RESPONSE 4200
#define MT_DEKA_SENSOR 4201
#define MT_DEKA_CAN_TOGGLE 4202
#define MT_DEKA_CAN_GRIP_TOGGLE 4203
#define MT_DEKA_CAN_EXIT 4204
//Deka Luke Hand Messages
#define MT_DEKA_HAND_SENSOR 4205
#define MT_DEKA_HAND_JSTICK_CMD 4206
//Right Hand Robotics Messages
#define MT_RH_GRIPPER_SENSOR 4207
//KUKA Messages
#define MT_KUKA_JOINT_COMMAND			4208
#define MT_KUKA_FEEDBACK				4209
#define MT_KUKA_EXIT                    4210
#define MT_KUKA_PTP_JOINT				4211
#define MT_KUKA_DEBUG					4212
// Taska
#define MT_TASKA_CMD					4250
#define MT_TASKA_REPLY					4251
#define MT_TASKA_ERROR					4252

// MujocoVR C++ Messages
// moved to mjvr_types.h
// MT 4213-4232 in use (as of 2020-06-08)

//Mechanical Indenter Messages
#define MT_MECH_STIM_CONFIGURE 4240
#define MT_MECH_STIM_RESET 4241
#define MT_MECH_STIM_STAGE 4242
#define MT_MECH_STIM_WAITING 4243
#define MT_MECH_STIM_TRIGGER 4244
#define MT_MECH_STIM_CANCEL 4245
#define MT_MECH_STIM_DONE 4246
#define MT_MECH_STIM_ERROR 4247

#define DEKA_DOF_COUNT 7
#define KUKA_DOF_COUNT 7

#define TAG_LENGTH 64

// Possible ways for us to control the MPL
// i.e. modes of the GROBOT_COMMAND Message
// They all begin with MPL_AT_ which stands for MPL Actuation Type
#define MPL_AT_ARM_EPV_FING_JV 0
#define MPL_AT_ARM_EPV_FING_JP 1
#define MPL_AT_ARM_JV_FING_JP 2
#define MPL_AT_ALL_JV 3
#define MPL_AT_ALL_JP 4
#define MPL_AT_ARM_EPP_FING_JP 5

// Time Freq Decomposition parameters:
#define TFD_FREQ_BINS 20

//
// MDF DEFINTIONS AND OTHER TYPEDEFS
//
typedef struct
{
	int serial_no;
	int sub_sample;
} MSG_HEADER;

typedef struct
{
	int session_num;
	int set_num;
	int block_num;
	int trial_num;
	char session_type[128]; // character fields must be at bottom to avoid issues reading in Python
	char subject_id[64];
} MDF_TRIAL_METADATA; // sent at start of trial

typedef struct
{
	int rep_num;
	int reserved;
} MDF_REP_START; // sent at start of rep

typedef struct
{
	char filename[256];
} MDF_PLAYSOUND;

typedef struct
{
	char filename[256];
} MDF_PLAYVIDEO;

typedef struct
{
	double start_command;
} MDF_START_TIMED_RECORDING;

typedef struct
{
	char state_name[128];
	double target[MAX_COMMAND_DIMS];
	double active_assist_weight[NUM_DOMAINS]; //3 "domains": {x,y,z} {rotation} {hand}
	double brain_control_weight[NUM_DOMAINS];
	double passive_assist_weight[NUM_DOMAINS];
	double jstick_control_weight[NUM_DOMAINS];
	double gain[NUM_DOMAINS];
	double threshold[NUM_DOMAINS];
	double force_targ[MAX_GRIP_DIMS];
	double dZ_gain; // gain on change in impedance
	double force_thresh;
	int active_override[MAX_COMMAND_DIMS]; // dimensions to override with 100% auto/0% BC
	int use_for_calib;
	int result_code;
	int stim_enable;
	int force_calib; // whether or not to calibrate on force
	int targ_set;	 // target set number
	int targ_idx;	 // index within target set
	short gripperControlMask[4];
} MDF_TASK_STATE_CONFIG;

typedef struct
{ //Just like a TASK_STATE_CONFIG but to be sent at the end of a state/phase of a trial to capture waypoints and more detail about results
	char state_name[128];
	double target[MAX_COMMAND_DIMS];
	double active_assist_weight[NUM_DOMAINS]; //3 "domains": {x,y,z} {rotation} {hand}
	double brain_control_weight[NUM_DOMAINS];
	double passive_assist_weight[NUM_DOMAINS];
	double jstick_control_weight[NUM_DOMAINS];
	double gain[NUM_DOMAINS];
	double threshold[NUM_DOMAINS];
	double force_targ[MAX_GRIP_DIMS];
	double dZ_gain; // gain on change in impedance
	double force_thresh;
	int active_override[MAX_COMMAND_DIMS]; // dimensions to override with 100% auto/0% BC
	int use_for_calib;
	int result_code;
	int stim_enable;
	int force_calib; // whether or not to calibrate on force
	int targ_set;	 // target set number
	int targ_idx;	 // index within target set
	short gripperControlMask[4];
} MDF_PHASE_RESULT;

typedef struct
{
	int passed;
	int failed;
} MDF_EXEC_SCORE;

typedef struct
{
	char state_name[128];
	double state_value;
} MDF_FLIP_THAT_BUCKET_DATA;

typedef struct
{
	char filename[256];
	double timer;
} MDF_PICDISPLAY;

typedef struct
{
	double ConfigID[12];
	double Vmax[12];
	double Vmin[12];
	double interphase[12];
} MDF_STIMDATA;

typedef struct
{
	char pathname[MAX_LOGGER_FILENAME_LENGTH]; //MAX_LOGGER_FILENAME_LENGTH = 256, defined in RTMA_types.h (also used by SAVE_MESSAGE_LOG)
	int pathname_length;
	int reserved;
} MDF_TDMS_CREATE;

typedef struct
{
	int sample_rate;							   //[Hz] DAQ sample rate for digital and analog data
	int pulse_count;							   //Number of analog pulses in this message
	int daq_channel[NUM_SPIKES_PER_STIM_MSG];	   // From the DAQ, 1-12
	int array_channel[NUM_SPIKES_PER_STIM_MSG];	   // From the headstage array, 1-64. CAUTION: This value is calcuated and may not be correct
	double daq_timestamp[NUM_SPIKES_PER_STIM_MSG]; // [seconds] DAQ timestamp of the start of spike voltage data
	float voltage[NUM_SPIKES_PER_STIM_MSG * 100];  // [volts] 1 ms of voltage data, starting at time daq_timestamp
	float interphase[NUM_SPIKES_PER_STIM_MSG];	   // [volts] Voltage at the interphase time after the first rise of the data. Interphase time is defined by CERESTIM_CONFIG_MODULE.
	float Vmax[NUM_SPIKES_PER_STIM_MSG];		   // [volts]
	float Vmin[NUM_SPIKES_PER_STIM_MSG];		   // [volts]
} MDF_STIM_VOLTAGE_MONITOR_DATA;

typedef struct
{
	float stim_sync_event[30]; //[seconds] DAQ timestamps when digital input became high
	float stim_param_event[5]; //[seconds] DAQ timestamps when digital input became high
	double spm_daq_delta_t;	   //[seconds] Differnce in clock time between SPM and DAQ, calcuated using the stim param/update event
} MDF_STIM_VOLTAGE_MONITOR_DIGITAL_DATA;

typedef struct
{
	int msg_length;
	char msg[1024];
} MDF_VOLTAGE_MONITOR_STATUS;

typedef struct
{
	double dutycycle_time;
}	MDF_STIM_DUTYCYCLE_TIME;

typedef struct
{
	double trial_duration;
}	MDF_STIM_TRIAL_DURATION;

typedef struct
{
	MSG_HEADER header;
	//int FTsequence[2];
	//char Funits[128];
	//char Tunits[128];
	double Fx;
	double Fy;
	double Fz;
	double Tz;
	double Tx;
	double Ty;
} MDF_ATIforcesensor;

/*typedef struct {
	double ardpos[256]; //Buffer size
	double A;
	double B;
	double C;
} MDF_KNOB_FEEDBACK;*/

typedef struct
{
	int bit;
	int value;
} MDF_SEAIO_OUT;

/*typedef struct {
	MSG_HEADER header;
	double TF[TFD_FREQ_BINS*MAX_SPIKE_SOURCES*MAX_SPIKE_CHANS_PER_SOURCE];
	double freq[TFD_FREQ_BINS];
} MDF_TFD; */

typedef struct
{
	int len;
	int reserved;
	char log[512];
} MDF_HSTLOG;

typedef struct
{
	int type; //0 -> filename
	int reserved;
	char data[256];
} MDF_EM_CONFIGURATION;

typedef struct
{
	int src;
	char decoder_type[128];
	char decoder_loc[256];
} MDF_EXTRACTION_RESPONSE;

typedef struct
{
	int unit_idx;
	int enabled;
} MDF_UPDATE_UNIT_STATE;

typedef struct
{
	MSG_HEADER header;
	unsigned char disabled_units[MAX_TOTAL_SPIKE_CHANS];
} MDF_DISABLED_UNITS;

typedef struct
{
	MSG_HEADER header;
	double command[MAX_COMMAND_DIMS];
	double dZ[MAX_GRIP_DIMS]; // decoded change in impedance
	int src;
	int reserved;
} MDF_CONTROL_SPACE_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double command[MAX_COMMAND_DIMS];
	double dZ[MAX_GRIP_DIMS]; // decoded change in impedance
	int src;
	int reserved;
} MDF_BIAS_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double stiffness[MPL_RAW_PERCEPT_DIMS];
	int src;
	int reserved;
} MDF_IMPEDANCE_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double command[MAX_COMMAND_DIMS];
	int src;
	int reserved;
} MDF_CONTROL_SPACE_POS_COMMAND; // for use w/ MPL_POS_CONTROL

typedef struct
{
	MSG_HEADER header;
	double command[MAX_COMMAND_DIMS];
	double stiffness[MPL_RAW_PERCEPT_DIMS];
	int src;
	int reserved;
} MDF_FINISHED_COMMAND;

typedef struct
{
	short proceed; // boolean [0 or 1]
	short fail;	   // boolean [0 or 1]
	int reserved;  // for 64-bit alignment
} MDF_EXECUTIVE_CTRL;

typedef struct
{
	MSG_HEADER header;
	double position[MAX_COMMAND_DIMS];
	double velocity[MAX_COMMAND_DIMS];
	//  double force[MAX_COMMAND_DIMS];
} MDF_CONTROL_SPACE_FEEDBACK;

typedef struct
{
	MSG_HEADER header;
	double position[MPL_RAW_PERCEPT_DIMS];
	double velocity[MPL_RAW_PERCEPT_DIMS];
	double torque[MPL_RAW_PERCEPT_DIMS];
	double temperature[MPL_RAW_PERCEPT_DIMS];
} MDF_MPL_RAW_PERCEPT;

typedef struct
{
	MSG_HEADER header;
	double ind_force[14];
	double mid_force[14];
	double rng_force[14];
	double lit_force[14];
	double thb_force[14];

	double ind_accel[3];
	double mid_accel[3];
	double rng_accel[3];
	double lit_accel[3];
	double thb_accel[3];

	short contacts[16]; // [II,IP,MI,MP,RI,RP,P1,P2,P3,P4]

} MDF_MPL_SEGMENT_PERCEPTS;

typedef struct
{
	MSG_HEADER header;
	double torque[MPL_RAW_PERCEPT_DIMS];
	double ind_force[14];
	double mid_force[14];
	double rng_force[14];
	double lit_force[14];
	double thb_force[14];
	short contacts[16]; // [II,IP,MI,MP,RI,RP,P1,P2,P3,P4]
} MDF_MPL_REBIASED_SENSORDATA;

typedef struct
{
	MSG_HEADER header;
	double torque[MPL_RAW_PERCEPT_DIMS];
	double ind_force[14];
	double mid_force[14];
	double rng_force[14];
	double lit_force[14];
	double thb_force[14];
	short contacts[16]; // [II,IP,MI,MP,RI,RP,P1,P2,P3,P4]
} MDF_CURSOR_FEEDBACK;

typedef struct
{
	short grating_visibility; // [No:-1 or Yes:1]
	short stimulation_on;	  // [No:-1 or Yes:1]
	short trial_set;
	short presentation;	   // [1 or 2]
	short increment_block; // boolean [0 or 1]
	short wait_response;   // boolean [0 or 1]
	short reserved;		   // for 64-bit alignment
} MDF_VISUAL_GRATING_BUILD;

typedef struct
{
	short channel;
	short session_num;
	short set_num;
	short block_num;
	short trial_num;
	short block_ID;
	short DELTA_reference_frequency;
	float ICMS_reference_frequency;
	float ICMS_reference_amplitude;
	float ICMS_frequency_1;
	float ICMS_frequency_2;
	float ICMS_amplitude_1;
	float ICMS_amplitude_2;
	float VIS_reference_frequency;
	float VIS_reference_amplitude;
	float VIS_frequency_1;
	float VIS_frequency_2;
	float VIS_amplitude_1;
	float VIS_amplitude_2;
	short response; // 64-bit aligned
} MDF_VISUAL_GRATING_RESPONSE;

typedef struct
{
	double position[7];
	double velocity[7];
} MDF_WAM_FEEDBACK;

typedef struct
{
	int source_index;		 // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	int num_chans_enabled;	 // number of channels enabled (expected 128)
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	short data[LFPSAMPLES_PER_HEARTBEAT * MAX_SPIKE_CHANS_PER_SOURCE];
} MDF_RAW_CTSDATA;

typedef struct
{
	int source_index;		 // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	int num_chans_enabled;	 // number of channels enabled (expected 256)
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	short data[LFPSAMPLES_PER_HEARTBEAT * MAX_SPIKE_CHANS_PER_SOURCE_N256];
} MDF_RAW_CTSDATA_N256;

typedef struct
{
	int source_index;		 // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	int num_chans_enabled;	 // number of channels enabled (expected 16)
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	short data[ANALOGSAMPLES_PER_HEARTBEAT * MAX_ANALOG_CHANS];
} MDF_RAW_ANALOGDATA;

typedef struct
{
	MSG_HEADER header;
	double source_timestamp[MAX_SPIKE_SOURCES]; // [seconds]source timestamp of the event that caused this count to happen
	short data[RAW_COUNTS_PER_SAMPLE * LFPSAMPLES_PER_HEARTBEAT * MAX_SPIKE_SOURCES * MAX_SPIKE_CHANS_PER_SOURCE];
} MDF_SPM_CTSDATA;

typedef struct
{
	MSG_HEADER header;
	double source_timestamp[MAX_SPIKE_SOURCES]; // [seconds]source timestamp of the event that caused this count to happen
	short data[RAW_COUNTS_PER_SAMPLE * LFPSAMPLES_PER_HEARTBEAT * MAX_SPIKE_SOURCES * MAX_ANALOG_CHANS];
} MDF_SPM_ANALOGDATA;

typedef struct
{
	int source_index;		 // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	int reserved;			 // for 64-bit alignment
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	double count_interval;	 // [seconds]time interval over which this count was integrated
	unsigned char counts[MAX_TOTAL_SPIKE_CHANS_PER_SOURCE];
} MDF_RAW_SPIKECOUNT;

typedef struct
{
	int source_index;		 // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	int reserved;			 // for 64-bit alignment
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	double count_interval;	 // [seconds]time interval over which this count was integrated
	unsigned char counts[MAX_TOTAL_SPIKE_CHANS_PER_SOURCE_N256];
} MDF_RAW_SPIKECOUNT_N256;

typedef unsigned char SPIKE_COUNT_DATA_TYPE;
typedef struct
{
	MSG_HEADER header;
	double source_timestamp[MAX_SPIKE_SOURCES]; // [seconds] source timestamp of the event that caused this count to happen
	double count_interval;						// [seconds]
	SPIKE_COUNT_DATA_TYPE counts[MAX_TOTAL_SPIKE_CHANS];
} MDF_SPM_SPIKECOUNT;

typedef struct
{
	int source_index; // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	short channel;
	unsigned char unit;
	unsigned char reserved1; //64-bit alignment
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	double fPattern[3];
	short nPeak;
	short nValley;
	int reserved2;
	short snippet[SAMPLES_PER_SNIPPET];
} SPIKE_SNIPPET;

typedef struct
{
	SPIKE_SNIPPET ss[SNIPPETS_PER_MESSAGE];
} MDF_SPIKE_SNIPPET; //contains SNIPPETS_PER_MESSAGE spikes worth of data to reduce message load

typedef struct
{
	int source_index; // a zero-based index in the range 0..(N-1) for N spike sources (e.g. separate acquisition boxes)
	short channel;
	unsigned char unit;
	unsigned char reserved1; //64-bit alignment
	double source_timestamp; // [seconds]source timestamp of the event that caused this count to happen
	double fPattern[3];
	short nPeak;
	short nValley;
	int rejectType; // 1 for blanking window (primary artifact), 2 for secondary artifact
	short snippet[SAMPLES_PER_SNIPPET];
} REJECTED_SNIPPET;

typedef struct
{
	REJECTED_SNIPPET rs[SNIPPETS_PER_MESSAGE];
} MDF_REJECTED_SNIPPET;

typedef struct
{
	int source_index;
	int channel;
	double source_timestamp;
	unsigned int data[2];
} MDF_RAW_DIGITAL_EVENT;

typedef struct
{
	MSG_HEADER header;
	int source_index[MAX_DIG_PER_SAMPLE];
	double source_timestamp[MAX_SPIKE_SOURCES];
	unsigned short byte0[MAX_DIG_PER_SAMPLE];
	unsigned short byte1[MAX_DIG_PER_SAMPLE];
	int num_events;
	int reserved;
} MDF_SPM_DIGITAL_EVENT;

typedef struct
{
	int source_index; //0 for NSP 1, 1 for NSP 2, 3 for CereStim module
	int channel;
	double source_timestamp; //NSP timestamp, s
	unsigned int data;
	int reserved;
} MDF_STIM_SYNC_EVENT; // special type of digital event

typedef struct
{
	int source_index; //0 for NSP 1, 1 for NSP 2
	int channel;
	double source_timestamp; //NSP timestamp, s
	unsigned int data;
	int reserved;
} MDF_STIM_UPDATE_EVENT; // special type of digital event

typedef struct
{
	char pathname[MAX_LOGGER_FILENAME_LENGTH];		//MAX_LOGGER_FILENAME_LENGTH = 256, defined in RTMA_types.h (also used by SAVE_MESSAGE_LOG)
	char subjectID[MAX_LOGGER_FILENAME_LENGTH / 2]; // 128
	unsigned record;								// 1 start, 0 stop
	unsigned reserved;
} MDF_CENTRALRECORD;

typedef struct
{
	MSG_HEADER header;
	char tag[TAG_LENGTH];
	double dof_vals[MAX_COMMAND_DIMS];
} MDF_INPUT_DOF_DATA;

typedef struct
{
	MSG_HEADER header;
	char tag[TAG_LENGTH];
	double raw_vals[MAX_DATAGLOVE_SENSORS];
	double calib_vals[MAX_DATAGLOVE_SENSORS];
	int gesture;
	int glovetype;
	int hand;
	int reserved;
} MDF_DATAGLOVE;

typedef struct
{
	MSG_HEADER header;
	int type;
	int channel;
	int value;
	int time;
} MDF_SLIDER_DATA;

typedef struct
{
	int frequency;
	int amplitude[3];
	int channel[3];
} MDF_USER_DEFINED_STIM; // allow user to set stimulation parameters via tablet interface

typedef struct
{
	int current_trial;
	char current_screen[256];
	char current_object[256];
	int left_canvas[2];
	int right_canvas[2];
	int frequency;
	int freq_choice;
	int bio;
	int drag;
	int amplitude[3];
	int satisfaction;
	int certainty;
	char chosen_object[256];
	int object_quest[6];
	int affective_quest[5];
} MDF_USER_BEHAVIOUR; // keep track of user behavior in interface

typedef struct
{
	int stop_stim;
} MDF_STOP_STIM; // stop stimulation externally

typedef struct
{
	int pause_trial;
} MDF_PAUSE_TRIAL; // stop stimulation externally

// STIMULATION TYPE DEFS
typedef struct
{
	int configID[MAX_CS_CONFIGS];  // equates to pattern in config_chan, MAX_CS_CONFIGS = 16
	int amp1[MAX_CS_CONFIGS];	   //unsigned char required by API, current amplitude in uA
	int amp2[MAX_CS_CONFIGS];	   //unsigned char required by API, current amplitude in uA
	int frequency[MAX_CS_CONFIGS]; //unsigned short required by API, Hz
	int num_modules;			   // more accurately, number of configurations (up to 16)
	int afcf;
	int width1;		//unsigned short required by API, us
	int width2;		//unsigned short required by API, us
	int interphase; //unsigned short required by API, us
} MDF_CERESTIM_CONFIG_MODULE;

typedef struct
{
	MSG_HEADER header;
	int stop;
	int numChans;					// Nuber of channels stimulated, up to 12
	int channel[MAX_STIM_CHANS_ON]; // Array channel stimulated, MAX_STIM_CHANS_ON = 12
	int pattern[MAX_STIM_CHANS_ON]; // corresponds to configID in config_module
	int reps;						// usage: play(reps) - 0 for indefinite (loop)
	float pause_t;					// usage: (milliseconds) how quickly the subsequent stimulus in the buffer is used (set to 0 if only one stimulation)
} MDF_CERESTIM_CONFIG_CHAN;

//changed these to be identical to config chan because we are now loading separate config file
typedef struct
{
	MSG_HEADER header;
	//int stop;
	//int numChans; // up to 12
	//int channel[MAX_STIM_CHANS_ON]; // MAX_STIM_CHANS_ON = 12
	//int pattern[MAX_STIM_CHANS_ON]; // corresponds to configID in config_module
	//int reps; // usage: play(reps). 0 for indefinite (loop)
	//int reserved;
	int stop;
	char pathname[MAX_LOGGER_FILENAME_LENGTH];
	int pathlength;
	int pulselength;
} MDF_CERESTIM_CONFIG_CHAN_ARBITRARY;

typedef struct
{
	MSG_HEADER header;
	int stop;
	int numChans;				 // requested (before limit by safety_mod), up to 64
	int channel[NUM_STIM_CHANS]; // NUM_STIM_CHANS = 64
	int pattern[NUM_STIM_CHANS]; // corresponds to configID in config_module
	int reps;					 // usage: play(reps). 0 for indefinite (loop)
	float pause_t;				 // usage: (milliseconds) how quickly the subsequent stimulus in the buffer is used (set to 0 if only one stimulation)
} MDF_CERESTIM_CONFIG_CHAN_PRESAFETY;

typedef struct
{
	MSG_HEADER header;
	int stop;
	int numChans;				 // requested (before limit by safety_mod), up to 64
	int channel[NUM_STIM_CHANS]; // NUM_STIM_CHANS = 64
	int pattern[NUM_STIM_CHANS]; // corresponds to configID in config_module
	int reps;					 // usage: play(reps). 0 for indefinite (loop)
	int reserved;
	char pathname[MAX_LOGGER_FILENAME_LENGTH];
	int pathlength;
} MDF_CERESTIM_CONFIG_CHAN_PRESAFETY_ARBITRARY; //may want to make this more unique to arbitrary pulse stuff

typedef struct
{
	int error;
	int config; // used for configuration error
		//char error[128];
} MDF_CERESTIM_ERROR;
// END STIMULATION TYPE DEFS

typedef struct
{
	char handp[48];
	char handd[18];
	char head[13];
	char arms[20];
	int tag;
	int flipframe;
} MDF_RF_REPORT;

typedef struct
{
	int record;
	int stop;
	char filename[256];
} MDF_AJA_CONFIG;

typedef struct
{
	MSG_HEADER header;
	char timecode[128];
} MDF_AJA_TIMECODE;

typedef struct
{
	int status;
	int reserved;
	char clipname[256];
} MDF_AJA_STATUS;

typedef struct
{
	MSG_HEADER header;
	double factor; // Normalization Factor applied to this message
	double length; // length of window used to calculate normalization
} MDF_NORMALIZATION_FACTOR;

typedef struct
{
	MSG_HEADER header;
	float lambda;
	int k;
	double cursor_pos; // if discretized, different than control_space_feedback
} MDF_CST_LAMBDA;

typedef struct
{
	double sweep_rate; // 0 for static
	int vis_bins;	   // number of bins for vision
	int stim_bins;	   // number of bins for stim
} MDF_CST_SETTINGS;

// for open-loop stim touch interface
// USER RESPONSES
typedef struct
{
	float a;
	int reserved;
} MDF_NATURAL_RESPONSE;

// if indexing takes too long, just send the string of the response
typedef struct
{
	int idx;
	int reserved;
} MDF_DEPTH_RESPONSE;

typedef struct
{
	float a;
	int reserved;
} MDF_PAIN_RESPONSE;

typedef struct
{
	signed int a;
	int reserved;
} MDF_MODALITY_TOGGLE;

typedef struct
{
	int idx;
	int reserved;
} MDF_MECH_RESPONSE;

typedef struct
{
	float a;
	int reserved;
} MDF_MECH_INTENSITY_RESPONSE;

typedef struct
{
	float a;
	int reserved;
} MDF_MOVE_INTENSITY_RESPONSE;

typedef struct
{
	float a;
	int reserved;
} MDF_TINGLE_INTENSITY_RESPONSE;

typedef struct
{
	int idx;
	int reserved;
} MDF_MOVE_RESPONSE;

typedef struct
{
	char img[32];
	int moreMsgs;
	int reserved;
	float pixels[64];
} MDF_DIR_PIXEL_COORDS;

typedef struct
{
	int idx;
	int reserved;
} MDF_TINGLE_RESPONSE;

typedef struct
{
	float a;
	int reserved;
} MDF_TEMP_RESPONSE;

typedef struct
{
	char img[32];
	int moreMsgs;
	int reserved;
	float pixels[64];
} MDF_PIXEL_COORDS;

// FLIGHT SIM
/*typedef struct{
	int runindex;
	int serial_no;
	int hour;
	int minute;
	int second;
} MDF_APLC; */

// PSYCHTOOLBOX DEFINITIONS
typedef struct
{
	char filename[256];
	int randomization;
} MDF_STIM_PRES_CONFIG;

typedef struct
{
	char stim_filename[256];
	char stim_state_name[256];
	double stim_display_time;
	double stim_start_delay;
} MDF_STIM_PRESENT;

typedef struct
{
	int phase_rep_end;
} MDF_STIM_PRES_PHASE_END;

typedef struct
{
	int pause_resume;
	int stop;
} MDF_STIM_PRES_STATUS;

typedef struct
{
	char stim_configtype[128];
} MDF_STIM_CONFIG_TYPE;

// 1d gripper
typedef struct
{
	MSG_HEADER header;
	double grip_pos[MAX_GRIPPER_DIMS];
	double velocity[MAX_GRIPPER_DIMS];
	double force[MAX_GRIPPER_DIMS];
	double impedance[MAX_GRIPPER_DIMS];
	short controlMask[4];
	int src;
	int reserved;
} MDF_GRIP_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double grip_pos[MAX_GRIPPER_DIMS];
	double velocity[MAX_GRIPPER_DIMS];
	double force[MAX_GRIPPER_DIMS];
	double impedance[MAX_GRIPPER_DIMS];
	short controlMask[4];
	char effector[64];
} MDF_GRIP_FINISHED_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double grip_pos[MAX_GRIPPER_DIMS];
	double velocity[MAX_GRIPPER_DIMS];
	double force[MAX_GRIPPER_FORCES];
	char effector[64];
} MDF_GRIPPER_FEEDBACK;

typedef struct
{
	MSG_HEADER header;
	double motor_pos[MJ_VR_MAX_MOTOR_COUNT];
	double motor_vel[MJ_VR_MAX_MOTOR_COUNT];
	double motor_torque[MJ_VR_MAX_MOTOR_COUNT];
	double joint_pos[MJ_VR_MAX_JOINT_COUNT];
	double joint_vel[MJ_VR_MAX_JOINT_COUNT];
	double contact[MJ_VR_MAX_CONTACT_COUNT];
} MDF_MUJOCO_SENSOR;

typedef struct
{
	MSG_HEADER header;
	double ref_pos[MJ_MAX_MOTOR];
	double ref_vel[MJ_MAX_MOTOR];
	double gain_pos[MJ_MAX_MOTOR];
	double gain_vel[MJ_MAX_MOTOR];
	short ref_pos_enabled;
	short ref_vel_enabled;
	short gain_pos_enabled;
	short gain_vel_enabled;
} MDF_MUJOCO_CMD;

#define MUJOCO_LINK_ID 1000 // if mocap_id (below) is set to this, read link_objects field, otherwise read/apply position normally
typedef struct
{
	unsigned int mocap_id;	   // mocap id associated with object (order in model file)
	unsigned int link_objects; //flag to link or unlink objects (such that they all move together), this is read only if mocap_id is set to MUJOCO_LINK_ID
	double pos[3];
} MDF_MUJOCO_MOVE;

typedef struct
{
	unsigned int obj_id; // mocap id associated with object (order in model file)
	double pos[3];
	double orientation[3];
} MDF_MUJOCO_OBJMOVE;

typedef struct
{
	char message[256]; // mujoco message text
	int position;	   // 0: top right, 1: top left, 2: bottom right, 3: bottom left
} MDF_MUJOCO_MSG;

typedef struct
{
	double color_id; // color_id: 0 (invisible), 1 (red), 2 (green), 3 (yellow)
} MDF_MUJOCO_GHOST_COLOR;

typedef struct
{
	MSG_HEADER header;
	unsigned short motor_sp[2];	 // motor set points
	unsigned short reserved1[2]; // 64-bit balancing
	unsigned char mode;			 // control mode {'Pos' 'Vel' 'Force' 'VelForce' 'SensReq'}
	unsigned char reserved2[3];	 // 64-bit balancing
} MDF_OPENHAND_CMD;

typedef struct
{
	MSG_HEADER header;
	unsigned short motor_pos;
	unsigned short force;
} MDF_OPENHAND_SENS;

typedef struct
{
	MSG_HEADER header;
	int ID;
	int reserved;
	double pos[3];	  //x,y,z
	double orient[3]; //roll,pitch,yaw
	double timestamp; // [seconds] source timestamp of the event that caused this count to happen
	char name[128];
} MDF_OPTITRACK_RIGID_BODY;

typedef struct
{
	MSG_HEADER header;
	int raw_analog[3];
	double force[3];
} MDF_SINGLETACT_DATA;

typedef struct
{
	unsigned int can_id;   //Deka Can Message ID
	unsigned char data[8]; //8 Byte data field in deka Can Message
	int padding;

} DEKA_CAN_MSG;

typedef struct
{
	MSG_HEADER header;
	DEKA_CAN_MSG ACI_1; //ACI 1, MessageID 0x210
	DEKA_CAN_MSG ACI_2; //ACI_2, MessageID 0x211
	DEKA_CAN_MSG ACI_3; //ACI_3, MessageID 0x212
} MDF_DEKA_ACI_RESPONSE;

typedef struct
{
	MSG_HEADER header;				  //Message header with serial no. and sub serial no.
	DEKA_CAN_MSG position_msg_1;	  //Shoulder/Elbow, MessageID 0x4AA
	DEKA_CAN_MSG position_msg_2;	  //Wrist/Hand, MessageID 0x4AC
	double motor_pos[DEKA_DOF_COUNT]; //Decoded motor position in degrees {'WristRot','WristFE', 'Hand,'ShoulderAbAd','ShoulderFE', 'HumeralRot','Elbow'}
	double motor_current[DEKA_DOF_COUNT];
	int mode; //Standby = 0, Arm = 1;
	int sync; //Flag to indicate whether all sensor data came from same 0x080 sync period
	int grip; //Current Grip Number Selected
	int padding;
} MDF_DEKA_SENSOR;

typedef struct
{
	int toggle;
	int padding;
} MDF_DEKA_CAN_TOGGLE;

typedef struct
{
	int toggle; //Up = 1 Down = 0;
	int padding;
} MDF_DEKA_CAN_GRIP_TOGGLE;

typedef struct
{
	int exit;
	int padding;
} MDF_DEKA_CAN_EXIT;

typedef struct
{
	MSG_HEADER header;
	double joint_dest[KUKA_DOF_COUNT];
	int err_move_mode;
	int err_input_cap[6];	  //6 translation/rotation DOF
	int err_cart_wall_eef[6]; //6 translation/rotation DOF, End-effector (EEF)
	int err_cart_wall_arm[6]; //6 translation/rotation DOF, Wrist/Elbow
	int err_jpos_stop[3];
} MDF_KUKA_JOINT_COMMAND;

typedef struct
{
	MSG_HEADER header;
	double time;					  //seconds
	double joint_pos[KUKA_DOF_COUNT]; //radians
	double cart_pos[3];				  //meters
	double cart_angle[3];			  //radians
	double cart_pos_vel[3];			  //m/s
	double cart_rot_vel[3];			  //rad/s
	double cart_force[3];			  //Newtons
	double cart_torque[3];			  //N*m
	double dest_delta_t;			  //nanoseconds
	int mode;						  //Movement mode
	int reserved;
} MDF_KUKA_FEEDBACK;

typedef struct
{
	int exit;
	int padding;
} MDF_KUKA_EXIT;

typedef struct
{
	double joint_pos[KUKA_DOF_COUNT]; //radians
} MDF_KUKA_PTP_JOINT;

typedef struct
{
	double joint_pos[KUKA_DOF_COUNT]; //radians
} MDF_KUKA_DEBUG;

// Grapevine Xipp messages

typedef struct
{
	MSG_HEADER header; // message header
	int num_chans_per_headstage[MAX_XIPP_EEG_HEADSTAGES];
	unsigned int source_timestamp[XIPP_SAMPLES_PER_MSG]; // array of grapevine timestamps for each data point
	float data[XIPP_SAMPLES_PER_MSG * MAX_XIPP_CHANS];	 // array of 40 samples of EMG data per channel, reshaped into a vector
} MDF_XIPP_EMG_DATA_RAW;

typedef struct
{
	MSG_HEADER header;										  // message header
	unsigned long long source_timestamp[MYO_SAMPLES_PER_MSG]; // array of myo timestamps for each data point
	int data[MYO_SAMPLES_PER_MSG * MAX_MYO_EMG_CHANS];		  // array of 4 samples of EMG data per channel, reshaped into a vector
} MDF_MYO_EMG_DATA;

typedef struct
{
	MSG_HEADER header;					 // message header
	unsigned long long source_timestamp; // array of myo timestamps for each data point
	float orientation[4];
	float gyroscope[3];
	float acceleration[3];
} MDF_MYO_KIN_DATA;

typedef struct
{
	MSG_HEADER header; // sample no in header.serial_no
	double source_timestamp;
	unsigned int xipp_timestamp; // ripple timestamp
	int reserved;
} MDF_SAMPLE_GENERATED;

#define PRENSILIA_DOF 5
#define PRENSILIA_EXT_SENSORS 7
typedef struct
{
	MSG_HEADER header;
	unsigned short stream_type;
	unsigned short current[PRENSILIA_DOF];
	unsigned short position[PRENSILIA_DOF];
	unsigned short external[PRENSILIA_EXT_SENSORS];
	unsigned short tension[PRENSILIA_DOF]; // element 0 expected to be empty
	unsigned short reserved;
} MDF_PRENSILIA_SENS;

typedef struct
{
	MSG_HEADER header;
	short mode[PRENSILIA_DOF]; // 0 pos, 1 velocity, 2 force
	short command[PRENSILIA_DOF];
} MDF_PRENSILIA_CMD;

//Haptix Deka Hand Messages
typedef struct
{
	MSG_HEADER header;							//Message header with serial no. and sub serial no.
	DEKA_CAN_MSG position_msg_1;				//Wrist/Finger Positions, MessageID 0x4AA
	DEKA_CAN_MSG position_msg_2;				//Thumb Positions, MessageID 0x4BF
	DEKA_CAN_MSG force_msg_1;					//Finger Forces, MessageID 0x241
	DEKA_CAN_MSG force_msg_2;					//Palm Forces, MessageID, 0x341
	DEKA_CAN_MSG force_msg_3;					//Thumb Forces, MessageID, 0x4C2
	double motor_pos[HX_LUKE_MOTOR_COUNT];		//Decoded motor position in degrees {'WristRot','WristFE', 'ThumbYaw','ThumbPitch','Index', 'MRP'}
	double contact[HX_DEKA_LUKE_CONTACT_COUNT]; //Decoded contact forces in Newtons. {'ProximalPalm','DistalPalm','HandDorsal','HandEdge','ThumbVolar','ThumbRadial','ThumbDorsal','ThumbUlnar',...
												//'IndexTip','IndexLateral','MiddleTip', 'RingTip','PinkyTip'};
	int mode;									//Standby = 0, Hand = 1;
	int status[HX_DEKA_LUKE_CONTACT_COUNT];		//Robot Sensor Status
	int sync;									//Flag to indicate whether all sensor data came from same 0x080 sync period
	int grip;
} MDF_DEKA_HAND_SENSOR;

typedef struct
{
	MSG_HEADER header;					 // message header with serial no.
	double ref_vel[HX_LUKE_MOTOR_COUNT]; // vector of motor velocity commands
} MDF_DEKA_HAND_JSTICK_CMD;

typedef struct
{
	float proximal_angle;
	float distal_angle;
	float pressure[NUM_SENSORS_PER_FINGER]; //Unitless
	int contact[NUM_SENSORS_PER_FINGER];
} RH_FINGER_DATA;

typedef struct
{
	float joint_angle[NUM_DYNAMIXEL]; //Radians
	float raw_angle[NUM_DYNAMIXEL];
	float velocity[NUM_DYNAMIXEL];
	float load[NUM_DYNAMIXEL]; //Unitless
	float voltage[NUM_DYNAMIXEL];
	int temperature[NUM_DYNAMIXEL]; //Celsius
} DYNAMIXEL_INFO;

typedef struct
{
	MSG_HEADER header;
	RH_FINGER_DATA finger_1;
	RH_FINGER_DATA finger_2;
	RH_FINGER_DATA finger_3;
	DYNAMIXEL_INFO motor_info;
} MDF_RH_GRIPPER_SENSOR;

typedef struct
{
	MSG_HEADER header;
	double left_plate[4];
	double left_plate_mean;
	double center_plate[4];
	double center_plate_mean;
	double right_plate[4];
	double right_plate_mean;
} MDF_TABLE_LOAD_CELLS;

// MujocoVR C++ Definitions
// moved to mjvr_types.h

// Taska
typedef struct {
	MSG_HEADER header;
	unsigned char op_code;
	unsigned char padding[7];
	unsigned char stx;
	unsigned char type;
	unsigned char sub_index;
	unsigned char length;
	unsigned char data[60];
}MDF_TASKA_CMD;

typedef struct {
	MSG_HEADER header;
	double tx_timestamp;
	double rx_timestamp;
	double comm_time;
	unsigned char op_code;
	unsigned char padding[7];
	unsigned char stx;
	unsigned char type;
	unsigned char sub_index;
	unsigned char length;
	unsigned char data[60];
}MDF_TASKA_REPLY;

typedef struct {
	MSG_HEADER header;
	int error_code;
	int reserved;
	char msg[256];
	unsigned char dump[64];
}MDF_TASKA_ERROR;
typedef struct {
	int source; // 0:Exec Panel, 1:GUI
	int length;
	char str[1024];
} MDF_MECH_STIM_CONFIGURE;

#endif // _CLIMBER_CONFIG_
