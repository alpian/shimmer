import struct
import pygame
import pygame.camera
import pygame.time
import cv2.cv as cv
import socket
import itertools
import threading
from pygame.locals import *

pygame.init()

def toHex(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

class Receiver(threading.Thread):
    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP
        self.sock.bind(("127.0.0.1", 50005))
        self.listener = listener
            
    def run(self):
        while True:
            data, address = self.sock.recvfrom(8192)
            self.listener.handle(data)


class Displayer(object):
    def __init__(self):
        self.size = (640,480)
        self.smallerSize = (self.size[0]/2, self.size[1]/2)
        # create a display surface. standard pygame stuff
        self.display = pygame.display.set_mode(self.smallerSize, 0)
        
        #self.cam = pygame.camera.Camera(self.clist[0], self.size)

        # create a surface to capture to.  for performance purposes
        # bit depth is the same as that of the display surface.
        self.snapshot = pygame.pixelarray.PixelArray(pygame.surface.Surface(self.smallerSize, 0, self.display))
        
        self.receiver = Receiver(self)
        self.receiver.daemon = True
        self.receiver.start()
        
        self.fps = 12
        self.clock = pygame.time.Clock()

    def handle(self, data):
        dataIndex = 0
        while dataIndex < len(data):
            columnIndex, numberOfChanges = struct.Struct("hB").unpack(data[dataIndex : dataIndex + 3])
            changesString = data[dataIndex + 3 : dataIndex + 3 + (numberOfChanges * 4)]
            changes = grouper(changesString, 4)
            dataIndex += 3 + (numberOfChanges * 4)
            for change in changes:
                if len(change) == 4:
                    rowIndex, r, g, b = map(ord, change)
                    self.snapshot[columnIndex, rowIndex] = (r << 16) | (g << 8) | b
        
        self.display.blit(self.snapshot.make_surface(), (0,0))
        pygame.display.flip()
        
    def main(self):
        going = True
        while going:
            events = pygame.event.get()
            for e in events:
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    # close the camera safely
                    going = False

            self.clock.tick(self.fps)

Displayer().main()
