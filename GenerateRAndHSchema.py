#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tom
#
# Created:     29/03/2012
# Copyright:   (c) tom 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

class DataExistsError(Exception):
    def __init__(self, value):
         self.value = value
    def __str__(self):
         return repr(self.value)

class InvalidArgumentsError(Exception):
    def __init__(self, value):
         self.value = value
    def __str__(self):
         return repr(self.value)


import arcpy, os, sys, traceback, array, math

def makeALRS(outputGDB, sr, lrsNetworks, lrsActivities, RouteIDLength = 12):
    try:
        try:
            RouteIDLength = int(RouteIDLength)
        except:
            arcpy.AddError('Test Route ID Length must be a positive integer.')
            raise InvalidArgumentsError('Route ID Length must be a positive integer.')

        centerlineName = "Centerline"
        centerlinePath = os.path.join(outputGDB,centerlineName)
        calibrationPointName = "CalibrationPoint"
        calibrationPointPath = os.path.join(outputGDB,calibrationPointName)
        redlineName = "Redline"
        redlinePath = os.path.join(outputGDB,redlineName)
        routeTableName = "Route"
        routeTablePath = os.path.join(outputGDB,routeTableName)
        centerlineSequenceName = "CenterlineSequence"
        centerlineSequencePath = os.path.join(outputGDB,centerlineSequenceName)
        networksDomainName = 'dLRSNetworks'
        activityDomainName = 'dActivityType'
        datasetDict = dict()
        datasetDict['Domain'] = [networksDomainName, activityDomainName]
        datasetDict['Feature Class'] = [centerlineName, calibrationPointName, redlineName]
        datasetDict['Table'] = [routeTableName, centerlineSequenceName]

        #Validate the input geodatabase
        dscWrk = arcpy.Describe(outputGDB)
        existingData = []
        ##arcpy.env.workspace = outputGDB
        for key in datasetDict.keys():
            for name in datasetDict[key]:
                if key == 'Domain':
                    if name in dscWrk.domains:
                        existingData += [[key, name]]
                elif arcpy.Exists(os.path.join(outputGDB, name)):
                        existingData += [[key, name]]
        if len(existingData) > 0:
            errorMessage = ''
            cnt = 1
            for item in existingData:
                if cnt == 1:
                    errorMessage += '%s:%s' % (item[0], item[1])
                else:
                    errorMessage += ', %s:%s' % (item[0], item[1])
                cnt += 1
            raise DataExistsError(existingData)

        #Create the domains
        arcpy.CreateDomain_management(outputGDB, networksDomainName,'LRS Networks in an ALRS','SHORT','CODED')
        counter = 0
        for network in lrsNetworks:
            counter+=1
            arcpy.AddCodedValueToDomain_management(outputGDB, networksDomainName, counter, network)
        arcpy.CreateDomain_management(outputGDB, activityDomainName,'Activites to be performed on routes in an ALRS','SHORT','CODED')
        counter = 0
        for activity in lrsActivities:
            counter+=1
            arcpy.AddCodedValueToDomain_management(outputGDB, activityDomainName, counter, activity)

        #Add the Centerline feature class
        arcpy.CreateFeatureclass_management(outputGDB,centerlineName,"POLYLINE",'#',"ENABLED","ENABLED",sr)
        arcpy.AddField_management(centerlinePath, 'FROMDATE','Date',0,0,8)
        arcpy.AddField_management(centerlinePath, 'TODATE','Date',0,0,8)
        arcpy.AddField_management(centerlinePath, 'ROADWAYID','String',0,0,RouteIDLength)
        arcpy.AddMessage('Created centerline schema')

        #Add the Redline feature class
        arcpy.CreateFeatureclass_management(outputGDB,redlineName,"POLYLINE",'#',"DISABLED","DISABLED",sr)
        arcpy.AddField_management(redlinePath,'ROUTEID','String',0,0,RouteIDLength)
        arcpy.AddField_management(redlinePath,'ROUTENAME','String',0,0,12)
        arcpy.AddField_management(redlinePath,'FROMMEASURE','Double',0,0,8)
        arcpy.AddField_management(redlinePath,'TOMEASURE','Double',0,0,8)
        arcpy.AddField_management(redlinePath,'EFFECTIVEDATE','Date',0,0,8)
        arcpy.AddField_management(redlinePath,'ACTIVITYTYPE','SmallInteger',0,0,2)
        arcpy.AssignDomainToField_management(redlinePath, 'ACTIVITYTYPE', activityDomainName)
        arcpy.AddMessage('Created redline schema')

        #Add the Calibration Point feature class
        arcpy.CreateFeatureclass_management(outputGDB, calibrationPointName,"POINT",'#',"ENABLED","ENABLED",sr)
        arcpy.AddField_management(calibrationPointPath,'ROUTEID','String',0,0,RouteIDLength)
        arcpy.AddField_management(calibrationPointPath,'NETWORKID','SmallInteger',0,0,2)
        arcpy.AssignDomainToField_management(calibrationPointPath,'NETWORKID',networksDomainName)
        arcpy.AddField_management(calibrationPointPath,'MEASURE','Double',0,3,12)
        arcpy.AddField_management(calibrationPointPath,'FROMDATE','Date',0,0,8)
        arcpy.AddField_management(calibrationPointPath,'TODATE','Date',0,0,8)
        arcpy.AddMessage('Created calibration point schema')

        #Add the Route table
        arcpy.CreateTable_management(outputGDB, routeTableName)
        arcpy.AddField_management(routeTablePath,'FROMDATE','Date',0,0,8)
        arcpy.AddField_management(routeTablePath,'TODATE','Date',0,0,8)
        arcpy.AddField_management(routeTablePath,'ROUTEID','String',0,0,RouteIDLength)
        arcpy.AddField_management(routeTablePath,'ROUTENAME','String',0,0,12)
        arcpy.AddMessage('Created route table schema')

        #Add the Centerline Sequence table
        arcpy.CreateTable_management(outputGDB, centerlineSequenceName)
        arcpy.AddField_management(centerlineSequencePath,'ROUTEID','String',0,0,RouteIDLength)
        arcpy.AddField_management(centerlineSequencePath,'ROADWAYID','String',0,0,RouteIDLength)
        arcpy.AddField_management(centerlineSequencePath,'NETWORKID','SmallInteger',0,0,2)
        arcpy.AssignDomainToField_management(centerlineSequencePath,'NETWORKID',networksDomainName)
        arcpy.AddField_management(centerlineSequencePath,'FROMDATE','Date',0,0,8)
        arcpy.AddField_management(centerlineSequencePath,'TODATE','Date',0,0,8)
        arcpy.AddMessage('Created centerline sequence table schema')

        #Set the output Centerline feature class
        arcpy.SetParameterAsText(5, centerlinePath)
        #Set the output Calibration Point feature class
        arcpy.SetParameterAsText(6, calibrationPointPath)
        #Set the output Route table
        arcpy.SetParameterAsText(7, routeTablePath)
        #Set the output Centerline sequence table
        arcpy.SetParameterAsText(8, centerlineSequencePath)
        #Set the output Redline feature class
        arcpy.SetParameterAsText(9, redlinePath)
    except arcpy.ExecuteError as e:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        raise e
    except DataExistsError as e:
        errorIntro = "The following datasets already exist in this geodatabase. Either drop this data or choose a new geodatabase. Existing datasets: "
        arcpy.AddError(errorIntro)
        print errorIntro
        for dataType, dataName in e.value:
            dataErrorString = '   %s: %s' % (dataType, dataName)
            print dataErrorString
            arcpy.AddError(dataErrorString)
        raise DataExistsError('Existing data error')
    except InvalidArgumentsError as err:
        #print err.value
        raise InvalidArgumentsError(err.value)
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
        raise e

