#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tom
#
# Created:     06/08/2012
# Copyright:   (c) tom 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy, os, sys, traceback, GenerateRAndHSchema, CreateAndReplaceRoadsAndHighwayIndexes as idx, string, uuid

##def isItemInList(testList, testVale):
##    try:
##        testList.index(testVale)
##        return True
##    except:
##        return False

def addMissingFieldsToTarget(inputTable, targetTable, excludeList): #For the purpose of loading data from inputTable to targetTable
    returnFields = []
    targetDesc = arcpy.Describe(targetTable)
    inputDesc = arcpy.Describe(inputTable)
    for field in inputDesc.fields:
        if field.type != 'OID' and field.type != 'Geometry' and field.name != 'Shape_Length' and field.name != 'OBJECTID':
            if not field.name in excludeList:
                ##arcpy.AddMessage('Adding field ' + field.name + ' of type ' + field.type)
                returnFields += [field.name]
                if field.name in targetDesc.fields:
                    arcpy.DeleteField_management(targetTable, field.name)
                ##if not field.name in targetDesc.fields:
                try:
                    arcpy.AddField_management(targetTable, field.name, field.type, field.precision, field.scale, field.length, field.aliasName)
                except:
                    arcpy.AddWarning('Unable to add field ' + field.name + ' to ' + targetTable)
    return returnFields

def main():
    try:
        outGDBFullPath = arcpy.GetParameterAsText(0)
##        outGDBName = arcpy.GetParameterAsText(1)
        inputFC= arcpy.GetParameterAsText(1)
        routeFieldName = arcpy.GetParameterAsText(2)
        fromDateField = arcpy.GetParameterAsText(3)
        toDateField = arcpy.GetParameterAsText(4)
        defaultFromDate = arcpy.GetParameterAsText(5)
        inputCalibrationFC = arcpy.GetParameterAsText(6)
        inputCalibrationMField = arcpy.GetParameterAsText(7)
        lrsNetworks = [arcpy.GetParameterAsText(8)]

        inputDsc = arcpy.Describe(inputFC)
        sr = inputDsc.spatialReference

        #Get the route ID field from the source so we can create the schema using the same field length
        routeField = arcpy.ListFields(inputFC, routeFieldName)[0]
        lrsActivities = ['Calibrate Route', 'Cartographic Realignment', 'Create Route', 'Extend Route', 'Realign Gap Route', 'Realign Overlapping Route', 'Realign Route', 'Reassign Route', 'Retire Route', 'Reverse Route', 'Shorten Route']

        arcpy.AddMessage('Creating Roads and Highways schema')
        GenerateRAndHSchema.makeALRS(outGDBFullPath,sr,lrsNetworks, lrsActivities, routeField.length)
        tempFC = os.path.join(outGDBFullPath, 'TempInput')
        routeTable = os.path.join(outGDBFullPath, 'Route')
        centerlineFC = os.path.join(outGDBFullPath, 'Centerline')
        centerlineSequence = os.path.join(outGDBFullPath, 'CenterlineSequence')
        calibrationPoint = os.path.join(outGDBFullPath, 'CalibrationPoint')
        #Delete the routeID from the route and calibration point feature classes so they can take on the route ID of the source
        arcpy.DeleteField_management(routeTable, ['ROUTEID'])
        arcpy.AddField_management(centerlineFC,"ROADWAYIDGUID","GUID")
        arcpy.AddField_management(centerlineSequence,"ROADWAYIDGUID","GUID")

        upperInputFieldNames = []
        for field in inputDsc.fields:
            upperInputFieldNames += [field.name.upper()]
        if 'ROUTENAME' in upperInputFieldNames:
            arcpy.DeleteField_management(routeTable, ['ROUTENAME'])
            arcpy.AddMessage('Deleted ROUTENAME')
        arcpy.DeleteField_management(calibrationPoint, ['ROUTEID'])

        arcpy.AddMessage('Loading routes')
        routeFields = addMissingFieldsToTarget(inputFC, routeTable, [fromDateField, toDateField])
        inFeatures = arcpy.SearchCursor(inputFC)
        routeTableCursor = arcpy.InsertCursor(routeTable)
        cCursor = arcpy.InsertCursor(centerlineFC)
        csCursor = arcpy.InsertCursor(centerlineSequence)
        arcpy.AddMessage('Writing routes.')
        x = 1
        try:
            for feature in inFeatures:
                arcpy.AddMessage('Loading route with RouteID ' + str(feature.getValue(routeFieldName)))
                guid = '{' + str(uuid.uuid4()) + '}'
                newRoute = routeTableCursor.newRow()
                for field in routeFields:
                    newRoute.setValue(field, feature.getValue(field))
                if fromDateField is not None and fromDateField != '' and fromDateField != '#':
                    newRoute.FROMDATE = feature.getValue(fromDateField)
                else:
                    newRoute.FROMDATE = defaultFromDate
                if toDateField is not None and toDateField != '' and toDateField != '#':
                    newRoute.TODATE = feature.getValue(toDateField)
                routeTableCursor.insertRow(newRoute)
                newCS = csCursor.newRow()
                newCS.ROUTEID = feature.getValue(routeFieldName)
                newCS.FROMDATE = defaultFromDate
                newCS.ROADWAYID = x
                newCS.ROADWAYIDGUID = guid
                newCS.NETWORKID = 1
                csCursor.insertRow(newCS)
                newCenterline = cCursor.newRow()
                newCenterline.Shape = feature.getValue(inputDsc.shapeFieldName)
                newCenterline.RoadwayID = x
                newCenterline.ROADWAYIDGUID = guid
                newCenterline.FROMDATE = defaultFromDate
                cCursor.insertRow(newCenterline)
                x += 1

        finally:
            del routeTableCursor
            del cCursor
            del csCursor
            del inFeatures
            del feature

        #Load calibration points
        arcpy.AddMessage('Loading calibration points')
        calibrationFields = addMissingFieldsToTarget(inputCalibrationFC, calibrationPoint, [inputCalibrationMField])
        inCalCursor = arcpy.SearchCursor(inputCalibrationFC)
        outCalCursor = arcpy.InsertCursor(calibrationPoint)

        try:
            for calPnt in inCalCursor:
                newCal = outCalCursor.newRow()
                for field in calibrationFields:
                    ##arcpy.AddMessage('Calculating calibration point field: ' + field)
                    newCal.setValue(field, calPnt.getValue(field))
                newCal.MEASURE = calPnt.getValue(inputCalibrationMField)
                newCal.NETWORKID = 1
                newCal.Shape = calPnt.Shape
                outCalCursor.insertRow(newCal)
        finally:
            del inCalCursor
            del outCalCursor

        #Build indexes
        idx.RecreateIndexes(centerlineSequence, calibrationPoint, routeTable, [routeFieldName])

        #Set file geodatabase as output
        arcpy.SetParameterAsText(9, outGDBFullPath)
    except GenerateRAndHSchema.DataExistsError:
        pass
    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
    except:
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]

        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

        # Return python error messages for use in script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

if __name__ == '__main__':
    main()




