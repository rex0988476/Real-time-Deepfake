from threading import Thread
import cv2, time
import os
import sys
import subprocess
# single thread doubles performance of gpu-mode - needs to be set before torch import
if any(arg.startswith('--gpu-vendor') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
from v3_delete_video import delete_video
from v3_swapper import  get_face_swapper
from v3_analyser import get_face_single
from queue import Queue
import ffmpeg
#import v5_play_video

def process_img(frame):
    is_get_face,face = get_face_single(frame)
    if is_get_face:
        result = get_face_swapper().get(frame, face, source_face, paste_back=True)
    else:
        result=face
    return result

class VideoStreamWidget(object):
    def __init__(self,audio_in_num,audio_out_num, src=0, is_complementary_frame=True):
        # queue
        self.q=Queue()
        self.q_save = Queue()
        self.q_make_video_frames_list=Queue()
        self.q_wake_complementary_frame=Queue()
        # others
        self.threads=[]
        self.capture = cv2.VideoCapture(0)
        self.init = True
        self.audio_in_num=audio_in_num
        self.audio_out_num=audio_out_num
        # make video variable
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.output_num = 1
        self.result_video = cv2.VideoWriter()
        # complementary frame variable
        self.output_clear_num = 1
        self.delete_num_name = 1
        self.output_clear_count = 0
        # Start the thread to read frames from the video stream
        i=0
        while i<8:
            thread = Thread(target=self.update)
            thread.daemon = True
            self.threads.append(thread)
            thread.start()
            i+=1
        self.is_complementary_frame=is_complementary_frame
        if self.is_complementary_frame:
            # count time thread
            self.thread_count_time = Thread(target=self.count_time)
            self.thread_count_time.daemon = True
            # complementary frame thread
            t_complementary_frame=Thread(target=self.interpolate_frames)
            t_complementary_frame.daemon = True
            t_complementary_frame.start()
        self.t_play_videos = Thread(target=self.call_play_video)
        self.t_play_videos.daemon = True
        self.t_play_videos.start()

    def update(self):
        # Read the next frame from the stream in a different thread
        global RUN
        while RUN:
        #while True:
            if self.capture.isOpened():
                (status, frame) = self.capture.read()
                if status:
                    result = process_img(frame)
                    self.q.put(result)
            #time.sleep(.01)

    def count_time(self):
        global RUN
        while RUN:
        #while True:
            #self.q_save = Queue()
            start=time.time()
            time.sleep(0.97)
            end=time.time()
            print(f"count 多久:{end-start}")
            #get 1 sec frames
            self.frames_to_video()

    def frames_to_video(self):
        video_fps = self.q_save.qsize()
        if video_fps > 0:
            self.result_video = cv2.VideoWriter(f'output_{self.output_num}.mp4', self.fourcc, video_fps, (640, 480))
            i=0
            while i<video_fps:
                self.result_video.write(self.q_save.get())# stuck until 1 sec frames in)
                i+=1
            self.result_video.release()
            self.output_num += 1
            # wake interpolate_frames up
            self.q_wake_complementary_frame.put(1)
  
    def interpolate_frames(self):
        FPS=24
        global RUN
        while RUN:
        #while True:
            _=self.q_wake_complementary_frame.get() # stuck until make video finish
            if os.path.isfile(f"output_{self.output_clear_num}.mp4"):
                input_file = f"./output_{self.output_clear_num}.mp4"
                output_file = f"./output_clear_{self.output_clear_num}.mp4"
                print(input_file)
                print(output_file)
                frame_rate = FPS  # 目標幀率
                start=time.time()
                ffmpeg.input(input_file).output(output_file, vf='minterpolate=fps=' + str(frame_rate)).run()
                end=time.time()
                print(f"補 多久:{end-start}")
                #os.remove(f"output_{num}.mp4")
                self.output_clear_num += 1
                self.output_clear_count += 1
            else:
                print("失敗")
                pass
            """
            if self.output_clear_count>=100:
                #os.remove(f"./output_clear_{self.delete_num_name}.mp4")
                os.remove("./output_{self.delete_num_name}.mp4")
                self.delete_num_name+=1
                self.output_clear_count-=1
                """

    def final(self):
        self.result_video.release()

    def call_play_video(self):
        #v5_play_video.play_video(self.audio_in_num,self.audio_out_num)
        # open play_video
        file_path = f"v5_play_video.py"
        self.process = subprocess.Popen(["python", file_path,str(self.audio_in_num),str(self.audio_out_num)])

    def show_frame(self):
        global RUN
        output = self.q.get()
        if self.init == True:
            if self.is_complementary_frame:
                self.thread_count_time.start()
            self.start_time = time.time()
            self.frame_count = 0
        else:
            # 計算FPS
            self.frame_count += 1
            elapsed_time = time.time() - self.start_time
            fps = self.frame_count / elapsed_time
            
        # Display frames in main program
        
        if self.init == False:
            pass
            #cv2.putText(output, f"FPS: {round(fps, 2)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if self.is_complementary_frame:
            self.q_save.put(output)
        cv2.imshow('frame', output)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.final()
            self.process.terminate()
            self.capture.release()
            cv2.destroyAllWindows()
            RUN=False
            #v5_play_video.play_video_RUN=False
            #os._exit(0)
        self.init = False
        #return(output)

source_face = ""
RUN=True
#if __name__ == '__main__':

def app(source_face_path,camera_num,audio_in_num,audio_out_num,is_complementary_frame):
    #delete old files
    delete_video()
    #read source img
    global source_face
    source_face = cv2.imread(source_face_path)
    is_get_source_face,source_face = get_face_single(source_face)
    if not is_get_source_face:
        print("source no face.")
        os._exit(0)
    #app class
    #v5_play_video.play_video_RUN=True
    global RUN
    video_stream_widget = VideoStreamWidget(src=camera_num,audio_in_num=audio_in_num,audio_out_num=audio_out_num,is_complementary_frame=is_complementary_frame)
    while RUN:
        video_stream_widget.show_frame()
    #v5_play_video.play_video_RUN=False
    video_stream_widget.capture.release()
    video_stream_widget.process.terminate()
    cv2.destroyAllWindows()
    video_stream_widget.final()
    #os._exit(0)
#app('./data/target.jpg',0,2,4,False)