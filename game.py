import pygame
import pygame.camera
import pygame.time
import cv2.cv as cv
from pygame.locals import *

pygame.init()
pygame.camera.init()

camlist = pygame.camera.list_cameras()
print(camlist)
if camlist:
    cam = pygame.camera.Camera(camlist[0],(640,480))


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
        self.lastSnapshot = None
        self.snapshot = pygame.surface.Surface(self.size, 0, self.display)
        
        fourcc = cv.CV_FOURCC('P','I','M','1')
        self.fps = 12
        self.writer = cv.CreateVideoWriter('out.avi', fourcc, 24, self.smallerSize, 1)
        
        self.clock = pygame.time.Clock()
        self.total_bytes = 0
        self.number_of_frames = 0

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
        self.lastSnapshot = self.snapshot.copy()
            
        if self.cam.query_image():
            self.snapshot = self.cam.get_image(self.snapshot)

        # blit it to the display surface.  simple!
#        self.display.blit(self.snapshot.subsurface(pygame.Rect(left, top, width, height)), (0,0))
        subview = self.snapshot.subsurface(pygame.Rect(160, 120, 320, 240))
        lastSubview = self.lastSnapshot.subsurface(pygame.Rect(160, 120, 320, 240))
        
        lastSubviewPxArray = pygame.pixelarray.PixelArray(lastSubview)
        subviewPxArray = pygame.pixelarray.PixelArray(subview)
        compared = subviewPxArray.compare(lastSubviewPxArray, 0.12)
        
        changes = 0
        # find the white pixels only
        for x in range(0, 320):
            for y in range(0, 240):
                if compared[x, y] == compared.surface.map_rgb((255, 255, 255)):
                    changes += 1
                    lastSubviewPxArray[x, y] = subviewPxArray[x, y]
        
        self.total_bytes += (changes * 4)
        self.number_of_frames += 1
        
        print "Average bytes = ", (self.total_bytes / self.number_of_frames) 
        
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
        print "Written frame"

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
