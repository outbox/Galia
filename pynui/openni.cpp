#include "openni.h"
#include "nui_data.h"
#include <XnOpenNI.h>
#include <XnCodecIDs.h>
#include <boost/interprocess/ipc/message_queue.hpp>
#include <boost/thread.hpp>
#include <string>
#include <signal.h>

using namespace boost::interprocess;

static nui_data data;
static XnContext* context;
static XnNodeHandle userGenerator;
static XnNodeHandle depthGenerator;
static XnNodeHandle recorder;

void add_event(nui_event::event_type event, XnUserID user) {
  for (int i=0; i<max_events;++i) {
    if (!data.events[i].event) {
      data.events[i].event = event;
      data.events[i].user = user;
      return;
    }
  }
}

const char* calibration_path() {
  return "calibration.data";
}

void XN_CALLBACK_TYPE new_user(XnNodeHandle generator, XnUserID user, void* pCookie) {
  printf("New user %d\n", user);
  xnStartPoseDetection(generator, "Psi", user);
  XnStatus status = xnLoadSkeletonCalibrationDataFromFile(generator, user, calibration_path());
  if(status != XN_STATUS_OK) status = xnLoadSkeletonCalibrationData(generator, user, 0);
  if(status != XN_STATUS_OK) {
    printf("Failed to load calibration data\n");
    xnRequestSkeletonCalibration(generator, user, TRUE);
  } else {
    xnStartSkeletonTracking(generator, user);
  }
  add_event(nui_event::new_user, user);
}

void XN_CALLBACK_TYPE lost_user(XnNodeHandle generator, XnUserID user, void* pCookie) {
  printf("Lost user %d\n", user);
  add_event(nui_event::lost_user, user);
}

void XN_CALLBACK_TYPE pose_detected(XnNodeHandle pose, const XnChar* strPose, XnUserID user, void* cxt) {
  printf("Pose detected \"%s\" for user %d\n", strPose, user);
  add_event(nui_event::pose_start, user);
}

void XN_CALLBACK_TYPE out_of_pose(XnNodeHandle pose, const XnChar* strPose, XnUserID user, void* cxt) {
  printf("Out of pose \"%s\" for user %d\n", strPose, user);
  add_event(nui_event::pose_end, user);
}

void XN_CALLBACK_TYPE calibration_started(XnNodeHandle generator, XnUserID user, void* cxt) {
  printf("Calibration started\n");
  add_event(nui_event::calibration_start, user);
}

void XN_CALLBACK_TYPE calibration_ended(XnNodeHandle generator, XnUserID user, XnBool bSuccess, void* cxt) {
  printf("Calibration done [%d] %ssuccessfully\n", user, bSuccess?"":"un");
  if (bSuccess) {
    XnStatus status = xnSaveSkeletonCalibrationDataToFile(generator, user, calibration_path());
    xnSaveSkeletonCalibrationData(generator, user, 0);
    if(status != XN_STATUS_OK) printf("Failed to save calibration\n");
    status = xnStartSkeletonTracking(generator, user);
    if(status != XN_STATUS_OK) printf("Failed to start tracking\n");
  } else {
    xnRequestSkeletonCalibration(generator, user, TRUE);
  }
  xnStartPoseDetection(generator, "Psi", user);
  add_event(nui_event::calibration_end, user);
}

void check_status(XnStatus status, const char* what) {
  if (status != XN_STATUS_OK) {
    printf("%s failed: %s\n", what, xnGetStatusString(status));
    exit(1);
  }
}

void start_capture(XnNodeHandle recorder, XnNodeHandle generator) {
  char recordFile[256] = {0};
  time_t rawtime;
  struct tm *timeinfo;

  time(&rawtime);
  timeinfo = localtime(&rawtime);
  XnUInt32 size;
  xnOSStrFormat(recordFile, sizeof(recordFile)-1, &size,
		"record_%d_%02d_%02d[%02d_%02d_%02d].oni",
                timeinfo->tm_year + 1900, timeinfo->tm_mon + 1, timeinfo->tm_mday, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);

  xnSetRecorderDestination(recorder, XN_RECORD_MEDIUM_FILE, recordFile);
  xnAddNodeToRecording(recorder, generator, XN_CODEC_16Z_EMB_TABLES);
}

void sighandler(int signum) {
  xnRemoveNodeFromRecording(recorder, depthGenerator);
  printf("Process %d got signal %d\n", getpid(), signum);
  exit(0);
}

