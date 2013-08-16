import os
import re
import multiprocessing
import arcpy

#arcpy.ImportToolbox(r'C:\Program Files (x86)\Common Files\Esri\Roads and Highways\ToolBoxes\Roads And Highways Tools.tbx')

def splitArray(arr, count):
     return [arr[i::count] for i in range(count)]


def generateRouteCalibration(fc, outFolder, counter, routeIDFieldName, routeIDRange):
    layerName = os.path.basename(fc) + str(counter)
    newRouteLayer = layerName + '_route'
    queryString = '('
    for q in routeIDRange:
        queryString += '\'%s\',' % q
    queryString = queryString[0:len(queryString) - 1] + ')'
    whereClause = '%s IN %s' % (routeIDFieldName, queryString)
    arcpy.MakeFeatureLayer_management(fc, layerName, whereClause)
    #arcpy.SelectLayerByAttribute_management(layerName, 'NEW_SELECTION', '%s IN %s' % (routeIDFieldName, queryString))
    outShapeFile = arcpy.CreateScratchName(layerName,'','Shapefile', outFolder)
    outCalibrationSF = arcpy.CreateScratchName(layerName + '_cal','','Shapefile', outFolder)
    print 'Creating ' + outShapeFile
    arcpy.CopyFeatures_management(layerName, outShapeFile)
    print 'Created ' + outShapeFile
    #arcpy.MakeFeatureLayer_management(outShapeFile, newRouteLayer)
    #arcpy.GenerateCalibrationPoints_roads(newRouteLayer,"Rte_Id","M_ON_ROUTE_2D",outCalibrationSF)
    return outShapeFile

def main():
  # Create a pool class and run the jobs?the number of jobs is equal to the number of processors
    try:
        row, rows = None, None
        inFC = r'C:\GIS_DATA\DOT\CalibrationPointEventsEvents.lyr';
        outFolder = r'C:\GIS_DATA\DOT\CalPoints';
        routeIDFieldName = 'RouteId'

        tempFrequencyTable = 'IN_MEMORY/RouteFrq1'
        arcpy.Frequency_analysis(inFC,tempFrequencyTable,routeIDFieldName)
        rows = arcpy.SearchCursor(tempFrequencyTable)
        routeIDList = []
        for row in rows:
            routeIDList += [row.getValue(routeIDFieldName)]

        routeIDChunks = splitArray(routeIDList, multiprocessing.cpu_count())
        results = []
        pool = multiprocessing.Pool()
        counter = 0
        for chunk in routeIDChunks:
            print "Submitted job " + str(counter)
            #Async call
            results += [pool.apply_async(generateRouteCalibration, (inFC, outFolder, counter, routeIDFieldName, chunk, ))]
            #synchronous call
            #results += [generateRouteCalibration(inFC, outFolder, counter, routeIDFieldName, chunk)]
            counter += 1
        #pool.map(generateRouteCalibration, routeIDList, multiprocessing.cpu_count())
    finally:
        if pool:
            pool.close()
            pool.join()
        if row:
            del row
        if rows:
            del rows
    for result in results:
        print result.get(1)
        #print result


  # Synchronize the main process with the job processes to ensure proper cleanup.

# End main
if __name__ == '__main__':
    main()
