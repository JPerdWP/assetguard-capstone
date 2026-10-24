"""Build the final report from editable Markdown. Run from any directory."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,Flowable,Preformatted
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent
# Fonts shipped with ReportLab keep builds portable on Windows/macOS/Linux.
import reportlab
fontdir=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('Vera',str(fontdir/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Vera-Bold',str(fontdir/'VeraBd.ttf')))
pdfmetrics.registerFontFamily('Vera',normal='Vera',bold='Vera-Bold',italic='Vera',boldItalic='Vera-Bold')
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='BodyText2',fontName='Vera',fontSize=9.4,leading=14,spaceAfter=9,textColor=colors.HexColor('#253840')))
S.add(ParagraphStyle(name='H1x',fontName='Vera-Bold',fontSize=19,leading=25,spaceAfter=14,textColor=colors.HexColor('#12373d')))
S.add(ParagraphStyle(name='H2x',fontName='Vera-Bold',fontSize=12,leading=17,spaceAfter=9,spaceBefore=9,textColor=colors.HexColor('#087b72')))
S.add(ParagraphStyle(name='H3x',fontName='Vera-Bold',fontSize=10,leading=15,spaceAfter=8,spaceBefore=7))
S.add(ParagraphStyle(name='Cellx',fontName='Vera',fontSize=8,leading=11,spaceAfter=0))
S.add(ParagraphStyle(name='Captionx',fontName='Vera',fontSize=8,leading=11,spaceAfter=9,textColor=colors.HexColor('#61747d')))
S.add(ParagraphStyle(name='Codex',fontName='Courier',fontSize=8,leading=12,spaceAfter=10,backColor=colors.HexColor('#f0f4f6'),borderPadding=10))
class Diagram(Flowable):
    def __init__(self,kind):
        super().__init__();self.kind=kind;self.width=504;self.height=270 if kind=='architecture' else 260
    def draw(self):
        c=self.canv
        def box(x,y,w,h,title,lines):
            c.setFillColor(colors.HexColor('#f1f7f6'));c.setStrokeColor(colors.HexColor('#aac5c5'));c.roundRect(x,y,w,h,7,fill=1)
            c.setFillColor(colors.HexColor('#12373d'));c.setFont('Vera-Bold',10);c.drawString(x+12,y+h-23,title)
            c.setFont('Vera',8)
            for j,line in enumerate(lines):c.drawString(x+12,y+h-42-j*14,line)
        def arrow(x1,y1,x2,y2,label=None):
            c.setStrokeColor(colors.HexColor('#087b72'));c.setFillColor(colors.HexColor('#087b72'));c.setLineWidth(1.4);c.line(x1,y1,x2,y2)
            import math
            angle=math.atan2(y2-y1,x2-x1);p=c.beginPath();p.moveTo(x2,y2)
            p.lineTo(x2-7*math.cos(angle-.5),y2-7*math.sin(angle-.5));p.lineTo(x2-7*math.cos(angle+.5),y2-7*math.sin(angle+.5));p.close();c.drawPath(p,fill=1,stroke=0)
            if label:c.setFont('Vera',7);c.drawCentredString((x1+x2)/2,(y1+y2)/2+8,label)
        if self.kind=='architecture':
            box(4,164,150,83,'Browser',['HTML forms + local CSS','Administrator / viewer'])
            box(177,164,150,83,'Flask application',['Session / CSRF / roles','Validation + Jinja views'])
            box(350,164,150,83,'SQLite database',['Users / assets / issues','Activity + transactions'])
            arrow(154,204,177,204);arrow(327,204,350,204)
            box(80,24,344,100,'Write request flow',['1. Authenticate and authorize','2. Validate submitted fields and linked records','3. Commit record and activity event together','4. Redirect to updated read page'])
            arrow(252,164,252,124)
        else:
            box(4,150,225,100,'USERS',['PK id; username UNIQUE','password_hash; role'])
            box(275,150,225,100,'ASSETS',['PK id; tag UNIQUE','name; employee; os; support'])
            box(4,4,225,113,'ACTIVITY',['PK id; FK actor_id -> users','action; entity; entity_id','happened_at (UTC)'])
            box(275,4,225,113,'ISSUES',['PK id; FK asset_id -> assets','FK owner_id -> users','title; description; severity; status','reported_at; resolved_at; resolution'])
            arrow(110,150,110,117,'1 to many')
            arrow(390,150,390,117,'1 to many')
            arrow(229,175,275,95,'owns')
        c.setFont('Vera',7);c.setFillColor(colors.HexColor('#61747d'))

lines=(ROOT/'final_report_source.md').read_text().splitlines()
story=[];i=0
while i<len(lines):
    line=lines[i].strip()
    if not line:i+=1;continue
    if line=='\\pagebreak':story.append(PageBreak());i+=1;continue
    if line=='[ARCHITECTURE]':story.append(Diagram('architecture'));story.append(Spacer(1,10));i+=1;continue
    if line=='[DATABASE]':story.append(Diagram('database'));story.append(Spacer(1,10));i+=1;continue
    if line.startswith('```'):
        block=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
        story.append(Preformatted('\n'.join(block),S['Codex']));i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',x) for x in cells):rows.append([Paragraph(escape(x),S['Cellx']) for x in cells])
            i+=1
        n=len(rows[0]);widths=[135,369] if n==2 else [170,267,67]
        if n==3 and 'Executed cases' in rows[0][1].text:widths=[310,80,114]
        table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f2f1')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d3dfe1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.extend([table,Spacer(1,12)]);continue
    if line.startswith('!['):
        match=re.match(r'!\[(.*?)\]\((.*?)\)',line);caption,path=match.groups()
        img=Image(str(ROOT/path)); width=484
        # Two screens on the UI page share vertical space; individual form gets more space.
        if 'remediation' not in path:width=484
        img.drawHeight=img.imageHeight*width/img.imageWidth;img.drawWidth=width
        story.extend([img,Spacer(1,6),Paragraph(escape(caption),S['Captionx'])]);i+=1;continue
    level=len(line)-len(line.lstrip('#'))
    if level and line[level:level+1]==' ':
        story.append(Paragraph(escape(line[level+1:]),S[{1:'H1x',2:'H2x',3:'H3x'}.get(level,'H3x')]))
    else:
        story.append(Paragraph(escape(line),S['BodyText2']))
    i+=1

def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#d3dfe1'));c.line(54,43,558,43)
    c.setFont('Vera',8);c.setFillColor(colors.HexColor('#61747d'))
    c.drawString(54,29,'AssetGuard | CIT Capstone | John Paul Perdicaro');c.drawRightString(558,29,str(doc.page))
SimpleDocTemplate(str(ROOT/'Final_Project_Report.pdf'),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=42,bottomMargin=58,title='AssetGuard - CIT Capstone Final Project Report',author='John Paul Perdicaro (prepared with AI assistance)').build(story,onFirstPage=footer,onLaterPages=footer)
print(ROOT/'Final_Project_Report.pdf')
