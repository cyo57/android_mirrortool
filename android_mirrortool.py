# Android Mirror Tool 2019/02/02 Hiroyuki Ogasawara
# vim:ts=4 sw=4 et:

# $ pip3 install opencv-python
# $ pip3 install pywin32
# $ python android_mirrortool.py


import  os
import  sys
import  subprocess
import  cv2
import  threading
import  platform
import  datetime
if platform.system() == 'Windows':
    import  win32pipe, win32file


class Config:

    BufferSize= 1024
    CaptureSize= '1920x1080'
    Bitrate= '12m'

    def __init__( self ):
        pass



class WinPipe:

    def __init__( self, name= None ):
        self.wpipe= None
        if name is not None:
            self.open( name )

    def open( self, pipe_name ):
        self.name= r'\\.\pipe\Streaming'+pipe_name
        self.wpipe= win32pipe.CreateNamedPipe( self.name, win32pipe.PIPE_ACCESS_DUPLEX, win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT, 1, Config.BufferSize, Config.BufferSize, 0, None )
        win32pipe.ConnectNamedPipe( self.wpipe, None )

    def close( self ):
        if self.wpipe:
            win32pipe.DisconnectNamedPipe( self.wpipe )
            win32file.CloseHandle( self.wpipe )
        self.wpipe= None

    def write( self, data ):
        try:
            win32file.WriteFile( self.wpipe, data )
        except:
            pass

    def __enter__( self ):
        return  self

    def __exit__( self, *arg ):
        self.close()



class FifoPipe:

    def __init__( self, name= None ):
        self.wpipe= None
        if name is not None:
            self.open( name )

    def open( self, pipe_name ):
        self.name= '/tmp/Streaming'+pipe_name
        try:
            os.mkfifo( self.name )
        except OSError as e:
            import  errno
            if e.errno != errno.EEXIST:
                raise
        self.wpipe= open( self.name, 'wb' )

    def close( self ):
        if self.wpipe:
            os.close( self.wpipe )
        self.wpipe= None

    def write( self, data ):
        try:
            self.wpipe.write( data )
        except:
            pass

    def __enter__( self ):
        return  self

    def __exit__( self, *arg ):
        self.close()



class StreamingPipe( threading.Thread ):

    def __init__( self, command, pipe_name ):
        super().__init__()
        self.pipe= None
        self.proc= None
        self.command= command
        self.pipe_name= pipe_name

    def exec_pipe( self, command, output_pipe_name ):
        if platform.system() == 'Windows':
            self.pipe= WinPipe( output_pipe_name )
        else:
            self.pipe= FifoPipe( output_pipe_name )
        pipe= self.pipe
        try:
            with subprocess.Popen( command, stdout=subprocess.PIPE ) as proc:
                self.proc= proc
                while True:
                    data= proc.stdout.read( Config.BufferSize )
                    if not data:
                        break
                    pipe.write( data )
        except OSError:
            print( 'Pipe Exec Error' + str(command) )
            raise
        finally:
            pipe.close()

    def run( self ):
        self.exec_pipe( self.command, self.pipe_name )

    def stop_pipe( self ):
        self.proc.kill()
        self.pipe.close()



class MirrorPlayer( threading.Thread ):

    def __init__( self, pipe_name ):
        super().__init__()
        self.pipe_name= pipe_name

    def play( self, input_pipe_name ):
        if platform.system() == 'Windows':
            self.name= r'\\.\pipe\Streaming' + input_pipe_name
        else:
            self.name= '/tmp/Streaming' + input_pipe_name
        video= cv2.VideoCapture( self.name )
        cv2.namedWindow( 'Android mirror', cv2.WINDOW_AUTOSIZE )
        frame_rate= int( video.get(5) )
        print( 'framerate', frame_rate )
        frame_rate= 1
        while True:
            is_read,frame= video.read()
            k= cv2.waitKey(frame_rate)
            if k  == 27 or not is_read:
                break
            cv2.imshow( 'Android mirror', frame )
        video.release()

    def run( self ):
        self.play( self.pipe_name )



class ScreenMirror:

    def __init__( self ):
        pass

    def f_mirror( self ):
        pipe_name= 'android1'
        command= 'adb exec-out screenrecord --output-format h264'.split()
        command+= [ '--bit-rate', Config.Bitrate, '--size', Config.CaptureSize ]
        command.append( '-' )
        pipe= StreamingPipe( command, pipe_name )
        pipe.start()

        player= MirrorPlayer( pipe_name )
        player.play( pipe_name )

        pipe.stop_pipe()
        pipe.join()

    def f_capture( self ):
        file_name= datetime.datetime.now().strftime( 'capture_%Y%m%d_%H%M%S.png' )
        command= 'adb exec-out screencap -p'.split()
        with open( file_name, 'wb' ) as fo:
            with subprocess.Popen( command, stdout=subprocess.PIPE ) as proc:
                data,err= proc.communicate()
                fo.write( data )

    def exec_func( self, func_name ):
        getattr( self, func_name )()



def usage():
    print( 'android_mirrortool.py [options]' )
    print( '  -b, --bitrate <bitrate>     ex. --bitrate 8m' )
    print( '  -s, --size <mirror_size>    ex. --size 1280x720' )
    print( '  -c, --capture               screen capture' )


def main( argv ):
    mode= 'f_mirror'
    acount= len(argv)
    ai= 1
    while ai < acount:
        arg= argv[ai]
        if arg[0] == '-':
            if arg == '-b' or arg == '--bitrate':
                if ai+1 < acount:
                    ai+= 1
                    Config.Bitrate= arg[ai]
            elif arg == '-s' or arg == '--size':
                if ai+1 < acount:
                    ai+= 1
                    Config.CaptureSize= arg[ai]
            elif arg == '-c' or arg == '--capture':
                mode= 'f_capture'
            else:
                usage()
        ai+= 1
    ScreenMirror().exec_func( mode )
    return  0


if __name__ == '__main__':
    sys.exit( main( sys.argv ) )


