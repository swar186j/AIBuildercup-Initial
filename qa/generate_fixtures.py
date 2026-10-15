"""Generate explicitly fictional documents without identity numbers."""
from pathlib import Path
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parent/'fixtures'
OUT.mkdir(exist_ok=True)
for kind,name,address in [('aadhaar','Rahul Kumar Sharma','12 MG Road, Pune, Maharashtra'),('pan','Rahul K Sharma',''),('address','Rahul Kumar Sharma','45 FC Road, Pune, Maharashtra')]:
    lines=['FICTIONAL TEST DOCUMENT - NOT VALID',kind.upper()+' SAMPLE', 'Name: '+name,'DOB: 1998-06-15']
    if address: lines.append('Address: '+address)
    lines.append('Synthetic QA fixture. No identity number. No official validity.')
    c=canvas.Canvas(str(OUT/f'fictional_{kind}.pdf'),pagesize=(640,360))
    c.setFillColorRGB(.12,.25,.4)
    for i,line in enumerate(lines):
        c.setFont('Helvetica-Bold' if i<2 else 'Helvetica',16 if i<2 else 12)
        c.drawString(30,320-i*42,line)
    c.save()
    im=Image.new('RGB',(1000,430),'white');d=ImageDraw.Draw(im)
    for i,line in enumerate(lines): d.text((25,25+i*60),line,fill='navy',font_size=24)
    im.save(OUT/f'fictional_{kind}.png')
    im.save(OUT/f'fictional_{kind}.jpg')
