import pyaudio
import cv2
import time
from threading import Thread
from queue import Queue
import sys


wait_key_num = 42
init = True
start_time = 0

video_picture = Queue()
video_capture = 0

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()


input_device_index = int(sys.argv[1])
output_device_index = int(sys.argv[2])
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=CHUNK)

play_stream = p.open(format=FORMAT,
                     channels=CHANNELS,
                     rate=RATE,
                     output=True,
                     output_device_index=output_device_index,
                     frames_per_buffer=CHUNK)
recorded_data = Queue()

def play_voices():
    global play_stream
    time.sleep(1.9)
    while True:
        play_stream.write(recorded_data.get())

def record():
    global stream
    while True:
        data = stream.read(CHUNK)
        recorded_data.put(data)

def read_video():
    num = 1
    while True:
        # read video
        video_capture = cv2.VideoCapture(f"output_{num}.mp4")
        #print(video_capture.isOpened())
        if video_capture.isOpened():
            # read frames
            for i in range(24):
                ret, frame = video_capture.read()
                if ret:
                    video_picture.put(frame)
            num += 1
        elif num==1 and cv2.VideoCapture(f"output_{2}.mp4").isOpened():
            num += 1

play_sound=Thread(target=play_voices)
play_sound.daemon = True

sound_record=Thread(target=record)
sound_record.daemon = True

read_videos=Thread(target=read_video)
read_videos.daemon = True

play_video_RUN=True

# 逐一播放影片q
#def play_video(input_device_index,output_device_index):
#    global play_video_RUN
#    global init
#    global stream
#    global play_stream
#    global num
#    global wait_key_num

number = 0
while play_video_RUN:
    if init == True:
        sound_record.start()
        play_sound.start()
        read_videos.start()
        time.sleep(1)
        init = False
    
    # show frame
    frame =  video_picture.get()
    cv2.imshow('Video', frame)
    # click q to stop
    if cv2.waitKey(wait_key_num) & 0xFF == ord('q'):
        # release resource
        video_capture.release()
        stream.stop_stream()
        stream.close()
        play_stream.stop_stream()
        play_stream.close()
        p.terminate()
        cv2.destroyAllWindows()
        exit(1)
    number = number + 1
    if number == 24:
        number = 0
        end_time = time.time()
        print("花多久播影片", end_time - start_time,end="")
        if(end_time - start_time)>1:
            wait_key_num-=1
            print(", wait_key_num-1",wait_key_num)
        elif(end_time - start_time)<1:
            wait_key_num+=1
            print(", wait_key_num+1",wait_key_num)
        
        start_time = time.time()


video_capture.release()
stream.stop_stream()
stream.close()
play_stream.stop_stream()
play_stream.close()
p.terminate()
cv2.destroyAllWindows()
    #sys.exit(1)
    


