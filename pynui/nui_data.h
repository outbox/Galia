#ifndef NUI_DATA_H
#define NUI_DATA_H

#include <XnOpenNI.h>

const int max_users = 10;
const int joint_count = 25;
const int max_events = 10;

struct nui_event {
    enum event_type {
        none,
        new_user,
        lost_user,
        calibration_start,
        calibration_end,
        pose_start,
        pose_end,
    };
    event_type event;
    XnUserID user;
};

struct nui_data {
    unsigned int width, height;
    XnPoint3D depth_map[640*480];
    XnLabel label_map[640*480];
    bool users[max_users];
    XnSkeletonJointTransformation joints[max_users][joint_count];
    nui_event events[max_events];
    
    nui_data() {
        width = height = 0;
        for (int i=0; i<max_users; ++i) {
            users[i] = false;
            for (int j = 0; j<joint_count;++j) {
                joints[i][j].position.fConfidence = 0;
                joints[i][j].orientation.fConfidence = 0;
            }
        }
        
        for (unsigned int i=0; i<sizeof(depth_map)/sizeof(depth_map[0]); ++i) {
            depth_map[i].X = depth_map[i].Y = depth_map[i].Z = 0;
        }
        for (unsigned int i=0; i<sizeof(label_map)/sizeof(label_map[0]); ++i) {
            label_map[i] = 0;
        }
        clear_events();
    }
    
    void clear_events() {
        for (int i=0;i<max_events; ++i) {
            events[i].event = nui_event::none;
        }
    }
};

#endif