void openni_loop(bool record, std::string replay) {
//  signal(SIGSEGV, sighandler);
//  signal(SIGKILL, sighandler);
//  signal(SIGTERM, sighandler);

  printf("OpenNI process started.\n");

  message_queue mq(open_or_create, "kinect_queue", 1, sizeof(nui_data));
  
  check_status(xnInit(&context), "Init");
  if(replay.length()) {
    check_status(xnContextOpenFileRecordingEx(context, replay.c_str(), &depthGenerator), "Open replay");
  } else {
    check_status(xnCreateDepthGenerator(context, &depthGenerator, 0, 0), "Create depth");
  }
  check_status(xnCreateUserGenerator(context, &userGenerator, 0, 0), "Create user");
  
  if(!xnIsCapabilitySupported(userGenerator, XN_CAPABILITY_POSE_DETECTION)) {
    printf("User generator doesn't support pose detection.\n");
    exit(1);
  }
  if (!xnIsCapabilitySupported(userGenerator, XN_CAPABILITY_SKELETON)) {
    printf("User generator doesn't support skeleton.\n");
    exit(1);
  }
  
  xnSetGlobalMirror(context, true);
  
  xnSetSkeletonProfile(userGenerator, XN_SKEL_PROFILE_ALL);
  
  check_status(xnStartGeneratingAll(context), "StartGenerating");
  
  XnCallbackHandle user_cb, calibration_cb, pose_detected_cb, out_of_pose_cb;
  xnRegisterUserCallbacks(userGenerator, ::new_user, ::lost_user, 0, &user_cb);
  xnRegisterCalibrationCallbacks(userGenerator, ::calibration_started, ::calibration_ended, 0, &calibration_cb);
  xnRegisterToPoseDetected(userGenerator, ::pose_detected, 0, &pose_detected_cb);
  xnRegisterToPoseDetected(userGenerator, ::out_of_pose, 0, &out_of_pose_cb);

  XnOutputMetaData outputData;
  XnMapMetaData mapData;
  mapData.pOutput = &outputData;
  mapData.PixelFormat = XN_PIXEL_FORMAT_GRAYSCALE_16_BIT;
  XnDepthMetaData depthData;
  depthData.pMap = &mapData;
  xnGetDepthMetaData(depthGenerator, &depthData);
  data.width = depthData.pMap->Res.X;
  data.height = depthData.pMap->Res.Y;
    
  if (data.width*data.height > sizeof(data.depth_map) / sizeof(XnPoint3D)) {
    printf("Depth map is too big\n");
    exit(1);
  }
  
  if(record) start_capture(recorder, depthGenerator);

  while (true) {
    // exit if parent dies
    if (getppid() == 1) exit(0);
        
    xnWaitAnyUpdateAll(context);

    XnOutputMetaData outputData;
    XnMapMetaData mapData;
    mapData.pOutput = &outputData;
    mapData.PixelFormat = XN_PIXEL_FORMAT_GRAYSCALE_16_BIT;
    XnSceneMetaData smd;
    smd.pMap = &mapData;
    xnGetUserPixels(userGenerator, 0, &smd);
    memcpy(data.label_map, smd.pData, data.width*data.height*sizeof(XnLabel));
        
    XnDepthMetaData depthData;
    depthData.pMap = &mapData;
    xnGetDepthMetaData(depthGenerator, &depthData);
    const XnDepthPixel* source = depthData.pData;
    XnPoint3D* target = data.depth_map;
        
    for (unsigned int y=0; y<data.height; y++) {
      for (unsigned int x=0; x < data.width; ++x, ++target, ++source) {
        target->X = x;
        target->Y = y;
        target->Z = *source;
      }
    }
        
    xnConvertProjectiveToRealWorld(depthGenerator, data.width*data.height, data.depth_map, data.depth_map);
        
    for (int i=0; i<max_users; ++i) {
      data.users[i] = false;
    }
        
    XnUserID users[15];
    XnUInt16 user_count = 15;
    xnGetUsers(userGenerator, users, &user_count);
    for (int i = 0; i<user_count; ++i) {
      XnUserID user = users[i];
      data.users[user] = true;
            
      for (int j = 1; j < joint_count; ++j) {
        xnGetSkeletonJoint(userGenerator, user, (XnSkeletonJoint)j, &data.joints[user][j]);
      }
    }
        
    if(mq.try_send(&data, sizeof(nui_data), 0)) {
      data.clear_events();
    }
  }
}

struct callable{
  bool record;
  std::string replay;
  void operator()() { openni_loop(record, replay); };
};
void create_openni_thread(bool record, const char* replay) {
  callable c = {record, replay?replay:""};
  boost::thread t(c);
}
