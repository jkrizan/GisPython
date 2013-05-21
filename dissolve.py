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

def dissolve1():
    
    inshape=r'E:\WORK\RAZNO\lpis\lpis_inicijalni.shp'
    codes=[210,400,424,900,421,422,420,320,310,490,410,500,300,200]
    outshape=r'E:\WORK\RAZNO\lpis\lpis_diss_cus.shp'
    
    c = fiona.collection(inshape, "r")
    driver=c.driver
    crs=c.crs
    geom=[]
    value=[]
    zup=[]
    
    print 'Reading ...'
    for i,f in enumerate(c):
        if i%1000 == 0:
            print i
        geom.append(shape(f['geometry']).simplify(1.0))
        value.append(f['properties']['KOR_ZEM'])
        zup.append(f['properties']['ZUPANIJA'])
    print 'Done.'
    
    geom = np.array(geom)
    value=np.array(value)
    zup=np.array(zup)
    zupu=np.unique(zup)
    
    i=0
    rec={'geometry':{'coordinates':None,'type':'Polygon'},'properties':{'kor_zem':None}}
    schema={'geometry':'Polygon','properties':{'kor_zem':'int'}}
    with fiona.open(outshape,'w',driver,schema,crs) as out:   
        for code in codes:
            for z in zupu:
                print code #, z
                sub_c=geom[(value==code)&(zup==z)]#[shape(f['geometry']) for f in c if f['KOR_ZEM']==code]
                print ' have {} records ...'.format(len(sub_c))
                ta = time.time()
                u = cascaded_union(sub_c)
                print 'Union in {} secs'.format(time.time()-ta)
                if u.type=='Polygon':
                    u=[u]
                for f in u:
                    i+=1
                    if i%1000==0:
                        print 'Writing record {}'.format(i)
                    #gg=[[coord for coord in f.exterior.coords]]
                    #for ii in f.interiors:
                    #    gg.append([coord for coord in ii.coords])
                    gg=mapping(f)
                    rec['geometry']['coordinates']=gg
                    rec['properties']['kor_zem']=code
                    out.write(rec)
                    
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
    
def dissolve2(inshape,outshape,nx=5,ny=5):
     
    c = fiona.open(inshape, "r")
    driver=c.driver
    crs=c.crs
    
    covers=[]
    dx=(c.bounds[2]-c.bounds[0])/nx
    dy=(c.bounds[3]-c.bounds[1])/ny
    for i in range(nx):
        for j in range(ny):
            bbox=(c.bounds[0]+dx*i,c.bounds[1]+dy*j,c.bounds[0]+dx*(i+1),c.bounds[1]+dy*(j+1))
            bbox=shapely.geometry.box(*bbox)
            covers.append(bbox)
    c.close()
    
    inters_geom=[]
    inters_code=[]
    i=0
    rec={'geometry':{'coordinates':None,'type':'Polygon'},'properties':{'kor_zem':None}}
    schema={'geometry':'Polygon','properties':{'kor_zem':'int'}}
    with fiona.open(outshape,'w',driver,schema,crs) as out:
        for ci,cover in enumerate(covers):
            geom,value=read_from_cover(inshape,cover.bounds)
            print 'cover {}. {} shapes'.format(ci,len(geom))
            codes=np.unique(value)
            for code in codes:
                sub_c=geom[(value==code)]#[shape(f['geometry']) for f in c if f['KOR_ZEM']==code]
                print '  code {} have {} records ...'.format(code,len(sub_c))
                sys.stdout.flush()
                ta = time.time()
                sub_c=shapely.geometry.MultiPolygon(sub_c) #u = shapely.ops.unary_union(sub_c)#cascaded_union(sub_c)
                u=sub_c.buffer(0.01)
                print '  union in {} secs'.format(time.time()-ta)
                if u.type=='Polygon':
                    u=[u]
                for f in u:
                    if f.intersects(cover.boundary):    # Ako sijeće ....
                        inters_geom.append(f)
                        inters_code.append(code)
                    else:          
                        i+=1
                        if i%100==0:
                            print 'Writing record {}'.format(i)
                        gg=mapping(f.simplify(0.1))
                        rec['geometry']=gg
                        rec['properties']['kor_zem']=int(code)
                        out.write(rec)   
        print '{} polygons on intersections'.format(len(inters_geom))
        geom=np.array(inters_geom)
        value=np.array(inters_code)
        codes=np.unique(value)
        for code in codes:
            sub_c=geom[(value==code)]#[shape(f['geometry']) for f in c if f['KOR_ZEM']==code]
            print '  code {} have {} records ...'.format(code,len(sub_c))
            ta = time.time()
            u=shapely.geometry.MultiPolygon(sub_c).buffer(0.01)#u = cascaded_union(sub_c)
            print '  union in {} secs'.format(time.time()-ta)
            if u.type=='Polygon':
                u=[u]
            for f in u:      
                i+=1
                if i%1000==0:
                    print 'Writing record {}'.format(i)
                gg=mapping(f.simplify(0.1))
                rec['geometry']=gg
                rec['properties']['kor_zem']=int(code)
                out.write(rec)
    
if __name__=='__main__':

    inshape=r'E:\WORK\RAZNO\lpis\lpis_inicijalni.shp'
    outshape=r'E:\WORK\RAZNO\lpis\lpis_diss_3.shp'
    dissolve2(inshape,outshape,nx=10,ny=10)
	#nx=5
    #ny=5

    #inshape=r'E:\WORK\RAZNO\lpis\lpis_test.shp'
    #outshape=r'E:\WORK\RAZNO\lpis\lpis_test_diss.shp'
    #dissolve2(inshape,outshape,nx=1,ny=1)
    
    