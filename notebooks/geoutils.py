###############################################################################
#### Collection of useful functions
####
#### Licensed under MIT License
###############################################################################
#
# Copyright (c) 2020 Martin Christen, martin.christen@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

from urllib.request import urlopen
import os
import sys



def download(url, destfile, overwrite=True):
    print("Downloading", destfile, "from", url)

    if os.path.exists(destfile) and not overwrite:
        print("File already exists, not overwriting.")
        return
    
    response = urlopen(url) 
    info = response.info()
    cl = info["Content-Length"]
    
    if cl != None:
        filesize = int(cl)
        currentsize = 0
        
        with open(destfile, 'wb') as f:
            while True:
                chunk = response.read(16*1024)
                currentsize += len(chunk)
                
                if not chunk:
                    break
                f.write(chunk)
                percent = int(100*currentsize/filesize)
                
                bar = "*"*(percent)
                bar += "-"*((100-percent))
                print('\r{}% done \t[{}]'.format(percent, bar), end='')
        print("")
        
    else:
        print("Downloading please wait... (filesize unknown)")
        with open(destfile, 'wb') as f:
            while True:
                chunk = response.read(16*1024)
                if not chunk:
                    break
                f.write(chunk)
                

#------------------------------------------------------------------------------
# Fix DLL path in notebooks
# For proj4 we need to set the PROJ_LIB path manually
# Bug: https://github.com/jupyter/notebook/issues/4569


def fixenv():
    os.environ['PATH'] = os.path.split(sys.executable)[0] + "/Library/bin" + os.pathsep + os.environ['PATH'] 
    
    if 'PROJ_LIB' not in os.environ:
        os.environ['PROJ_LIB'] =  os.path.split(sys.executable)[0] + "/Library/share/proj" 

#------------------------------------------------------------------------------

