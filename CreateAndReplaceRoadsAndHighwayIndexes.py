#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tom
#
# Created:     02/04/2012
# Copyright:   (c) tom 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy, os

def RecreateIndexes(CenterlineSequence, CalibrationPoint, Route, RouteIDs):
    tableArray = [[CenterlineSequence, ['ROUTEID','NETWORKID','FROMDATE','TODATE']]]
    tableArray += [[CalibrationPoint, ['ROUTEID','NETWORKID','FROMDATE','TODATE', 'MEASURE']]]
    tableArray += [[Route, ['FROMDATE','TODATE'] + RouteIDs]]
    for indexGroup in tableArray:
        for fieldName in indexGroup[1]:
            tableName = os.path.basename(indexGroup[0])
            indexName = 'IX_%s' % (fieldName)
            if len(arcpy.ListIndexes(indexGroup[0],indexName)) == 1:
                arcpy.RemoveIndex_management(indexGroup[0], indexName)
            try:
                arcpy.AddIndex_management(indexGroup[0], fieldName, indexName)
                arcpy.AddMessage('Created index %s on field %s in table %s' % (indexName, fieldName, tableName))
            except:
                arcpy.AddWarning('Unable to create index %s on field %s in table %s' % (indexName, fieldName, tableName))

def main():
    #Parameter inputs
    CenterlineSequence = arcpy.GetParameterAsText(0)
    CalibrationPoint = arcpy.GetParameterAsText(1)
    Route = arcpy.GetParameterAsText(2)
    RouteIDs = arcpy.GetParameterAsText(3).split(';')
    RecreateIndexes(CenterlineSequence, CalibrationPoint, Route, RouteIDs)

if __name__ == '__main__':
    main()
