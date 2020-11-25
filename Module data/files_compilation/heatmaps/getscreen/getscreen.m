function image = getscreen
% GETSCREEN captures the screen and returns a struct that could be used to
% make videos or written to an image file using the imwrite. 
% For example:
% a = getscreen
% imwrite(a.cdata,'screen.jpg');
% To make a video
% vidObj = VideoWriter('Testvideo.avi');
% open(vidObj);
% for n = 1:100
%     image = getframe(gcf);
%     writeVideo(vidObj,image);
% end
% close(vidObj)
% Author: Lateef Adewale Kareem
robo = java.awt.Robot;
t = java.awt.Toolkit.getDefaultToolkit();
rectangle = java.awt.Rectangle(t.getScreenSize());
imagedata = robo.createScreenCapture(rectangle);
h = imagedata.getHeight();
w = imagedata.getWidth();
data = imagedata.getData();
pix = data.getPixels(0,0,w,h,[]);
tmp = uint8(reshape(pix(:),3,w,h));
for i = 1:3
    image.cdata(:,:,i) = squeeze(tmp(i,:,:))';
end
image.colormap = [];