#ifndef _MUJOCOVR_TYPES_
#define _MUJOCOVR_TYPES_

#ifndef _RTMA_TYPES_H_
	#include "../../rtma/include/RTMA_types.h"
#endif //_RTMA_TYPES_H_

#define MID_MUJOCO_VR_MODULE        61 // MujocoVR C++ Module

#define MT_MUJOCO_VR_REQUEST_STATE		4213
#define MT_MUJOCO_VR_REPLY_STATE		4214
#define MT_MUJOCO_VR_MOCAP_MOVE		    4215
#define MT_MUJOCO_VR_MOTOR_MOVE		    4216
#define MT_MUJOCO_VR_REQUEST_MODEL_INFO 4217
#define MT_MUJOCO_VR_REPLY_MODEL_INFO   4218
#define MT_MUJOCO_VR_REQUEST_LINK_STATE 4219
#define MT_MUJOCO_VR_REPLY_LINK_STATE	4220
#define MT_MUJOCO_VR_LINK				4221
#define MT_MUJOCO_VR_LINK_RESET			4222
#define MT_MUJOCO_VR_FLOATBODY_MOVE		4223
#define MT_MUJOCO_VR_RESET				4224
#define MT_MUJOCO_VR_RELOAD				4225
#define MT_MUJOCO_VR_LOAD_MODEL			4226
#define MT_MUJOCO_VR_PAUSE				4227
#define MT_MUJOCO_VR_RESUME				4228
#define MT_MUJOCO_VR_MOTOR_CTRL			4229
#define MT_MUJOCO_VR_MOTOR_CONFIG		4230
#define MT_MUJOCO_VR_SET_RGBA			4231
#define MT_MUJOCO_VR_MSG                4232

// MujocoVR Defines
#define MJ_VR_MAX_MOCAP_COUNT	 32
#define MJ_VR_MAX_BODY_COUNT	 64
#define MJ_VR_MAX_MOTOR_COUNT	 32
#define MJ_VR_MAX_JOINT_COUNT	 64
#define MJ_VR_MAX_JOINT_DOF		128
#define MJ_VR_MAX_CONTACT_COUNT	 32
#define MJ_VR_MAX_TENDON_COUNT   32

// MujocoVR C++ Definitions

typedef struct {
	int serial_no;
	int sub_sample;
} MJVR_MSG_HEADER;

typedef struct {
	MJVR_MSG_HEADER header;
} MDF_MUJOCO_VR_REQUEST_STATE;

typedef struct {
	MJVR_MSG_HEADER header;
	int requester_MID;
	int reserved;

	double sim_time;
    double body_position[3 * MJ_VR_MAX_BODY_COUNT];
    double body_orientation[4 * MJ_VR_MAX_BODY_COUNT];

	int motor_ctrltype[MJ_VR_MAX_MOTOR_COUNT];
    double motor_position[MJ_VR_MAX_MOTOR_COUNT];
    double motor_velocity[MJ_VR_MAX_MOTOR_COUNT];

    double joint_position[MJ_VR_MAX_JOINT_DOF];
    double joint_velocity[MJ_VR_MAX_JOINT_DOF];
	double joint_torque[MJ_VR_MAX_JOINT_DOF];

    double contact[MJ_VR_MAX_CONTACT_COUNT];
} MDF_MUJOCO_VR_REPLY_STATE;

typedef struct {
	MJVR_MSG_HEADER header;
} MDF_MUJOCO_VR_REQUEST_MODEL_INFO;

typedef struct {
	MJVR_MSG_HEADER header;
	int requester_MID;
	int reserved;

	char model_file[512];
	double sim_time;
	int nq;
	int nv;
    int num_body;
	int num_mocap;
	int num_float;
    int num_motor;
    int num_joint;
    int num_contact;
	int num_tendon;
	int reserved1;
	int body_id[MJ_VR_MAX_BODY_COUNT];
	int mocap_id[MJ_VR_MAX_MOCAP_COUNT]; // bodyid of mocap body
	int float_id[MJ_VR_MAX_MOCAP_COUNT]; // bodyid of floating body
	int motor_id[MJ_VR_MAX_MOTOR_COUNT];
	int joint_id[MJ_VR_MAX_JOINT_COUNT];
	int contact_id[MJ_VR_MAX_CONTACT_COUNT];
	int tendon_id[MJ_VR_MAX_TENDON_COUNT];
	int joint_type[MJ_VR_MAX_JOINT_COUNT];
    double max_motor_limits[MJ_VR_MAX_MOTOR_COUNT];
    double min_motor_limits[MJ_VR_MAX_MOTOR_COUNT];
	char body_names[1024];  //Names separated by NULL
	char mocap_names[1024]; //Names separated by NULL
	char float_names[1024]; //Names separated by NULL
	char motor_names[1024]; //Names separated by NULL
	char joint_names[1024]; //Names separated by NULL
	char contact_names[1024]; //Names separated by NULL
	char tendon_names[1024]; //Names separated by NULL
} MDF_MUJOCO_VR_REPLY_MODEL_INFO;

