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

    def __init__( self, pipe_name= None ):
        self.wpipe= None
        if pipe_name is not None:
            self.open( pipe_name )

    @staticmethod
    def get_pipe_name( pipe_name ):
        return  r'\\.\pipe\Streaming' + pipe_name

    def open( self, pipe_name ):
        self.wpipe= win32pipe.CreateNamedPipe( pipe_name, win32pipe.PIPE_ACCESS_DUPLEX, win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT, 1, Config.BufferSize, Config.BufferSize, 0, None )
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

    def __init__( self, pipe_name= None ):
        self.wpipe= None
        if pipe_name is not None:
            self.open( pipe_name )

    @staticmethod
    def get_pipe_name( pipe_name ):
        return  '/tmp/Streaming' + pipe_name

    def open( self, pipe_name ):
        self.pipe_name= pipe_name
        try:
            os.mkfifo( pipe_name )
        except OSError as e:
            import  errno
            if e.errno != errno.EEXIST:
                raise
        self.wpipe= open( pipe_name, 'wb' )

    def close( self ):
        if self.wpipe:
            try:
                self.wpipe.close()
                self.wpipe= None
                os.remove( self.pipe_name )
            except OSError as e:
                pass

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
        if platform.system() == 'Windows':
            self.pipe_class= WinPipe
        else:
            self.pipe_class= FifoPipe
        self.pipe_name= self.pipe_class.get_pipe_name( pipe_name )

    def exec_pipe( self, command, pipe_name ):
        pipe= self.pipe_class( pipe_name )
        self.pipe= pipe
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

    def get_filename( self ):
        return  self.pipe_name



class MirrorPlayer( threading.Thread ):

    def __init__( self, file_name= None ):
        super().__init__()
        self.name= file_name

    def play( self, input_file_name ):
        title= 'Android mirror'
        video= cv2.VideoCapture( input_file_name )
        cv2.namedWindow( title, cv2.WINDOW_AUTOSIZE )
        while True:
            is_read,frame= video.read()
            k= cv2.waitKey( 1 )
            if k  == 27 or not is_read:
                break
            cv2.imshow( title, frame )
        video.release()

    def run( self ):
        self.play( self.name )



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

        player= MirrorPlayer()
        player.play( pipe.get_filename() )

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