if __name__ == '__main__':
    #Testing variables
##    outputGDB = r'E:\Projects\ArcPY\RoadsAndHighways\HamCo.gdb'
##    sr = arcpy.SpatialReference()
##    sr.factoryCode = 26918
##    sr.create()
##    lrsNetworks = ['Mile Marker', 'Reference Marker', 'Named Route']
##    lrsActivities = ['Calibrate Route', 'Create Route', 'Extend Route', 'Realign Gap Route', 'Realign Overlapping Route', 'Realign Route', 'Reassign Route', 'Retire Route', 'Reverse Route', 'Shorten Route']

    #Parameter inputs
    outputGDB = arcpy.GetParameterAsText(0)
    sr = arcpy.GetParameterAsText(1)
    lrsNetworks = arcpy.GetParameterAsText(2).split(";")
    lrsActivities = arcpy.GetParameterAsText(3).split(";")
    routeIDLength = arcpy.GetParameterAsText(4)
    if(routeIDLength is None or routeIDLength == '' or routeIDLength == '#'):
        arcpy.AddMessage('Creating ALRS schema with default route ID length of 12.')
        makeALRS(outputGDB, sr, lrsNetworks, lrsActivities)
    else:
        makeALRS(outputGDB, sr, lrsNetworks, lrsActivities, routeIDLength)


