#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import os
import tempfile
import string
import zipfile
from math import sin, cos, pi, fabs

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
import Plugins
import Errors
import TextDoc
import DrawDoc
import const
import FontScale

from intl import gettext as _

#-------------------------------------------------------------------------
#
# OpenDrawDoc
#
#-------------------------------------------------------------------------
class OpenDrawDoc(DrawDoc.DrawDoc):

    def __init__(self,styles,type,orientation):
        DrawDoc.DrawDoc.__init__(self,styles,type,orientation)
        self.f = None
        self.filename = None
        self.level = 0
        self.time = "0000-00-00T00:00:00"
	self.page = 0

    def open(self,filename):
        import time
        
        t = time.localtime(time.time())
        self.time = "%04d-%02d-%02dT%02d:%02d:%02d" % \
                    (t[0],t[1],t[2],t[3],t[4],t[5])

        if filename[-4:] != ".sxd":
            self.filename = filename + ".sxd"
        else:
            self.filename = filename

        try:
            self.content_xml = tempfile.mktemp()
            self.f = open(self.content_xml,"wb")
        except IOError,msg:
            errmsg = "%s\n%s" % (_("Could not create %s") % self.filename, msg)
            raise Errors.ReportError(errmsg)
        except:
            raise Errors.ReportError("Could not create %s" % self.filename)

        self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<office:document-content ')
        self.f.write('xmlns:office="http://openoffice.org/2000/office" ')
        self.f.write('xmlns:style="http://openoffice.org/2000/style" ')
        self.f.write('xmlns:text="http://openoffice.org/2000/text" ')
        self.f.write('xmlns:table="http://openoffice.org/2000/table" ')
        self.f.write('xmlns:draw="http://openoffice.org/2000/drawing" ')
        self.f.write('xmlns:fo="http://www.w3.org/1999/XSL/Format" ')
        self.f.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
        self.f.write('xmlns:number="http://openoffice.org/2000/datastyle" ')
        self.f.write('xmlns:svg="http://www.w3.org/2000/svg" ')
        self.f.write('xmlns:chart="http://openoffice.org/2000/chart" ')
        self.f.write('xmlns:dr3d="http://openoffice.org/2000/dr3d" ')
        self.f.write('xmlns:math="http://www.w3.org/1998/Math/MathML" ')
        self.f.write('xmlns:form="http://openoffice.org/2000/form" ')
        self.f.write('xmlns:script="http://openoffice.org/2000/script" ')
        self.f.write('office:class="text" office:version="0.9">\n')
        self.f.write('<office:script/>\n')
        self.f.write('<office:font-decls>\n')
        self.f.write('<style:font-decl style:name="Times New Roman" ')
        self.f.write('fo:font-family="&apos;Times New Roman&apos;" ')
        self.f.write('style:font-family-generic="roman" ')
        self.f.write('style:font-pitch="variable"/>\n')
        self.f.write('<style:font-decl style:name="Arial" ')
        self.f.write('fo:font-family="Arial" ')
        self.f.write('style:font-family-generic="swiss" ')
        self.f.write('style:font-pitch="variable"/>\n')
        self.f.write('</office:font-decls>\n')
        self.f.write('<office:automatic-styles>\n')
        self.f.write('<style:style style:name="GSuper" style:family="text">')
        self.f.write('<style:properties style:text-position="super 58%"/>')
	self.f.write('</style:style>\n')
	self.f.write('<style:style style:name="P1" style:family="paragraph">\n')
	self.f.write('<style:properties fo:margin-left="0cm" ')
	self.f.write('fo:margin-right="0cm" fo:text-indent="0cm"/>\n')
	self.f.write('</style:style>\n')
        for key in self.style_list.keys():
            style = self.style_list[key]
            self.f.write('<style:style style:name="T' + key + '" ')
            self.f.write('style:family="text">\n')
            self.f.write('<style:properties ')

            font = style.get_font()
            if font.get_type_face() == TextDoc.FONT_SANS_SERIF:
                self.f.write('fo:font-family="Arial" ')
            else:
                self.f.write('fo:font-family="&apos;Times New Roman&apos;" ')
            self.f.write('fo:font-size="' + str(font.get_size()) + 'pt" ')
            color = font.get_color()
	    self.f.write('fo:color="#%02x%02x%02x" ' % color)
            if font.get_bold():
                self.f.write('fo:font-weight="bold" ')
            if font.get_italic():
                self.f.write('fo:font-style="italic" ')
	    if font.get_underline():
		self.f.write('style:text-underline="single" ')
                self.f.write('style:text-underline-color="font-color" ')
            self.f.write('/>\n')
            self.f.write('</style:style>\n')
        self.f.write('</office:automatic-styles>\n')
        self.f.write('<office:body>\n')

    def close(self):
        self.f.write('</office:body>\n')
        self.f.write('</office:document-content>\n')
        self.f.close()
        try:
            self._write_styles_file()
            self._write_manifest()
            self._write_meta_file()
            self._write_zip()
        except:
            raise Errors.ReportError("Could not create %s" % self.filename)

        print self.print_req
        if self.print_req:
            os.environ["FILE"] = self.filename
            os.system ('/usr/bin/oodraw "$FILE" &')

    def _write_zip(self):
        
        file = zipfile.ZipFile(self.filename,"w",zipfile.ZIP_DEFLATED)
        file.write(self.manifest_xml,"META-INF/manifest.xml")
        file.write(self.content_xml,"content.xml")
        file.write(self.meta_xml,"meta.xml")
        file.write(self.styles_xml,"styles.xml")
        file.close()

        os.unlink(self.manifest_xml)
        os.unlink(self.content_xml)
        os.unlink(self.meta_xml)
        os.unlink(self.styles_xml)
        
    def _write_styles_file(self):
        self.styles_xml = tempfile.mktemp()
	self.f = open(self.styles_xml,"wb")
        self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<office:document-styles ')
        self.f.write('xmlns:office="http://openoffice.org/2000/office" ')
        self.f.write('xmlns:style="http://openoffice.org/2000/style" ')
        self.f.write('xmlns:text="http://openoffice.org/2000/text" ')
        self.f.write('xmlns:table="http://openoffice.org/2000/table" ')
        self.f.write('xmlns:draw="http://openoffice.org/2000/drawing" ')
        self.f.write('xmlns:fo="http://www.w3.org/1999/XSL/Format" ')
        self.f.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
        self.f.write('xmlns:number="http://openoffice.org/2000/datastyle" ')
        self.f.write('xmlns:svg="http://www.w3.org/2000/svg" ')
        self.f.write('xmlns:chart="http://openoffice.org/2000/chart" ')
        self.f.write('xmlns:dr3d="http://openoffice.org/2000/dr3d" ')
        self.f.write('xmlns:math="http://www.w3.org/1998/Math/MathML" ')
        self.f.write('xmlns:form="http://openoffice.org/2000/form" ')
        self.f.write('xmlns:script="http://openoffice.org/2000/script" ')
        self.f.write('office:class="text" office:version="0.9">\n')
        self.f.write('<office:font-decls>\n')
        self.f.write('<style:font-decl style:name="Times New Roman" ')
        self.f.write('fo:font-family="&apos;Times New Roman&apos;" ')
        self.f.write('style:font-family-generic="roman" ')
        self.f.write('style:font-pitch="variable"/>\n')
        self.f.write('<style:font-decl style:name="Arial" ')
        self.f.write('fo:font-family="Arial" ')
        self.f.write('style:font-family-generic="swiss" ')
        self.f.write('style:font-pitch="variable"/>\n')
        self.f.write('</office:font-decls>\n')

        self.f.write('<office:styles>\n')
	self.f.write('<draw:marker draw:name="Arrow" svg:viewBox="0 0 200 400"')
	self.f.write(' svg:d="m100 0 100 400h-200z"/>\n')
	self.f.write('<style:default-style style:family="graphics">\n')
	self.f.write('<style:properties fo:color="#000000" ')
	self.f.write('fo:font-family="&apos;Times New Roman&apos;" ')
	self.f.write('style:font-style-name="" style:font-family-generic="roman" ')
	self.f.write('style:font-pitch="variable" fo:font-size="24pt" ')
	self.f.write('fo:language="en" fo:country="US" ')
	self.f.write('style:line-break="strict"/>\n')
	self.f.write('</style:default-style>\n')

	self.f.write('<style:style style:name="standard" style:family="graphics">\n')
	self.f.write('svg:stroke-width="0cm" ')
	self.f.write('svg:stroke-color="#000000" ')
	self.f.write('draw:marker-start-width="0.3cm" ')
	self.f.write('draw:marker-start-center="false" ')
	self.f.write('draw:marker-end-width="0.3cm" ')
	self.f.write('draw:marker-end-center="false" ')
	self.f.write('draw:fill="solid" ')
	self.f.write('draw:fill-color="#00b8ff" ')
	self.f.write('draw:shadow="hidden" ')
	self.f.write('draw:shadow-offset-x="0.3cm" ')
	self.f.write('draw:shadow-offset-y="0.3cm" ')
	self.f.write('draw:shadow-color="#808080" ')
	self.f.write('fo:color="#000000" ')
	self.f.write('style:text-outline="false" ')
	self.f.write('style:text-crossing-out="none" ')
	self.f.write('fo:font-family="&apos;Times New Roman&apos;" ')
	self.f.write('style:font-style-name="" ')
	self.f.write('style:font-family-generic="roman" ')
	self.f.write('style:font-pitch="variable" ')
	self.f.write('fo:font-size="24pt" ')
	self.f.write('fo:font-style="normal" ')
	self.f.write('fo:text-shadow="none" ')
	self.f.write('style:text-underline="none" ')
	self.f.write('fo:font-weight="normal" ')
	self.f.write('fo:line-height="100%" ')
	self.f.write('fo:text-align="start" ')
	self.f.write('text:enable-numbering="false" ')
	self.f.write('fo:margin-left="0cm" ')
	self.f.write('fo:margin-right="0cm" ')
	self.f.write('fo:text-indent="0cm" ')
	self.f.write('fo:margin-top="0cm" ')
	self.f.write('fo:margin-bottom="0cm"/>\n')
	self.f.write('</style:style>\n')

	for style_name in self.draw_styles.keys():
            style = self.draw_styles[style_name]
            self.f.write('<style:style style:name="')
  	    self.f.write(style_name)
	    self.f.write('" style:family="graphics" ')
	    self.f.write('style:parent-style-name="standard">\n')
	    self.f.write('<style:properties ')
            if style.color[0] == 255 and style.color[1] == 255 and style.color[2] == 255:
                self.f.write('draw:fill="none" ')
            else:
                self.f.write('draw:fill="solid" ')

            self.f.write('draw:fill-color="#%02x%02x%02x" ' % style.get_fill_color())
                
            if style.get_line_style() == DrawDoc.DASHED:
                self.f.write('draw:color="#cccccc" ')
            else:
                self.f.write('draw:color="#%02x%02x%02x" ' % style.get_color())
                
            
            if style.get_line_width():
                self.f.write('draw:stroke="solid" ')
            else:
                self.f.write('draw:stroke="none" ')
            if style.get_shadow():
		self.f.write('draw:shadow="visible" ')
            else:
		self.f.write('draw:shadow="hidden" ')
	    self.f.write('/>\n')
  	    self.f.write('</style:style>\n')

        self.f.write('<style:style style:name="Standard" ')
        self.f.write('style:family="paragraph" style:class="text"/>\n')
        for key in self.style_list.keys():
            style = self.style_list[key]
            self.f.write('<style:style style:name="' + key + '" ')
            self.f.write('style:family="paragraph" ')
            self.f.write('style:parent-style-name="Standard" ')
            self.f.write('style:class="text">\n')
            self.f.write('<style:properties ')

            if style.get_padding() != 0.0:
	       self.f.write('fo:padding="%.3fcm" ' % style.get_padding())

            align = style.get_alignment()
	    if align == TextDoc.PARA_ALIGN_LEFT:
	       self.f.write('fo:text-align="left" ')
            elif align == TextDoc.PARA_ALIGN_RIGHT:
               self.f.write('fo:text-align="right" ')
            elif align == TextDoc.PARA_ALIGN_CENTER:
               self.f.write('fo:text-align="center" ')
               self.f.write('style:justify-single-word="false" ')
            else:
               self.f.write('fo:text-align="justify" ')
               self.f.write('style:justify-single-word="false" ')
            font = style.get_font()
            if font.get_type_face() == TextDoc.FONT_SANS_SERIF:
                self.f.write('style:font-name="Arial" ')
            else:
                self.f.write('style:font-name="Times New Roman" ')
            self.f.write('fo:font-size="' + str(font.get_size()) + 'pt" ')
            color = font.get_color()
	    self.f.write('fo:color="#%02x%02x%02x" ' % color)
            if font.get_bold():
                self.f.write('fo:font-weight="bold" ')
            if font.get_italic():
                self.f.write('fo:font-style="italic" ')
	    if font.get_underline():
		self.f.write('style:text-underline="single" ')
                self.f.write('style:text-underline-color="font-color" ')
            self.f.write('fo:text-indent="%.2fcm" ' % style.get_first_indent())
            self.f.write('fo:margin-right="%.2fcm" ' % style.get_right_margin())
            self.f.write('fo:margin-left="%.2fcm" ' % style.get_left_margin())
            self.f.write('fo:margin-top="0cm" ')
            self.f.write('fo:margin-bottom="0.212cm"')
            self.f.write('/>\n')
            self.f.write('</style:style>\n')

	# Current no leading number format for headers
            
        self.f.write('</office:styles>\n')
        self.f.write('<office:automatic-styles>\n')
        self.f.write('<style:page-master style:name="PM0">\n')
        self.f.write('<style:properties fo:page-width="%.2fcm" ' % self.width)
        self.f.write('fo:page-height="%.2fcm" ' % self.height)
        self.f.write('style:num-format="1" ')
        if self.orientation == TextDoc.PAPER_PORTRAIT:
            self.f.write('style:print-orientation="portrait" ')
        else:
            self.f.write('style:print-orientation="landscape" ')
        self.f.write('fo:margin-top="%.2fcm" ' % self.tmargin)
        self.f.write('fo:margin-bottom="%.2fcm" ' % self.bmargin)
        self.f.write('fo:margin-left="%.2fcm" ' % self.lmargin)
        self.f.write('fo:margin-right="%.2fcm"/>\n' % self.rmargin)
        self.f.write('</style:page-master>\n')
	self.f.write('<style:style style:name="dp1" style:family="drawing-page">\n')
	self.f.write('<style:properties draw:background-size="border" draw:fill="none"/>\n')
	self.f.write('</style:style>\n')
        self.f.write('</office:automatic-styles>\n')
	self.f.write('<office:master-styles>\n')
	self.f.write('<draw:layer-set>\n')
	self.f.write('<draw:layer draw:name="layout" draw:locked="false" ')
	self.f.write('draw:printable="true" draw:visible="true"/>\n')
	self.f.write('<draw:layer draw:name="background" draw:locked="false" ')
	self.f.write('draw:printable="true" draw:visible="true"/>\n')
	self.f.write('<draw:layer draw:name="backgroundobjects" ')
	self.f.write('draw:locked="false" draw:printable="true" draw:visible="true"/>\n')
	self.f.write('<draw:layer draw:name="controls" draw:locked="false" ')
	self.f.write('draw:printable="true" draw:visible="true"/>\n')
	self.f.write('<draw:layer draw:name="measurelines" draw:locked="false" ')
	self.f.write('draw:printable="true" draw:visible="true"/>\n')
	self.f.write('</draw:layer-set>\n')
	self.f.write('<style:master-page style:name="Home" ')
	self.f.write('style:page-master-name="PM0" draw:style-name="dp1"/>\n')
	self.f.write('</office:master-styles>\n')
	self.f.close()
        
    def start_paragraph(self,style_name):
	self.f.write('<text:p text:style-name="%s">' % style_name)

    def end_paragraph(self):
        self.f.write('</text:p>\n')

    def write_text(self,text):
        text = text.replace('&','&amp;');       # Must be first
        text = text.replace('\t','<text:tab-stop/>')
        text = text.replace('\n','<text:line-break/>')
        text = text.replace('<','&lt;');
        text = text.replace('>','&gt;');
        text = text.replace('&lt;super&gt;','<text:span text:style-name="GSuper">')
        text = text.replace('&lt;/super&gt;','</text:span>')
	self.f.write(text)

    def _write_manifest(self):
        self.manifest_xml = tempfile.mktemp()
	self.f = open(self.manifest_xml,"wb")
	self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	self.f.write('<manifest:manifest ')
        self.f.write('xmlns:manifest="http://openoffice.org/2001/manifest">')
	self.f.write('<manifest:file-entry ')
        self.f.write('manifest:media-type="application/vnd.sun.xml.draw" ')
	self.f.write('manifest:full-path="/"/>')
        self.f.write('<manifest:file-entry manifest:media-type="" ')
	self.f.write('manifest:full-path="Pictures/"/>')
	self.f.write('<manifest:file-entry manifest:media-type="text/xml" ')
	self.f.write('manifest:full-path="content.xml"/>')
	self.f.write('<manifest:file-entry manifest:media-type="text/xml" ')
	self.f.write('manifest:full-path="styles.xml"/>')
	self.f.write('<manifest:file-entry manifest:media-type="text/xml" ')
	self.f.write('manifest:full-path="meta.xml"/>')
	#self.f.write('<manifest:file-entry manifest:media-type="text/xml" ')
	#self.f.write('manifest:full-path="settings.xml"/>')
	self.f.write('</manifest:manifest>\n')
	self.f.close()

    def _write_meta_file(self):
        name = self.name
        self.meta_xml = tempfile.mktemp()
	self.f = open(self.meta_xml,"wb")
	self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	self.f.write('<office:document-meta ')
	self.f.write('xmlns:office="http://openoffice.org/2000/office" ')
	self.f.write('xmlns:xlink="http://www.w3.org/1999/xlink" ')
	self.f.write('xmlns:dc="http://purl.org/dc/elements/1.1/" ')
	self.f.write('xmlns:meta="http://openoffice.org/2000/meta" ')
	self.f.write('office:class="text" office:version="0.9">\n');
	self.f.write('<office:meta>\n')
	self.f.write('<meta:generator>')
        self.f.write(const.progName + ' ' + const.version)
        self.f.write('</meta:generator>\n')
	self.f.write('<meta:initial-creator>')
	self.f.write(name)
	self.f.write('</meta:initial-creator>\n')
	self.f.write('<meta:creation-date>')
	self.f.write(self.time)
	self.f.write('</meta:creation-date>\n')
	self.f.write('<dc:creator>')
	self.f.write(name)
	self.f.write('</dc:creator>\n')
	self.f.write('<dc:date>')
	self.f.write(self.time)
	self.f.write('</dc:date>\n')
	self.f.write('<meta:print-date>0-00-00T00:00:00</meta:print-date>\n')
	self.f.write('<dc:language>en-US</dc:language>\n')
	self.f.write('<meta:editing-cycles>1</meta:editing-cycles>\n')
	self.f.write('<meta:editing-duration>PT0S</meta:editing-duration>\n')
	self.f.write('<meta:user-defined meta:name="Info 0"/>\n')
	self.f.write('<meta:user-defined meta:name="Info 1"/>\n')
	self.f.write('<meta:user-defined meta:name="Info 2"/>\n')
	self.f.write('<meta:user-defined meta:name="Info 3"/>\n')
	self.f.write('</office:meta>\n')
	self.f.write('</office:document-meta>\n')
	self.f.close()

    def start_page(self,orientation=None):
	self.page = self.page + 1
	self.f.write('<draw:page draw:name="page%d" ' % self.page)
	self.f.write('draw:master-page-name="Home">\n')

    def end_page(self):
	self.f.write('</draw:page>\n')

    def rotate_text(self,style,text,x,y,angle):

        stype = self.draw_styles[style]
        pname = stype.get_paragraph_style()
        p = self.style_list[pname]
	font = p.get_font()
        size = font.get_size()

        height = size*(len(text))
        width = 0
        for line in text:
            width = max(width,FontScale.string_width(font,line))
        wcm = (width/72.0)*2.54
        hcm = (height/72.0)*2.54

        rangle = -((pi/180.0) * angle)

        self.f.write('<draw:text-box draw:style-name="%s" ' % style)
        self.f.write('draw:layer="layout" svg:width="%.3fcm" ' % wcm)
        self.f.write('svg:height="%.3fpt" ' % hcm)
        self.f.write('draw:transform="rotate (%.8f) ' % rangle)
        xloc = x-((wcm/2.0)*cos(-rangle)) + self.lmargin
        yloc = y-((hcm)*sin(-rangle)) + self.tmargin
        self.f.write('translate (%.3fcm %.3fcm)"' % (xloc,yloc))
        self.f.write('>')
        self.f.write('<text:p><text:span text:style-name="T%s">' % pname)
        self.write_text(string.join(text,'\n'))
        self.f.write('</text:span></text:p></draw:text-box>\n')

    def draw_path(self,style,path):
        stype = self.draw_styles[style]

        minx = 9e12
        miny = 9e12
        maxx = 0
        maxy = 0

        for point in path:
            minx = min(point[0],minx)
            miny = min(point[1],miny)
            maxx = max(point[0],maxx)
            maxy = max(point[1],maxy)

        self.f.write('<draw:polygon draw:style-name="%s" draw:layer="layout" ' % style)
        x = int((minx+self.lmargin)*1000)
        y = int((miny+self.tmargin)*1000)
        
        self.f.write('svg:x="%d" svg:y="%d" ' % (x,y))
        self.f.write('svg:viewBox="0 0 %d %d" ' % (int(maxx-minx)*1000,int(maxy-miny)*1000))
        self.f.write('svg:width="%.4fcm" ' % (maxx-minx))
        self.f.write('svg:height="%.4fcm" ' % (maxy-miny))
        
        point = path[0]
        x1 = int((point[0]-minx)*1000)
        y1 = int((point[1]-miny)*1000)
        self.f.write('draw:points="%d,%d' % (x1,y1))

        for point in path[1:]:
            x1 = int((point[0]-minx)*1000)
            y1 = int((point[1]-miny)*1000)
            self.f.write(' %d,%d' % (x1,y1))
        self.f.write('"/>\n')

    def draw_line(self,style,x1,y1,x2,y2):
        x1 = x1 + self.lmargin
        x2 = x2 + self.lmargin
        y1 = y1 + self.tmargin
        y2 = y2 + self.tmargin
	box_style = self.draw_styles[style]

        self.f.write('<draw:line draw:style="')
        self.f.write(style)
        self.f.write('" svg:x1="%.3fcm" ' % x1)
        self.f.write('svg:y1="%.3fcm" ' % y1)
        self.f.write('svg:x2="%.3fcm" ' % x2)
        self.f.write('svg:y2="%.3fcm" ' % y2)
        self.f.write('/>\n')

    def draw_text(self,style,text,x,y):
        x = x + self.lmargin
        y = y + self.tmargin
	box_style = self.draw_styles[style]
	para_name = box_style.get_paragraph_style()

        pstyle = self.style_list[para_name]
        font = pstyle.get_font()
        sw = FontScale.string_width(font,text)*1.3

	self.f.write('<draw:text-box draw:style-name="')
	self.f.write(style)
	self.f.write('" draw:layer="layout" ')
        # fix this
	self.f.write('svg:width="%.3fcm" ' % sw)
	self.f.write('svg:height="%.4fpt" ' % (font.get_size()*1.4))

	self.f.write('svg:x="%.3fcm" ' % float(x))
        self.f.write('svg:y="%.3fcm">' % float(y))
        self.f.write('<text:p text:style-name="P1">')
        self.f.write('<text:span text:style-name="T%s">' % para_name)
        self.f.write(text)
        self.f.write('</text:span></text:p>')
        self.f.write('</draw:text-box>\n')

    def draw_bar(self,style,x,y,x2,y2):
        x = x + self.lmargin
        x2 = x2 + self.lmargin
        y = y + self.tmargin
        y2 = y2 + self.tmargin

	box_style = self.draw_styles[style]
	para_name = box_style.get_paragraph_style()

	self.f.write('<draw:rect draw:style-name="')
	self.f.write(style)
	self.f.write('" draw:layer="layout" ')
	self.f.write('svg:width="%.3fcm" ' % float(x2-x))
	self.f.write('svg:height="%.3fcm" ' % float(y2-y))
	self.f.write('svg:x="%.3fcm" ' % float(x))
        self.f.write('svg:y="%.3fcm">' % float(y))
        self.f.write('</draw:rect>\n')

    def draw_box(self,style,text,x,y):
        x = x + self.lmargin
        y = y + self.tmargin
	box_style = self.draw_styles[style]
	para_name = box_style.get_paragraph_style()

	self.f.write('<draw:rect draw:style-name="')
	self.f.write(style)
	self.f.write('" draw:layer="layout" ')
	self.f.write('svg:width="%.3fcm" ' % box_style.get_width())
	self.f.write('svg:height="%.3fcm" ' % box_style.get_height())
	self.f.write('svg:x="%.3fcm" ' % float(x))
        self.f.write('svg:y="%.3fcm"' % float(y))
	if text != "":
            text = string.replace(text,'\t','<text:tab-stop/>')
            text = string.replace(text,'\n','<text:line-break/>')
            self.f.write('>\n')
  	    self.f.write('<text:p text:style-name="P1">')
	    self.f.write('<text:span text:style-name="T%s">' % para_name)
	    self.f.write(text)
            self.f.write('</text:span></text:p>\n')
            self.f.write('</draw:rect>\n')
        else:
            self.f.write('/>\n')

#-------------------------------------------------------------------------
#
# Register document generator
#
#-------------------------------------------------------------------------
print_label = None
if os.access ("/usr/bin/oodraw", os.X_OK):
    print_label = _("Open in OpenOffice.org")

Plugins.register_draw_doc(_("OpenOffice.org Draw"),OpenDrawDoc,1,1,".sxd",
                          print_label);
