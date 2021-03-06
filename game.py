import struct
import pygame
import pygame.camera
import pygame.time
import cv2.cv as cv
import socket
from pygame.locals import *

pygame.init()
pygame.camera.init()

camlist = pygame.camera.list_cameras()
print(camlist)
if camlist:
    cam = pygame.camera.Camera(camlist[0],(640,480))


def toHex(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)


class Transmitter(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP
        
        self.bufferSize = 8192
        self.buffer = ""
    
    def send(self):
#         for i in range(0, len(self.buffer), self.bufferSize):
#             self.sock.sendto(self.buffer[i:i+self.bufferSize], ("127.0.0.1", 50005))
#         
#         self.buffer = ""
        self.sock.sendto(self.buffer, ("127.0.0.1", 50005))
        
    def transmit(self, data):
#         self.buffer += data
#         if len(self.buffer) > self.bufferSize:
#             self.send()
        self.buffer += data
        self.send()
        self.buffer = ""


class Capture(object):
    def __init__(self):
        self.size = (640,480)
        self.smallerSize = (self.size[0]/2, self.size[1]/2)
        # create a display surface. standard pygame stuff
        self.display = pygame.display.set_mode(self.smallerSize, 0)
        
        # this is the same as what we saw before
        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError("Sorry, no cameras detected.")
        #self.cam = pygame.camera.Camera(self.clist[0], self.size)
        self.cam = pygame.camera.Camera("/dev/video1", self.size)
        self.cam.start()

        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshot = pygame.surface.Surface(self.size, 0, self.display)
        self.lastSnapshot = pygame.surface.Surface(self.size, 0, self.display)
        
#         fourcc = cv.CV_FOURCC('P','I','M','1')
        fourcc = cv.CV_FOURCC('W','E','B','P')
        self.fps = 12
        self.writer = cv.CreateVideoWriter('out.avi', fourcc, 24, self.smallerSize, 1)
        
        self.clock = pygame.time.Clock()
        self.total_bytes = 0
        self.number_of_frames = 0
        
        self.transmitter = Transmitter()

    def surface_to_string(self, surface):
        """Convert a pygame surface into string"""
        return pygame.image.tostring(surface, 'RGB')

    def pygame_to_cvimage(self, surface):
        """Convert a pygame surface into a cv image"""
        cv_image = cv.CreateImageHeader(surface.get_size(), cv.IPL_DEPTH_8U, 3)
        
        # flip the image from RGB to BGR for opencv
        r,g,b,a = surface.get_masks()
        surface.set_masks((b,g,r,a))
        r,g,b,a = surface.get_shifts()
        surface.set_shifts((b,g,r,a))
        
        image_string = self.surface_to_string(surface)
        #print len(image_string)
        cv.SetData(cv_image, image_string)
        return cv_image

    def get_and_flip(self):
        # if you don't want to tie the framerate to the camera, you can check 
        # if the camera has an image ready.  note that while this works
        # on most cameras, some will never return true.
            
        if self.cam.query_image():
            self.snapshot = self.cam.get_image(self.snapshot)

        # blit it to the display surface.  simple!
#        self.display.blit(self.snapshot.subsurface(pygame.Rect(left, top, width, height)), (0,0))
        subview = self.snapshot.subsurface(pygame.Rect(160, 120, 320, 240))
        lastSubview = self.lastSnapshot.subsurface(pygame.Rect(160, 120, 320, 240))
        
        lastSubviewPxArray = pygame.pixelarray.PixelArray(lastSubview)
        subviewPxArray = pygame.pixelarray.PixelArray(subview)
        compared = subviewPxArray.compare(lastSubviewPxArray, 0.12)
        
        frameAsString = ""
        changes = 0
        # find the white pixels only
        for x in range(0, 320):
            transmitColumn = ""
            for y in range(0, 240):
                if compared[x, y] == compared.surface.map_rgb((255, 255, 255)):
                    changes += 1
                    color = subviewPxArray[x, y]
                    lastSubviewPxArray[x, y] = color
                    toTransmit = struct.Struct("4B")
                    toTransmitString = toTransmit.pack(y, (color & 0xFF0000) >> 16, (color & 0x00FF00) >> 8, color & 0x0000FF)
                    transmitColumn += toTransmitString
                    #print color, ":", toTransmit.size, ": ", ":".join("{:02x}".format(ord(c)) for c in toTransmitString)
            # mark end of column
            if len(transmitColumn) != 0:
                #print "column:", toHex(transmitColumn)
                thisColumnAsString = struct.Struct("hB").pack(x, len(transmitColumn)/4) + transmitColumn # column index, nr of changes, changes
                frameAsString += thisColumnAsString 
                self.transmitter.transmit(thisColumnAsString)
        
        self.total_bytes += len(frameAsString)
        self.number_of_frames += 1
        
        #print toHex(frameAsString)
        
        if (self.number_of_frames % 1000) == 0:
            print "Average bytes = ", (self.total_bytes / self.number_of_frames) 
        
#         self.transmitter.transmit(frameAsString)
        
        # show actual view
        #self.display.blit(subview, (0,0))
        # show difference view
        #self.display.blit(compared.make_surface(), (0,0))
        # show morphed view
        lastSubviewPxArraySurface = lastSubviewPxArray.make_surface()
        self.display.blit(lastSubviewPxArraySurface, (0,0))
        
        
        pygame.display.flip()
        
        cv.WriteFrame(self.writer, self.pygame_to_cvimage(lastSubviewPxArraySurface.copy()))
        cv.WriteFrame(self.writer, self.pygame_to_cvimage(lastSubviewPxArraySurface.copy()))

    def main(self):
        going = True
        while going:
            events = pygame.event.get()
            for e in events:
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    self.cam.stop()
                    going = False

            self.clock.tick(self.fps)
            self.get_and_flip()

Capture().main()