typedef struct {
	MJVR_MSG_HEADER header;
} MDF_MUJOCO_VR_REQUEST_LINK_STATE;

typedef struct {
	MJVR_MSG_HEADER header;
	int requester_MID;
	int reserved;
	
	int nlink;
	int nfloat;
	int body_linkid[MJ_VR_MAX_BODY_COUNT];
	int link_followerid[MJ_VR_MAX_BODY_COUNT];
	int link_leaderid[MJ_VR_MAX_BODY_COUNT];
	char link_active[MJ_VR_MAX_BODY_COUNT];
	double link_rpos[3 * MJ_VR_MAX_BODY_COUNT];
	double link_quat_leader[4 * MJ_VR_MAX_BODY_COUNT];
	double link_quat_follower[4 * MJ_VR_MAX_BODY_COUNT];
} MDF_MUJOCO_VR_REPLY_LINK_STATE;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_links;
	int padding;
	int follower_id[MJ_VR_MAX_MOCAP_COUNT];
	int leader_id[MJ_VR_MAX_MOCAP_COUNT];
} MDF_MUJOCO_VR_LINK;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_links;
	int padding;
	int follower_id[MJ_VR_MAX_MOCAP_COUNT];
} MDF_MUJOCO_VR_LINK_RESET;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_id; // Must be <= than MJ_VR_MAX_MOCAP_COUNT
	int padding;
	int id[MJ_VR_MAX_MOCAP_COUNT]; // size: n
	double position[3 * MJ_VR_MAX_MOCAP_COUNT]; // size: n x 3
	double orientation[4 * MJ_VR_MAX_MOCAP_COUNT]; // size: n x 4
} MDF_MUJOCO_VR_MOCAP_MOVE;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_id; // Must be <= than MJ_VR_MAX_MOTOR_COUNT
	int padding;
	int id[MJ_VR_MAX_MOTOR_COUNT];
	double position[MJ_VR_MAX_MOTOR_COUNT];
} MDF_MUJOCO_VR_MOTOR_MOVE;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_id; // Must be <= than MJ_VR_MAX_MOCAP_COUNT
	int padding;
	int float_body_id[MJ_VR_MAX_MOCAP_COUNT];
	double position[3 * MJ_VR_MAX_MOCAP_COUNT];
	double orientation[4 * MJ_VR_MAX_MOCAP_COUNT];
	char disable_link[MJ_VR_MAX_MOCAP_COUNT];
} MDF_MUJOCO_VR_FLOATBODY_MOVE;

typedef struct {
	char model_filename[512];
} MDF_MUJOCO_VR_LOAD_MODEL;

typedef struct {
	MJVR_MSG_HEADER header;
	int type; // element type. _mjtObj enum values
	int id; // element id
	float rgba[4]; // rgba array
} MDF_MUJOCO_VR_SET_RGBA;

typedef struct{
	MJVR_MSG_HEADER header;
	int num_id; // Must be <= than MJ_VR_MAX_MOTOR_COUNT
	int padding;
	int id[MJ_VR_MAX_MOTOR_COUNT];
	int type[MJ_VR_MAX_MOTOR_COUNT];
	double k_p[MJ_VR_MAX_MOTOR_COUNT];
	double k_i[MJ_VR_MAX_MOTOR_COUNT];
	double k_d[MJ_VR_MAX_MOTOR_COUNT];
	double setpt[MJ_VR_MAX_MOTOR_COUNT];
} MDF_MUJOCO_VR_MOTOR_CONFIG;

typedef struct {
	MJVR_MSG_HEADER header;
	int num_id; // Must be <= than MJ_VR_MAX_MOTOR_COUNT
	int padding;
	int id[MJ_VR_MAX_MOTOR_COUNT];
	double ctrl[MJ_VR_MAX_MOTOR_COUNT];
} MDF_MUJOCO_VR_MOTOR_CTRL;

typedef struct{
    char message[256]; // mujoco message text
    int position; // 0: top right, 1: top left, 2: bottom right, 3: bottom left
} MDF_MUJOCO_VR_MSG;


#endif //_MUJOCOVR_TYPES_