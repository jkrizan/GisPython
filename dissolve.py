# -*- coding: utf-8 -*-
"""
Created on Mon May 13 23:45:54 2013

@author: josip
"""

import fiona
import shapely
from shapely.geometry import shape,mapping
from shapely.ops import cascaded_union
import time
import numpy as np
import sys

def read_from_cover(filename,bbox):
    c = fiona.open(filename, "r")
    geom=[]; value=[]
    print 'Reading ...'
    for i,f in enumerate(c.filter(bbox)):
        if i%1000 == 0:
            print i
        geom.append(shape(f['geometry']))
        value.append(f['properties']['KOR_ZEM'])
    c.close()
    print 'Done.'
    return np.array(geom),np.array(value)
    
def dissolve(inshape,dissolve_attrib,outshape,nx=5,ny=5,buffer_distance=0,simplify_tolerance=0):
    """
    Dissolves inshape with respect to dissolve_attrib and saves output to outshape.
    Algorithm is designed for very large number of polygons (verified on 800000).
    nx, ny -- number of divisions on x and y axes
    buffer_distance -- distance of buffer applied to collection of polygons
    simplify_tolerance -- tolerance for simplify function applied on unioned polygons
                    before saving to output shape
    """
    # read input vector
    c = fiona.open(inshape, "r")
    driver=c.driver
    crs=c.crs
    
    # calculate covers of entire shape
    covers=[]
    dx=(c.bounds[2]-c.bounds[0])/nx
    dy=(c.bounds[3]-c.bounds[1])/ny
    for i in range(nx):
        for j in range(ny):
            bbox=(c.bounds[0]+dx*i,c.bounds[1]+dy*j,c.bounds[0]+dx*(i+1),c.bounds[1]+dy*(j+1))
            bbox=shapely.geometry.box(*bbox)
            covers.append(bbox)
    c.close()
    
    inters_geom=[]  # geometries which intersects boundary of covers
    inters_code=[]  # codes of that geometries
    i=0
    rec={'geometry':{'coordinates':None,'type':'Polygon'},'properties':{dissolve_attrib:None}}
    schema={'geometry':'Polygon','properties':{dissolve_attrib:'int'}}
    with fiona.open(outshape,'w',driver,schema,crs) as out:
        for ci,cover in enumerate(covers):
            geom,value=read_from_cover(inshape,cover.bounds)
            print 'cover {}. {} shapes'.format(ci,len(geom))
            codes=np.unique(value)
            for code in codes:
                sub_c=geom[(value==code)]
                print '  code {} have {} records ...'.format(code,len(sub_c))
                #sys.stdout.flush()
                #ta = time.time()
                sub_c=shapely.geometry.MultiPolygon(sub_c) #u = shapely.ops.unary_union(sub_c)#cascaded_union(sub_c)
                u=sub_c.buffer(buffer_distance)
                #print '  union in {} secs'.format(time.time()-ta)
                if u.type=='Polygon': #Only one polygon
                    u=[u]
                for f in u:
                    if f.intersects(cover.boundary):    # If polygon intersetcs cover boundary
                        inters_geom.append(f)
                        inters_code.append(code)
                    else:          
                        i+=1
                        if i%1000==0:
                            print 'Writing record {}'.format(i)
                        if simplify_tolerance>0.0:
                            f=f.simplify(simplify_tolerance)
                        gg=mapping(f)
                        rec['geometry']=gg
                        rec['properties'][dissolve_attrib]=int(code)
                        out.write(rec)   
        print '{} polygons on intersections'.format(len(inters_geom))
        geom=np.array(inters_geom)
        value=np.array(inters_code)
        codes=np.unique(value)
        for code in codes:
            sub_c=geom[(value==code)]
            print '  code {} have {} records ...'.format(code,len(sub_c))
            #ta = time.time()
            u=shapely.geometry.MultiPolygon(sub_c).buffer(buffer_distance) #u = cascaded_union(sub_c)
            #print '  union in {} secs'.format(time.time()-ta)
            if u.type=='Polygon':
                u=[u]
            for f in u:      
                i+=1
                if i%1000==0:
                    print 'Writing record {}'.format(i)
                if simplify_tolerance>0.0:
                    f=f.simplify(simplify_tolerance)
                gg=mapping(f)
                rec['geometry']=gg
                rec['properties']['kor_zem']=int(code)
                out.write(rec)
    
if __name__=='__main__':

    inshape=r'E:\WORK\RAZNO\lpis\lpis_inicijalni.shp'
    outshape=r'E:\WORK\RAZNO\lpis\lpis_diss_3.shp'
    dissolve(inshape,outshape,nx=10,ny=10)
	#nx=5
    #ny=5

    #inshape=r'E:\WORK\RAZNO\lpis\lpis_test.shp'
    #outshape=r'E:\WORK\RAZNO\lpis\lpis_test_diss.shp'
    #dissolve2(inshape,outshape,nx=1,ny=1)
    
    