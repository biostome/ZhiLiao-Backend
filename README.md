# Rino体系IPC的SDK
## 前提
@Rino/rino-panel-sdk最低需要@1.1.4版本
## Suopoort

# 核心概念
### client: 
- IPC客户端实例, 一般来说每台设备都对应这一个client, 然后可以通过client调用所有的ipc业务, 如控制播放, 查询回放记录, 通过rtc通道发送数据等
- 可以初始化项目时通过```RinoIPCSDK.createClient```创建一个client
- 可以通过```RinoIPCSDK.getClient(devId)```获取已经创建的client

### playType:
- client的许多api都需要传递这个参数, 这个参数是用来告诉client需要处理针对什么场景的业务, 比如直播时传递"live", 回放时传递"playback"


# 使用教程
``` tsx
// 初始化项目时使用SDK初始化一个client
try {
    RinoIPCSDK.createClient(devInfo.devId, devInfo.uuid!, devInfo.ipcCameraNum!, devInfo.rtcType || 'agora' as any);
} catch (e) {
    console.error("createClient fail", e);
}

const client = RinoIPCSDK.getClient(devId);

// 调用拍照api拍摄直播流
client.snapShot(playType, curSelectedCameraIdx, `${dirPath}/${curSelectedCameraIdx}-${Date.now()}.jpg`)

// 通过client.event可以订阅client的IPC相关业务事件
const subscription = client.event.subscribeOnSnapShot((data){});
subscription.remove(); // 取消订阅

// 播放直播流
<RinoIPCPlayView
    devId={RinoSDK.device.deviceInfo.devId}
    scene={'live'}
    cameraIndex={curSelectedCameraIdx}
    mute={mute}
    leaveChannelWhenInActive
/>


// 播放回放流
<RinoIPCPlayView
    devId={RinoSDK.device.deviceInfo.devId}
    scene={'playback'}
    cameraIndex={curSelectedCameraIdx}
    mute={mute}
    playbackDefaultPlaytime={recordStartTime}
    leaveChannelWhenInActive
/>

// 控制回放播放时间
client.seekPlayback(startTime, startTime + duration);
// 暂停回放
client.pausePlayback();
// 继续回放
client.resumePlayback();
```# ZhiLiao-Backend
