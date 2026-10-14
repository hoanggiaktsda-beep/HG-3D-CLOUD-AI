"""Synthetic technical drawing, not a customer drawing or rendered 3D image."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path(__file__).parent
im=Image.new('RGB',(1400,1100),'white');d=ImageDraw.Draw(im)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42)
for i,t in enumerate(['TEST CABINET - SYNTHETIC DRAWING','WIDTH 1800 mm','DEPTH 450 mm','HEIGHT 900 mm']):
 d.text((70,50+i*90),t,fill='black',font=f)
d.rectangle((150,500,1150,1000),outline='black',width=4)
d.text((150,430),'FRONT - OUTER ENVELOPE ONLY',fill='black',font=f)
im.save(root/'dimensioned_cabinet.png')
